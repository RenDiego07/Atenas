import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import theme from '../styles/theme';

interface AuthHeaderProps {
  title: string;
  subtitle: string;
  logoSize?: number;
}

const AuthHeader: React.FC<AuthHeaderProps> = ({ title, subtitle, logoSize = 64 }) => {
  return (
    <View style={styles.header}>
      <Text style={[styles.logo, { fontSize: logoSize }]}>🏛️</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  header: {
    alignItems: 'center',
    marginBottom: theme.spacing.xxl,
  },
  logo: {
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
});

export default AuthHeader;
