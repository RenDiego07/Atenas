import axiosInstance from "../axiosConfig";

const TRANSCRIPTIONS_URL = '/transcriptions';

// Ejemplo: Obtener todas las transcripciones
export const getTranscriptions = async () => {
  try {
    const response = await axiosInstance.get(`${TRANSCRIPTIONS_URL}/`);
    return response.data;
  } catch (error) {
    console.error('Error al obtener transcripciones:', error);
    throw error;
  }
};

// Ejemplo: Crear una nueva transcripción (subir audio)
export const uploadAudio = async (audioFile: FormData) => {
  try {
    const response = await axiosInstance.post(`${TRANSCRIPTIONS_URL}/upload/`, audioFile, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 660000, // 11 minutos (660,000 ms) - Más que el backend (10 min)
    });
    return response.data;
  } catch (error: any) {
    // Manejo de errores mejorado
    if (error.code === 'ECONNABORTED') {
      console.error('Timeout: La solicitud tardó demasiado');
      throw new Error('El procesamiento está tardando más de lo esperado. Por favor, verifica el estado en el historial.');
    } else if (error.response) {
      // El servidor respondió con un error
      console.error('Error del servidor:', error.response.data);
      throw new Error(error.response.data?.error || 'Error al procesar el audio');
    } else if (error.request) {
      // No hubo respuesta del servidor
      console.error('Sin respuesta del servidor:', error.request);
      throw new Error('No se pudo conectar con el servidor. Verifica tu conexión.');
    } else {
      console.error('Error al subir audio:', error);
      throw error;
    }
  }
};