"""
Audio Chunking Service for Transcription Processing

This service handles the division of uploaded audio files into fixed-duration chunks
for subsequent transcription and summarization processing.

Design Decisions & Trade-offs:
===============================

1. Chunking Strategy: ffmpeg "segment" mode
   - Uses `ffmpeg -f segment -segment_time <N> -c copy -reset_timestamps 1`
   - PROS: Fastest approach, avoids re-encoding, preserves original quality/codec
   - CONS: Maintains original codec/container, may not be standardized for ASR
   - JUSTIFICATION: Speed and quality preservation are prioritized for initial chunking.
     ASR standardization can be handled later if needed.

2. Chunk Duration: 180 seconds (configurable)
   - Default policy: Fixed 180s chunks, last chunk may be shorter
   - Balances processing time vs. context preservation for summarization

3. File Organization:
   - Chunks stored at: MEDIA_ROOT/audios/<transcription_id>/chunks/chunk_<index>.<ext>
   - Prevents naming conflicts, enables easy cleanup per transcription

4. Idempotency Policy: Purge and Recreate (option a)
   - If re-chunking requested: removes existing chunks and creates new ones
   - Ensures consistent state, handles duration changes gracefully

5. Error Handling:
   - Transactional operations with proper rollback
   - Clear error messages without exposing internal paths
   - Sets transcription status to "failed" on errors

Dependencies:
=============
- ffmpeg: Must be installed and available in PATH
- mutagen: For accurate duration calculation
- django: For file handling and database operations

Usage:
======
```python
from apps.api.services.chunking import ChunkingService

service = ChunkingService()
chunks = service.chunk_transcription(transcription, seconds_per_chunk=180, force=False)
```
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from django.conf import settings
from django.db import transaction
from mutagen import File as MutagenFile
from apps.api.models import Transcription, TranscriptionChunk

logger = logging.getLogger(__name__)


class ChunkingError(Exception):
    """Custom exception for chunking-related errors."""
    pass


class ChunkingService:
    """Service for handling audio file chunking operations."""
    
    DEFAULT_CHUNK_DURATION = 180  # seconds
    MIN_AUDIO_DURATION = 1  # minimum 1 second to be considered valid
    
    def __init__(self):
        self._verify_dependencies()
    
    def _verify_dependencies(self) -> None:
        """Verify that required dependencies (ffmpeg) are available."""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise ChunkingError(
                "ffmpeg is not installed or not available in PATH. "
                "Please install ffmpeg to enable audio chunking."
            )
    
    def chunk_transcription(self, 
                          transcription: Transcription, 
                          seconds_per_chunk: int = None, 
                          force: bool = False) -> List[TranscriptionChunk]:
        """
        Chunk an audio transcription into fixed-duration segments.
        
        Args:
            transcription: The Transcription object to chunk
            seconds_per_chunk: Duration of each chunk in seconds (default: 180)
            force: If True, purge existing chunks and recreate
        
        Returns:
            List of created TranscriptionChunk objects
            
        Raises:
            ChunkingError: If chunking fails for any reason
        """
        if seconds_per_chunk is None:
            seconds_per_chunk = self.DEFAULT_CHUNK_DURATION
            
        # Check for existing chunks
        existing_chunks = TranscriptionChunk.objects.filter(transcription=transcription)
        if existing_chunks.exists() and not force:
            raise ChunkingError(
                f"Chunks already exist for transcription {transcription.id}. "
                "Use force=true to recreate them."
            )
        
        try:
            with transaction.atomic():
                # Purge existing chunks if they exist
                if existing_chunks.exists():
                    self._cleanup_chunk_files(existing_chunks)
                    existing_chunks.delete()
                
                # Validate audio file
                self._validate_audio_file(transcription)
                
                # Create chunk directory
                chunk_dir = self._get_chunk_directory(transcription)
                chunk_dir.mkdir(parents=True, exist_ok=True)
                
                # Perform chunking
                chunks = self._create_chunks(transcription, seconds_per_chunk, chunk_dir)
                
                # Update transcription status
                transcription.status = "chunked"
                transcription.save(update_fields=["status"])
                
                return chunks
                
        except Exception as e:
            logger.exception(f"Chunking failed for transcription {transcription.id}")
            transcription.status = "failed"
            transcription.save(update_fields=["status"])
            
            if isinstance(e, ChunkingError):
                raise
            else:
                raise ChunkingError(f"Unexpected error during chunking: {str(e)}")
    
    def _validate_audio_file(self, transcription: Transcription) -> None:
        """Validate that the audio file is suitable for chunking."""
        audio_path = transcription.audio_file.path
        
        if not os.path.exists(audio_path):
            raise ChunkingError("Audio file does not exist on disk")
        
        # Get accurate duration using mutagen
        try:
            audio_file = MutagenFile(audio_path)
            if not audio_file or not audio_file.info:
                raise ChunkingError("Could not read audio file metadata")
            
            duration = float(getattr(audio_file.info, "length", 0.0))
            if duration < self.MIN_AUDIO_DURATION:
                raise ChunkingError(
                    f"Audio file too short ({duration:.1f}s). "
                    f"Minimum duration: {self.MIN_AUDIO_DURATION}s"
                )
            
            # Update transcription duration if not set
            if not transcription.total_duration:
                transcription.total_duration = int(duration)
                transcription.save(update_fields=["total_duration"])
                
        except Exception as e:
            if isinstance(e, ChunkingError):
                raise
            raise ChunkingError(f"Error validating audio file: {str(e)}")
    
    def _get_chunk_directory(self, transcription: Transcription) -> Path:
        """Get the directory path for storing chunks."""
        return Path(settings.MEDIA_ROOT) / "audios" / str(transcription.id) / "chunks"
    
    def _create_chunks(self, 
                      transcription: Transcription, 
                      seconds_per_chunk: int, 
                      chunk_dir: Path) -> List[TranscriptionChunk]:
        """Create audio chunks using ffmpeg."""
        audio_path = transcription.audio_file.path
        total_duration = transcription.total_duration or 0
        
        # Determine file extension from original file
        original_ext = Path(audio_path).suffix.lower()
        if not original_ext:
            original_ext = '.mp3'  # fallback
        
        # Calculate expected number of chunks
        num_chunks = (total_duration + seconds_per_chunk - 1) // seconds_per_chunk
        
        # Generate chunk filename pattern
        chunk_pattern = chunk_dir / f"chunk_%03d{original_ext}"
        
        # Run ffmpeg segmentation
        ffmpeg_cmd = [
            'ffmpeg', '-i', audio_path,
            '-f', 'segment',
            '-segment_time', str(seconds_per_chunk),
            '-c', 'copy',
            '-reset_timestamps', '1',
            '-y',  # overwrite existing files
            str(chunk_pattern)
        ]
        
        try:
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed: {e.stderr}")
            raise ChunkingError(f"Audio segmentation failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise ChunkingError("Audio segmentation timed out (>5 minutes)")
        
        # Create TranscriptionChunk objects for generated files
        chunks = []
        chunk_files = sorted(chunk_dir.glob(f"chunk_*{original_ext}"))
        
        if not chunk_files:
            raise ChunkingError("No chunk files were generated by ffmpeg")
        
        for index, chunk_file in enumerate(chunk_files):
            # Calculate chunk timing
            start_sec = index * seconds_per_chunk
            end_sec = min(start_sec + seconds_per_chunk, total_duration)
            
            # Get actual duration of the chunk
            actual_duration = self._get_chunk_duration(chunk_file)
            
            # Create relative path for FileField
            relative_path = os.path.relpath(chunk_file, settings.MEDIA_ROOT)
            
            # Create TranscriptionChunk object
            chunk = TranscriptionChunk.objects.create(
                transcription=transcription,
                index=index,
                start_time=start_sec,
                end_time=end_sec,
                duration_sec=actual_duration,
                file=relative_path,
                status="ready"
            )
            chunks.append(chunk)
        
        logger.info(f"Successfully created {len(chunks)} chunks for transcription {transcription.id}")
        return chunks
    
    def _get_chunk_duration(self, chunk_file: Path) -> float:
        """Get the actual duration of a chunk file."""
        try:
            audio_file = MutagenFile(str(chunk_file))
            if audio_file and audio_file.info:
                return float(getattr(audio_file.info, "length", 0.0))
        except Exception as e:
            logger.warning(f"Could not get duration for {chunk_file}: {e}")
        
        return 0.0
    
    def _cleanup_chunk_files(self, chunks) -> None:
        """Remove chunk files from filesystem."""
        for chunk in chunks:
            if chunk.file:
                file_path = Path(settings.MEDIA_ROOT) / chunk.file.name
                try:
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete chunk file {file_path}: {e}")
        
        # Try to remove empty chunk directory
        try:
            if chunks.exists():
                first_chunk = chunks.first()
                chunk_dir = Path(settings.MEDIA_ROOT) / first_chunk.file.name
                chunk_dir = chunk_dir.parent
                if chunk_dir.exists() and not any(chunk_dir.iterdir()):
                    chunk_dir.rmdir()
        except Exception as e:
            logger.warning(f"Could not remove chunk directory: {e}")


# Convenience function for easy importing
def chunk_transcription(transcription: Transcription, 
                       seconds_per_chunk: int = None, 
                       force: bool = False) -> List[TranscriptionChunk]:
    """
    Convenience function to chunk a transcription.
    
    Args:
        transcription: The Transcription object to chunk
        seconds_per_chunk: Duration of each chunk in seconds (default: 180)
        force: If True, purge existing chunks and recreate
    
    Returns:
        List of created TranscriptionChunk objects
    """
    service = ChunkingService()
    return service.chunk_transcription(transcription, seconds_per_chunk, force)