import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity, Alert, ActivityIndicator, TextInput, ScrollView } from 'react-native';
import NavigationBar from '../components/NavigationBar';
import theme from '../styles/theme';
import { uploadAudio } from '../services/api/transcriptionsService';
import * as DocumentPicker from '@react-native-documents/picker';

const HomeScreen = () => {
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [customPrompt, setCustomPrompt] = useState('');
  
  const handleSelectFile = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
        copyTo: 'cachesDirectory',
      });
      const file = result[0];
      console.log('Archivo seleccionado:', file);
      setSelectedFile(file);
      setCustomPrompt('');
    } catch (error: any) {
      if (error.code === 'DOCUMENT_PICKER_CANCELED') {
        console.log('Usuario canceló la selección');
      } else {
        console.error('Error al seleccionar archivo:', error);
        Alert.alert('Error', 'Hubo un problema al seleccionar el archivo');
      }
    }
  };

  const handleUploadAudio = async () => {
    if (!selectedFile) {
      Alert.alert('Error', 'Por favor selecciona un archivo primero');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('audio_file', {
        uri: selectedFile.fileCopyUri || selectedFile.uri,
        type: selectedFile.type || 'audio/mpeg',
        name: selectedFile.name,
      } as any);

      if (customPrompt.trim()) {
        formData.append('custom_prompt', customPrompt.trim());
      }

      setUploading(true);
      const response = await uploadAudio(formData);
      console.log('Respuesta del servidor:', response);
      
      Alert.alert(
        '¡Éxito!',
        'Tu audio se ha procesado correctamente',
        [{ 
          text: 'OK',
          onPress: () => {
            setSelectedFile(null);
            setCustomPrompt('');
          }
        }]
      );
    } catch (error: any) {
      console.error('Error al subir audio:', error);
      Alert.alert('Error', 'Hubo un problema al subir el audio');
    } finally {
      setUploading(false);
    }
  };

  const handleCancelSelection = () => {
    setSelectedFile(null);
    setCustomPrompt('');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.content}>
          <Text style={styles.logo}>🏛️</Text>
          <Text style={styles.title}>Atenas</Text>
          <Text style={styles.subtitle}>Bienvenido a tu espacio de aprendizaje</Text>
          
          {/* Mostrar botón de selección o formulario completo */}
          {!selectedFile ? (
            <TouchableOpacity 
              style={styles.uploadButton}
              onPress={handleSelectFile}
              activeOpacity={0.8}
            >
              <View style={styles.uploadIconContainer}>
                <Text style={styles.uploadIcon}>🎤</Text>
              </View>
              <Text style={styles.uploadButtonText}>Seleccionar Audio</Text>
              <Text style={styles.uploadButtonSubtext}>
                Toca para seleccionar un archivo
              </Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.fileSelectedContainer}>
              {/* Información del archivo seleccionado */}
              <View style={styles.fileInfoCard}>
                <Text style={styles.fileInfoTitle}>Archivo seleccionado:</Text>
                <Text style={styles.fileName} numberOfLines={2}>
                  {selectedFile.name}
                </Text>
                <TouchableOpacity 
                  style={styles.changeFileButton}
                  onPress={handleSelectFile}
                >
                  <Text style={styles.changeFileText}>Cambiar archivo</Text>
                </TouchableOpacity>
              </View>

              {/* Text Input para el prompt personalizado */}
              <View style={styles.promptContainer}>
                <Text style={styles.promptLabel}>
                  Prompt personalizado (opcional)
                </Text>
                <Text style={styles.promptDescription}>
                  Describe cómo quieres que se genere el resumen
                </Text>
                <TextInput
                  style={styles.promptInput}
                  multiline={true}
                  numberOfLines={6}
                  maxLength={1000}
                  placeholder="Ejemplo: Resume destacando los puntos clave y conceptos importantes del audio..."
                  placeholderTextColor={theme.colors.textSecondary}
                  value={customPrompt}
                  onChangeText={setCustomPrompt}
                  textAlignVertical="top"
                />
                <Text style={styles.charCounter}>
                  {customPrompt.length}/1000 caracteres
                </Text>
              </View>

              {/* Botones de acción */}
              <View style={styles.actionButtonsContainer}>
                <TouchableOpacity 
                  style={[styles.uploadButton, uploading && styles.uploadButtonDisabled]}
                  onPress={handleUploadAudio}
                  activeOpacity={0.8}
                  disabled={uploading}
                >
                  {uploading ? (
                    <>
                      <ActivityIndicator size="large" color="#FFFFFF" />
                      <Text style={styles.uploadButtonText}>Procesando...</Text>
                      <Text style={styles.uploadButtonSubtext}>
                        Esto puede tardar varios minutos
                      </Text>
                    </>
                  ) : (
                    <>
                      <Text style={styles.uploadButtonText}>Subir y Procesar</Text>
                      <Text style={styles.uploadButtonSubtext}>
                        Generar transcripción y resumen
                      </Text>
                    </>
                  )}
                </TouchableOpacity>

                {!uploading && (
                  <TouchableOpacity 
                    style={styles.cancelButton}
                    onPress={handleCancelSelection}
                    activeOpacity={0.8}
                  >
                    <Text style={styles.cancelButtonText}>Cancelar</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          )}
        </View>
      </ScrollView>
      <NavigationBar />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.xl,
    paddingVertical: theme.spacing.xl,
  },
  logo: {
    fontSize: 80,
    marginBottom: theme.spacing.lg,
  },
  title: {
    fontSize: theme.fontSize.xxl,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: theme.fontSize.md,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: theme.spacing.xxl,
  },
  uploadButton: {
    backgroundColor: theme.colors.primary,
    borderRadius: theme.borderRadius.xl,
    padding: theme.spacing.xl,
    alignItems: 'center',
    width: '100%',
    maxWidth: 300,
    shadowColor: theme.colors.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  uploadButtonDisabled: {
    opacity: 0.6,
  },
  uploadIconContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: theme.borderRadius.full,
    width: 80,
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  uploadIcon: {
    fontSize: 40,
  },
  uploadButtonText: {
    color: theme.colors.textOnPrimary,
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.bold,
    marginBottom: theme.spacing.xs,
  },
  uploadButtonSubtext: {
    color: theme.colors.textOnPrimary,
    fontSize: theme.fontSize.sm,
    opacity: 0.8,
  },
  fileSelectedContainer: {
    width: '100%',
    maxWidth: 400,
  },
  fileInfoCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.lg,
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
    borderWidth: 2,
    borderColor: '#4CAF50',
  },
  fileInfoIcon: {
    fontSize: 40,
    marginBottom: theme.spacing.sm,
  },
  fileInfoTitle: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
  },
  fileName: {
    fontSize: theme.fontSize.md,
    color: theme.colors.textPrimary,
    fontWeight: theme.fontWeight.semibold,
    textAlign: 'center',
    marginBottom: theme.spacing.md,
  },
  changeFileButton: {
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.md,
  },
  changeFileText: {
    color: theme.colors.primary,
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.semibold,
  },
  promptContainer: {
    width: '100%',
    marginBottom: theme.spacing.lg,
  },
  promptLabel: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
  },
  promptDescription: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.md,
  },
  promptInput: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.md,
    fontSize: theme.fontSize.md,
    color: theme.colors.textPrimary,
    minHeight: 150,
    maxHeight: 250,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  charCounter: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    textAlign: 'right',
    marginTop: theme.spacing.xs,
  },
  actionButtonsContainer: {
    width: '100%',
    alignItems: 'center',
  },
  cancelButton: {
    marginTop: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
  },
  cancelButtonText: {
    color: theme.colors.textSecondary,
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
  },
});

export default HomeScreen;
