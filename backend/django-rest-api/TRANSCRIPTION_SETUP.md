# Audio Transcription System - Installation & Setup Guide

## 📦 Dependencies Installation

Install the required packages in your conda environment:

```bash
# Activate the conda environment
conda activate atenas-backend

# Install Celery and Redis client
pip install celery redis

# Install Whisper for transcription
pip install openai-whisper

# Install additional dependencies if needed
pip install torch torchvision torchaudio  # For Whisper model inference
```

## 🚀 Redis Setup

### macOS (using Homebrew):
```bash
# Install Redis
brew install redis

# Start Redis server
brew services start redis

# Or start manually:
redis-server
```

### Ubuntu/Debian:
```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

## 🔧 Starting the System

### 1. Start Redis (if not running as service):
```bash
redis-server
```

### 2. Start Django Development Server:
```bash
cd backend/django-rest-api
conda activate atenas-backend
python manage.py runserver
```

### 3. Start Celery Worker (in another terminal):
```bash
cd backend/django-rest-api
conda activate atenas-backend
celery -A config worker --loglevel=info
```

### 4. Optional: Start Celery Flower (monitoring):
```bash
pip install flower
celery -A config flower
# Access http://localhost:5555 for monitoring
```

## 🎯 API Usage Examples

### 1. Upload and Auto-Chunk Audio:
```bash
curl -X POST http://localhost:8000/api/transcriptions/upload/ \
  -H "Authorization: Bearer <your-token>" \
  -F "audio_file=@your_audio.mp3"
```

### 2. Start Transcription:
```bash
curl -X POST http://localhost:8000/api/transcriptions/{id}/transcribe/ \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"model": "base", "language": "es", "force": false}'
```

### 3. Check Progress:
```bash
curl -X GET http://localhost:8000/api/transcriptions/{id}/chunks/ \
  -H "Authorization: Bearer <your-token>"
```

## 🏗️ System Architecture

```
[Upload] → [Chunk] → [Transcribe] → [Summarize (future)]
    ↓         ↓          ↓
  Django   Django    Celery+Whisper
```

### Status Flow:
- **Transcription**: `uploaded` → `chunked` → `transcribing` → `transcribed`
- **Chunks**: `ready` → `transcribing` → `done`

## 🔍 Troubleshooting

### Common Issues:

1. **Celery can't connect to Redis:**
   - Check if Redis is running: `redis-cli ping`
   - Verify Redis URL in settings: `redis://localhost:6379/0`

2. **Whisper model download fails:**
   - Models are downloaded automatically on first use
   - Check internet connection and disk space (~1GB for medium model)

3. **Tasks stuck in pending:**
   - Ensure Celery worker is running
   - Check worker logs for errors
   - Verify task routing configuration

4. **Out of memory errors:**
   - Use smaller Whisper models (`tiny`, `base`, `small`)
   - Reduce worker concurrency: `celery -A config worker --concurrency=1`
   - Monitor system resources

### Monitoring Commands:

```bash
# Check Redis connection
redis-cli ping

# List active Celery tasks
celery -A config inspect active

# Check worker status
celery -A config inspect stats

# Purge all tasks (if needed)
celery -A config purge
```

## 🎛️ Configuration

### Whisper Model Sizes:
- **tiny**: ~39MB, fastest, lowest accuracy
- **base**: ~74MB, balanced (recommended)
- **small**: ~244MB, better accuracy
- **medium**: ~769MB, high accuracy
- **large**: ~1550MB, highest accuracy

### Performance Tips:
- Use GPU if available (automatic detection)
- Start with `base` model, upgrade based on needs
- Monitor memory usage with larger models
- Consider chunking duration vs. context trade-offs

## 🧪 Testing

Use the provided test endpoints to verify setup:

```python
# Test Celery + Whisper
from apps.api.tasks import test_whisper
result = test_whisper.delay()
print(result.get())
```