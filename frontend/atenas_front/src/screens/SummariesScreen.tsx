import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, SafeAreaView, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator, Modal } from 'react-native';
import NavigationBar from '../components/NavigationBar';
import theme from '../styles/theme';
import { getTranscriptions } from '../services/api/transcriptionsService';

interface Transcription {
  id: number;
  audio_name: string;
  summary_content: string | null;
  summary_prompt: string | null;
  status: string;
  created_at: string;
}

const SummariesScreen = () => {
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<Transcription | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const fetchTranscriptions = async () => {
    try {
      const data = await getTranscriptions();
      // Filtrar solo las que tienen resumen
      const withSummaries = data.filter((t: Transcription) => t.summary_content);
      setTranscriptions(withSummaries);
    } catch (error) {
      console.error('Error al cargar resúmenes:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTranscriptions();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchTranscriptions();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const month = months[date.getMonth()];
    const day = date.getDate();
    return `${month} ${day}`;
  };

  const truncateText = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const openSummary = (transcription: Transcription) => {
    setSelectedSummary(transcription);
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setSelectedSummary(null);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={styles.loadingText}>Cargando resúmenes...</Text>
        </View>
        <NavigationBar />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.icon}>📚</Text>
          <Text style={styles.title}>Mis Resúmenes</Text>
          <Text style={styles.subtitle}>
            {transcriptions.length > 0 
              ? `${transcriptions.length} resumen${transcriptions.length > 1 ? 'es' : ''} guardado${transcriptions.length > 1 ? 's' : ''}`
              : 'Aquí encontrarás todos tus resúmenes guardados'
            }
          </Text>
        </View>

        {transcriptions.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📝</Text>
            <Text style={styles.emptyText}>Aún no tienes resúmenes</Text>
            <Text style={styles.emptySubtext}>Comienza subiendo tu primer audio</Text>
          </View>
        ) : (
          <View style={styles.summariesContainer}>
            {transcriptions.map((transcription) => (
              <TouchableOpacity
                key={transcription.id}
                style={styles.summaryCard}
                onPress={() => openSummary(transcription)}
                activeOpacity={0.7}
              >
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle} numberOfLines={1}>
                    {transcription.audio_name}
                  </Text>
                  <Text style={styles.cardDate}>
                    {formatDate(transcription.created_at)}
                  </Text>
                </View>
                <Text style={styles.cardPreview} numberOfLines={3}>
                  {truncateText(transcription.summary_content || '')}
                </Text>
                <View style={styles.cardFooter}>
                  <Text style={styles.readMoreText}>Leer más →</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>

      {/* Modal para mostrar el resumen completo */}
      <Modal
        animationType="slide"
        transparent={false}
        visible={modalVisible}
        onRequestClose={closeModal}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={closeModal} style={styles.closeButton}>
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle} numberOfLines={2}>
              {selectedSummary?.audio_name}
            </Text>
            <Text style={styles.modalDate}>
              {selectedSummary && formatDate(selectedSummary.created_at)}
            </Text>
          </View>

          <ScrollView style={styles.modalContent}>
            {selectedSummary?.summary_prompt && (
              <View style={styles.promptSection}>
                <Text style={styles.promptLabel}>📝 Prompt usado:</Text>
                <Text style={styles.promptText}>{selectedSummary.summary_prompt}</Text>
              </View>
            )}

            <View style={styles.summarySection}>
              <Text style={styles.summaryLabel}>📄 Resumen:</Text>
              <Text style={styles.summaryText}>{selectedSummary?.summary_content}</Text>
            </View>
          </ScrollView>
        </SafeAreaView>
      </Modal>

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
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: theme.spacing.md,
    fontSize: theme.fontSize.md,
    color: theme.colors.textSecondary,
  },
  header: {
    paddingHorizontal: theme.spacing.xl,
    paddingTop: theme.spacing.xxl,
    paddingBottom: theme.spacing.lg,
    alignItems: 'center',
  },
  icon: {
    fontSize: 48,
    marginBottom: theme.spacing.md,
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
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.xl,
    paddingVertical: theme.spacing.xxl * 2,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: theme.spacing.lg,
    opacity: 0.5,
  },
  emptyText: {
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.xs,
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textTertiary,
    textAlign: 'center',
  },
  summariesContainer: {
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  summaryCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  cardTitle: {
    fontSize: theme.fontSize.lg,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.textPrimary,
    flex: 1,
    marginRight: theme.spacing.sm,
  },
  cardDate: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    fontWeight: theme.fontWeight.semibold,
  },
  cardPreview: {
    fontSize: theme.fontSize.md,
    color: theme.colors.textSecondary,
    lineHeight: 22,
    marginBottom: theme.spacing.sm,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginTop: theme.spacing.xs,
  },
  readMoreText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.primary,
    fontWeight: theme.fontWeight.semibold,
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  modalHeader: {
    paddingHorizontal: theme.spacing.xl,
    paddingTop: theme.spacing.lg,
    paddingBottom: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  closeButton: {
    alignSelf: 'flex-end',
    padding: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  closeButtonText: {
    fontSize: 28,
    color: theme.colors.textSecondary,
    fontWeight: theme.fontWeight.bold,
  },
  modalTitle: {
    fontSize: theme.fontSize.xl,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
  },
  modalDate: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    fontWeight: theme.fontWeight.semibold,
  },
  modalContent: {
    flex: 1,
    paddingHorizontal: theme.spacing.xl,
    paddingTop: theme.spacing.lg,
  },
  promptSection: {
    backgroundColor: '#F5F5F5',
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  promptLabel: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.sm,
  },
  promptText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textSecondary,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  summarySection: {
    marginBottom: theme.spacing.xxl,
  },
  summaryLabel: {
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.bold,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.md,
  },
  summaryText: {
    fontSize: theme.fontSize.md,
    color: theme.colors.textPrimary,
    lineHeight: 24,
  },
});

export default SummariesScreen;
