import React, { useState } from 'react';
import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import NavigationBar from '../components/NavigationBar';
import theme from '../styles/theme';
import { uploadAudio } from '../services/api/transcriptionsService';
import * as DocumentPicker from '@react-native-documents/picker';

const HomeScreen = () => {
  const [uploading, setUploading] = useState(false);

  const handleUploadAudio = async () => {
    try {
      // Seleccionar archivo de audio
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
        copyTo: 'cachesDirectory',
      });

      const file = result[0];
      console.log('Archivo seleccionado:', file);

      // Crear FormData
      const formData = new FormData();
      formData.append('audio_file', {
        uri: file.uri,
        type: file.type || 'audio/mpeg',
        name: file.name,
      } as any);

      setUploading(true);

      // Subir el archivo
      //const response = await uploadAudio(formData);
      //console.log('Respuesta del servidor:', response);

      Alert.alert(
        '¡Éxito!',
        'Tu audio se ha subido correctamente y está siendo procesado.',
        [{ text: 'OK' }]
      );
    } catch (error: any) {
      if (error.code === 'DOCUMENT_PICKER_CANCELED') {
        console.log('Usuario canceló la selección');
      } else {
        console.error('Error al subir audio:', error);
        Alert.alert(
          'Error',
          'Hubo un problema al subir el audio. Por favor, intenta de nuevo.',
          [{ text: 'OK' }]
        );
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.logo}>🏛️</Text>
        <Text style={styles.title}>Atenas</Text>
        <Text style={styles.subtitle}>Bienvenido a tu espacio de aprendizaje</Text>
        
        <TouchableOpacity 
          style={[styles.uploadButton, uploading && styles.uploadButtonDisabled]}
          onPress={handleUploadAudio}
          activeOpacity={0.8}
          disabled={uploading}
        >
          <View style={styles.uploadIconContainer}>
            {uploading ? (
              <ActivityIndicator size="large" color="#FFFFFF" />
            ) : (
              <Text style={styles.uploadIcon}>🎤</Text>
            )}
          </View>
          <Text style={styles.uploadButtonText}>
            {uploading ? 'Subiendo...' : 'Subir Audio'}
          </Text>
          <Text style={styles.uploadButtonSubtext}>
            {uploading ? 'Por favor espera' : 'Toca para seleccionar un archivo'}
          </Text>
        </TouchableOpacity>
      </View>
      <NavigationBar />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.xl,
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
});

export default HomeScreen;
