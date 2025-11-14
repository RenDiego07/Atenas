// src/services/authService.ts

import { Alert } from 'react-native';
import axiosInstance from '../axiosConfig';
import AsyncStorage from '@react-native-async-storage/async-storage';

// URL de tu backend para autenticación
const AUTH_URL = '/auth';

// Función para registrar un usuario
export const register = async (params: RegisterAuthParams) => {
  try {
    console.log('Registrando con parámetros:', params);
    const response = await axiosInstance.post(`${AUTH_URL}/register/`, {
      username: params.username,
      email: params.email,
      password: params.password,
      password_confirm: params.password_confirm,
      first_name: params.first_name,
      last_name: params.last_name,
    });
    return response.data;
  } catch (error) {
    console.error('Error al registrar:', error);
    throw error;
  }
};

// Función para iniciar sesión
export const login = async (params: LoginAuthParams) => {
  try {
    const response = await axiosInstance.post(`${AUTH_URL}/login/`, {
      username: params.username,
      password: params.password,
    });

    // Guardar el token en AsyncStorage
    await AsyncStorage.setItem('token', response.data.access);
    
    return response.data;  // Devuelve la respuesta con el token
  } catch (error) {
    console.error('Error al iniciar sesión:', error);
    Alert.alert('Error', 'Credenciales inválidas');
    throw error;
  }
};

// Función para cerrar sesión
export const logout = async () => {
  try {
    await AsyncStorage.removeItem('token');
  } catch (error) {
    console.error('Error al cerrar sesión:', error);
  }
};

// Función para obtener el token almacenado
export const getToken = async () => {
  return await AsyncStorage.getItem('token');
};

interface RegisterAuthParams {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

interface LoginAuthParams {
  username: string;
  password: string;
}