import React from 'react';
import { View, Text, StyleSheet, SafeAreaView, ScrollView } from 'react-native';
import NavigationBar from '../components/NavigationBar';
import theme from '../styles/theme';

const SummariesScreen = () => {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.icon}>📚</Text>
          <Text style={styles.title}>Mis Resúmenes</Text>
          <Text style={styles.subtitle}>Aquí encontrarás todos tus resúmenes guardados</Text>
        </View>

        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>📝</Text>
          <Text style={styles.emptyText}>Aún no tienes resúmenes</Text>
          <Text style={styles.emptySubtext}>Comienza creando tu primer resumen</Text>
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
  content: {
    flex: 1,
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
    paddingVertical: theme.spacing.xxl,
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
});

export default SummariesScreen;
