import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import theme from '../styles/theme';

const NavigationBar = () => {
  const navigation = useNavigation<any>();

  const handleLogout = async () => {
    Alert.alert(
      'Cerrar Sesión',
      '¿Estás seguro que deseas cerrar sesión?',
      [
        {
          text: 'Cancelar',
          style: 'cancel',
        },
        {
          text: 'Cerrar Sesión',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.removeItem('token');
              navigation.reset({
                index: 0,
                routes: [{ name: 'Login' }],
              });
            } catch (error) {
              console.error('Error al cerrar sesión:', error);
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity 
        style={styles.sideButton} 
        onPress={() => navigation.navigate('Summaries')}
      >
        <Text style={styles.icon}>📚</Text>
        <Text style={styles.sideButtonText}>Resúmenes</Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.centerButton} 
        onPress={() => navigation.navigate('Home')}
      >
        <Text style={styles.centerIcon}>🏛️</Text>
        <Text style={styles.centerButtonText}>Inicio</Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.sideButton} 
        onPress={handleLogout}
      >
        <Text style={styles.icon}>🚪</Text>
        <Text style={styles.sideButtonText}>Salir</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: theme.colors.surface,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  sideButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    flex: 1,
  },
  centerButton: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.primary,
    borderRadius: theme.borderRadius.full,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.lg,
    marginHorizontal: theme.spacing.sm,
    flex: 1.5,
    shadowColor: theme.colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  icon: {
    fontSize: 24,
    marginBottom: theme.spacing.xs,
  },
  centerIcon: {
    fontSize: 32,
    marginBottom: theme.spacing.xs,
  },
  sideButtonText: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    fontWeight: theme.fontWeight.medium,
  },
  centerButtonText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textOnPrimary,
    fontWeight: theme.fontWeight.semibold,
  },
});

export default NavigationBar;
