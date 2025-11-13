// src/screens/RegisterScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { register } from '../services/auth/authService';
import { useNavigation } from '@react-navigation/native';
import theme from '../styles/theme';
import AuthHeader from '../components/AuthHeader';
import FormContainer from '../components/FormContainer';
import StyledInput from '../components/StyledInput';
import PrimaryButton from '../components/PrimaryButton';
import SecondaryButton from '../components/SecondaryButton';
import Divider from '../components/Divider';

const RegisterScreen = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const navigation = useNavigation<any>();

  const handleRegister = async () => {
    try {
      const params = {
        username,
        email,
        password,
        password_confirm: passwordConfirm,
        first_name: firstName,
        last_name: lastName,
      };
      const response = await register(params);  // Pasar el objeto completo
      console.log('Respuesta:', response);
    } catch (error) {
      console.error('Error de registro:', error);
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
        showsVerticalScrollIndicator={false}
      >
        <AuthHeader 
          title="Crear Cuenta"
          subtitle="Únete a Atenas hoy"
          logoSize={56}
        />

        <FormContainer style={styles.formContainer}>
          <StyledInput
            label="Nombre"
            value={firstName}
            onChangeText={setFirstName}
            placeholder="Nombre"
            autoCapitalize="words"
          />

          <StyledInput
            label="Apellido"
            value={lastName}
            onChangeText={setLastName}
            placeholder="Apellido"
            autoCapitalize="words"
          />

          <StyledInput
            label="Usuario"
            value={username}
            onChangeText={setUsername}
            placeholder="Nombre de usuario"
            autoCapitalize="none"
          />

          <StyledInput
            label="Email"
            value={email}
            onChangeText={setEmail}
            placeholder="Correo electrónico"
            keyboardType="email-address"
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

          <StyledInput
            label="Confirmar Contraseña"
            value={passwordConfirm}
            onChangeText={setPasswordConfirm}
            placeholder="Confirmar contraseña"
            secureTextEntry
            autoCapitalize="none"
          />

          <PrimaryButton 
            title="Crear Cuenta" 
            onPress={handleRegister}
          />

          <Divider />

          <SecondaryButton 
            title="¿Ya tienes cuenta? Inicia sesión"
            onPress={() => navigation.reset({ index: 0, routes: [{ name: 'Login' }] }) }
          />
        </FormContainer>

        <Text style={styles.terms}>
          Al crear una cuenta, aceptas nuestros{' '}
          <Text style={styles.termsLink}>Términos de Servicio</Text> y{' '}
          <Text style={styles.termsLink}>Política de Privacidad</Text>
        </Text>
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
    paddingHorizontal: theme.spacing.xl,
    paddingTop: theme.spacing.xxl,
    paddingBottom: theme.spacing.xl,
  },
  formContainer: {
    marginBottom: theme.spacing.md,
  },
  terms: {
    fontSize: theme.fontSize.xs,
    color: theme.colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: theme.spacing.md,
  },
  termsLink: {
    color: theme.colors.primary,
    fontWeight: theme.fontWeight.semibold,
  },
});

export default RegisterScreen;
