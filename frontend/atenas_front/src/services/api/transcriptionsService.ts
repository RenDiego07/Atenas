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
    });
    return response.data;
  } catch (error) {
    console.error('Error al subir audio:', error);
    throw error;
  }
};
