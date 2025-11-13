// src/screens/LoginScreen.tsx
import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { login } from '../services/auth/authService';
import { useNavigation } from '@react-navigation/native';
import theme from '../styles/theme';
import AuthHeader from '../components/AuthHeader';
import FormContainer from '../components/FormContainer';
import StyledInput from '../components/StyledInput';
import PrimaryButton from '../components/PrimaryButton';
import SecondaryButton from '../components/SecondaryButton';
import Divider from '../components/Divider';

const LoginScreen = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const navigation = useNavigation<any>();

  const handleLogin = async () => {
    try {
      const params = {
        username,
        password,
      };

      const response = await login(params);
      navigation.reset({
        index: 0,
        routes: [{ name: 'Home' }],
      });
      console.log('Respuesta:', response);
    } catch (error) {
      console.error('Error de inicio de sesión:', error);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <AuthHeader 
          title="Bienvenido a Atenas"
          subtitle="Inicia sesión para continuar"
        />

        <FormContainer>
          <StyledInput
            label="Usuario"
            value={username}
            onChangeText={setUsername}
            placeholder="Nombre de usuario"
            autoCapitalize="none"
          />

          <StyledInput
            label="Contraseña"
            value={password}
            onChangeText={setPassword}
            placeholder="Contraseña"
            secureTextEntry
            autoCapitalize="none"
          />

          <PrimaryButton 
            title="Iniciar sesión" 
            onPress={handleLogin}
          />

          <Divider />

          <SecondaryButton 
            title="Crear una cuenta"
            onPress={() => navigation.navigate('Register')}
          />
        </FormContainer>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: theme.spacing.xl,
    paddingVertical: theme.spacing.xxl,
  },
});

export default LoginScreen;
