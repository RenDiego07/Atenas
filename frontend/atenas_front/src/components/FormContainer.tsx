import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import theme from '../styles/theme';

interface FormContainerProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

const FormContainer: React.FC<FormContainerProps> = ({ children, style }) => {
  return <View style={[styles.container, style]}>{children}</View>;
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.xl,
    padding: theme.spacing.xl,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
});

export default FormContainer;
