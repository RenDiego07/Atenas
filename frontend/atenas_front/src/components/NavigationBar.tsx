import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet, Alert } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import theme from '../styles/theme';

const NavigationBar = () => {
  const navigation = useNavigation<any>();
  const route = useRoute();
  
  const currentRoute = route.name;

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

  const isActive = (routeName: string) => currentRoute === routeName;

  return (
    <View style={styles.container}>
      <TouchableOpacity 
        style={[
          styles.sideButton,
          isActive('Summaries') && styles.activeButton
        ]} 
        onPress={() => navigation.navigate('Summaries')}
      >
        <Text style={styles.icon}>📚</Text>
        <Text style={[
          styles.sideButtonText,
          isActive('Summaries') && styles.activeButtonText
        ]}>
          Resúmenes
        </Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={[
          styles.centerButton,
          !isActive('Home') && styles.inactiveCenterButton
        ]} 
        onPress={() => navigation.navigate('Home')}
      >
        <Text style={styles.centerIcon}>🏛️</Text>
        <Text style={[
          styles.centerButtonText,
          !isActive('Home') && styles.inactiveCenterButtonText
        ]}>
          Inicio
        </Text>
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
    borderRadius: theme.borderRadius.md,
  },
  activeButton: {
    backgroundColor: `${theme.colors.primary}15`,
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
  inactiveCenterButton: {
    backgroundColor: theme.colors.surface,
    borderWidth: 2,
    borderColor: theme.colors.border,
    shadowOpacity: 0,
    elevation: 0,
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
  activeButtonText: {
    color: theme.colors.primary,
    fontWeight: theme.fontWeight.semibold,
  },
  centerButtonText: {
    fontSize: theme.fontSize.sm,
    color: theme.colors.textOnPrimary,
    fontWeight: theme.fontWeight.semibold,
  },
  inactiveCenterButtonText: {
    color: theme.colors.textSecondary,
  },
});

export default NavigationBar;
