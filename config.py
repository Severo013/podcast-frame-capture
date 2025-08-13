"""
Configurações e constantes para o Podcast Frame Processor
"""

# Configurações de Processamento
DEFAULT_EMOTION_THRESHOLD = 0.7
DEFAULT_BLUR_THRESHOLD = 100.0
DEFAULT_EYE_CLOSURE_THRESHOLD = 0.3
DEFAULT_SKIP_MINUTES = 10
DEFAULT_MIN_TIME_BETWEEN_EMOTIONS = 30  # segundos

# Configurações de Performance  
DEFAULT_FRAME_SKIP_RATIO = 2  # processar 2 frames por segundo
MAX_VIDEO_HEIGHT = 720  # qualidade máxima para download

# Modelos de IA
EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"
ALTERNATIVE_EMOTION_MODEL = "cardiffnlp/twitter-roberta-base-emotion"

# Mapeamento de emoções para português
EMOTION_MAPPING = {
    'joy': 'alegria',
    'happiness': 'felicidade', 
    'anger': 'raiva',
    'rage': 'furia',
    'surprise': 'surpresa',
    'fear': 'medo',
    'sadness': 'tristeza',
    'disgust': 'nojo',
    'neutral': 'neutro',
    'calm': 'calmo'
}

# Emoções consideradas "fortes" (prioritárias para captura)
STRONG_EMOTIONS = ['joy', 'happiness', 'anger', 'rage', 'surprise', 'fear']

# Configurações de qualidade de imagem
MIN_FACE_SIZE = (100, 100)  # tamanho mínimo da face para processamento
FACE_MARGIN = 20  # margem ao redor da face detectada

# Configurações de arquivo
TEMP_VIDEO_NAME = "temp_podcast_video.mp4"
DEFAULT_OUTPUT_DIR = "output_frames"

# Formato dos arquivos salvos
IMAGE_FORMAT = "jpg"
IMAGE_QUALITY = 95  # qualidade JPEG (0-100)

# Mensagens de status
STATUS_MESSAGES = {
    'downloading': "Baixando vídeo do YouTube...",
    'processing': "Processando frames do vídeo...", 
    'analyzing': "Analisando emoções...",
    'saving': "Salvando frame capturado...",
    'complete': "Processamento concluído!",
    'error': "Erro durante o processamento"
}
