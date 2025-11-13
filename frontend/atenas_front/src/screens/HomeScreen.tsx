import React from 'react';
import { View, Text, StyleSheet, SafeAreaView } from 'react-native';
import NavigationBar from '../components/NavigationBar';
import theme from '../styles/theme';

const HomeScreen = () => {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.logo}>🏛️</Text>
        <Text style={styles.title}>Atenas</Text>
        <Text style={styles.subtitle}>Bienvenido a tu espacio de aprendizaje</Text>
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
  },
});

export default HomeScreen;
