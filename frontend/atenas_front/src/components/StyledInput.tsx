import React from 'react';
import { View, TextInput, Text, StyleSheet, TextInputProps } from 'react-native';
import theme from '../styles/theme';

interface StyledInputProps extends TextInputProps {
  label?: string;
}

const StyledInput: React.FC<StyledInputProps> = ({ label, style, ...props }) => {
  return (
    <View style={styles.inputContainer}>
      {label && <Text style={styles.inputLabel}>{label}</Text>}
      <TextInput
        style={[styles.input, style]}
        placeholderTextColor={theme.colors.textTertiary}
        {...props}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  inputContainer: {
    marginBottom: theme.spacing.md,
  },
  inputLabel: {
    fontSize: theme.fontSize.sm,
    fontWeight: theme.fontWeight.semibold,
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
  },
  input: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    borderWidth: 1.5,
    borderColor: theme.colors.border,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.md,
    fontSize: theme.fontSize.md,
    color: theme.colors.textPrimary,
  },
});

export default StyledInput;
