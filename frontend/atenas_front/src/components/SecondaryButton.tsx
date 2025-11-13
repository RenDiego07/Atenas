import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ViewStyle } from 'react-native';
import theme from '../styles/theme';

interface SecondaryButtonProps {
  title: string;
  onPress: () => void;
  style?: ViewStyle;
}

const SecondaryButton: React.FC<SecondaryButtonProps> = ({ title, onPress, style }) => {
  return (
    <TouchableOpacity style={[styles.button, style]} onPress={onPress}>
      <Text style={styles.buttonText}>{title}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    backgroundColor: 'transparent',
    borderRadius: theme.borderRadius.lg,
    borderWidth: 2,
    borderColor: theme.colors.primary,
    paddingVertical: theme.spacing.md,
    alignItems: 'center',
  },
  buttonText: {
    color: theme.colors.primary,
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.semibold,
  },
});

export default SecondaryButton;
