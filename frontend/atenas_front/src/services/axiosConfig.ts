// src/services/api/axiosConfig.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// URL base de tu API
const API_BASE_URL = 'http://10.0.2.2:8000/api';

// Crear instancia de axios
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de Request: Agregar token automáticamente
axiosInstance.interceptors.request.use(
  async (config) => {
    try {
      // No agregar token para rutas de autenticación
      const isAuthRoute = config.url?.includes('/auth/login') || 
                          config.url?.includes('/auth/register');
      
      if (!isAuthRoute) {
        // Obtener el token desde AsyncStorage
        const token = await AsyncStorage.getItem('token');
        
        // Si existe el token, agregarlo al header
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
    
      return config;
    } catch (error) {
      console.error('Error al obtener el token:', error);
      return config;
    }
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de Response: Manejar errores globalmente
axiosInstance.interceptors.response.use(
  (response) => {
    // Si la respuesta es exitosa, simplemente retornarla
    return response;
  },
  async (error) => {
    // Si el token expiró o es inválido (401)
    if (error.response && error.response.status === 401) {
      console.log('Token inválido o expirado');
      
      // Limpiar el token
      await AsyncStorage.removeItem('token');
      
      // Aquí podrías disparar un evento o usar un navigation service
      // para redirigir al usuario a la pantalla de login
      // Por ejemplo: NavigationService.navigate('Login');
    }
    
    return Promise.reject(error);
  }
);

export default axiosInstance;
