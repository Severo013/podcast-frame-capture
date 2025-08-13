import cv2
import numpy as np
import os
import time
from urllib.parse import urlparse, parse_qs
import yt_dlp
from transformers import pipeline
import torch
from PIL import Image
import hashlib
from collections import defaultdict
import argparse
from datetime import datetime

class PodcastFrameProcessor:
    def __init__(self, emotion_threshold=0.8, blur_threshold=100.0, eye_closure_threshold=0.3):
        """
        Inicializa o processador de frames do podcast
        
        Args:
            emotion_threshold: Limiar mínimo para considerar uma emoção forte
            blur_threshold: Limiar para detectar imagens borradas (Laplacian variance)
            eye_closure_threshold: Limiar para detectar olhos fechados
        """
        self.emotion_threshold = emotion_threshold
        self.blur_threshold = blur_threshold
        self.eye_closure_threshold = eye_closure_threshold
        
        # Configurar dispositivo
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Usando dispositivo: {self.device}")
        
        # Inicializar modelos
        print("Carregando modelos de IA...")
        try:
            # Tentar carregar modelo específico para emoções em imagens
            self.emotion_classifier = pipeline(
                "image-classification",
                model="trpakov/vit-face-expression",
                device=0 if torch.cuda.is_available() else -1
            )
            print("Modelo de emoções carregado: vit-face-expression")
        except Exception as e:
            print(f"Erro ao carregar modelo principal: {e}")
            print("Tentando modelo alternativo...")
            try:
                # Modelo alternativo
                self.emotion_classifier = pipeline(
                    "image-classification", 
                    model="microsoft/DialoGPT-medium",
                    device=0 if torch.cuda.is_available() else -1
                )
                print("Modelo alternativo carregado")
            except Exception as e2:
                print(f"Erro ao carregar modelo alternativo: {e2}")
                print("Usando classificador baseado em características faciais...")
                self.emotion_classifier = None
        
        # Detector de faces do OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Controle de duplicatas
        self.captured_emotions = defaultdict(list)
        self.last_emotion_time = defaultdict(float)
        self.min_time_between_same_emotion = 30  # segundos
        
        # Estatísticas
        self.stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'quality_rejected': 0,
            'duplicate_rejected': 0,
            'saved_frames': 0
        }

    def download_video(self, youtube_url, output_path="temp_video.mp4"):
        """
        Baixa o vídeo do YouTube
        """
        print(f"Baixando vídeo: {youtube_url}")
        
        ydl_opts = {
            'format': 'best[height<=1080]',  # Qualidade 1080p para melhor resolução
            'outtmpl': output_path,
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            print(f"Vídeo baixado: {output_path}")
            return output_path
        except Exception as e:
            print(f"Erro ao baixar vídeo: {e}")
            return None

    def is_blurry(self, image):
        """
        Detecta se a imagem está borrada usando Laplacian variance
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var < self.blur_threshold

    def are_eyes_closed(self, face_region):
        """
        Detecta se os olhos estão fechados na região da face
        """
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(gray_face, 1.1, 5)
        
        if len(eyes) < 2:
            return True  # Se não detectar pelo menos 2 olhos, considera como fechados
        
        # Análise simples: se detectar olhos, considera abertos
        return False

    def extract_face_region(self, frame):
        """
        Extrai regiões de faces do frame
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        face_regions = []
        for (x, y, w, h) in faces:
            # Expandir um pouco a região da face
            margin = 20
            x_start = max(0, x - margin)
            y_start = max(0, y - margin)
            x_end = min(frame.shape[1], x + w + margin)
            y_end = min(frame.shape[0], y + h + margin)
            
            face_region = frame[y_start:y_end, x_start:x_end]
            face_regions.append((face_region, (x_start, y_start, x_end, y_end)))
        
        return face_regions

    def classify_emotion(self, face_image):
        """
        Classifica a emoção na imagem da face
        """
        try:
            if self.emotion_classifier is None:
                # Fallback: análise básica baseada em características
                return self.classify_emotion_basic(face_image)
            
            # Converter BGR para RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(face_rgb)
            
            # Classificar emoção
            results = self.emotion_classifier(pil_image)
            
            if results:
                top_emotion = results[0]
                return top_emotion['label'], top_emotion['score']
            
        except Exception as e:
            print(f"Erro na classificação de emoção: {e}")
            # Fallback para método básico
            return self.classify_emotion_basic(face_image)
        
        return None, 0.0

    def classify_emotion_basic(self, face_image):
        """
        Classificação básica de emoção usando características faciais
        (fallback quando o modelo AI não está disponível)
        """
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Detectar olhos e boca
            eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 5)
            
            # Análise simples baseada em detecções
            if len(eyes) >= 2:
                # Calcular algumas métricas básicas
                brightness = np.mean(gray)
                contrast = np.std(gray)
                
                # Classificação muito básica baseada em heurísticas
                if brightness > 120 and contrast > 30:
                    return "joy", 0.6
                elif brightness < 80:
                    return "sadness", 0.5  
                elif contrast > 50:
                    return "surprise", 0.5
                else:
                    return "neutral", 0.7
            
            return "neutral", 0.5
            
        except Exception as e:
            print(f"Erro na classificação básica: {e}")
            return "neutral", 0.5

    def should_save_frame(self, emotion, confidence, current_time):
        """
        Determina se o frame deve ser salvo baseado na emoção e timing
        """
        if confidence < self.emotion_threshold:
            return False
        
        # Verificar se já capturou essa emoção recentemente
        last_time = self.last_emotion_time.get(emotion, 0)
        if current_time - last_time < self.min_time_between_same_emotion:
            return False
        
        return True

    def save_frame(self, frame, emotion, confidence, timestamp, output_dir):
        """
        Salva o frame categorizado por emoção com alta qualidade
        """
        emotion_dir = os.path.join(output_dir, emotion)
        os.makedirs(emotion_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp e confiança
        filename = f"{emotion}_{timestamp:.1f}s_conf{confidence:.2f}.jpg"
        filepath = os.path.join(emotion_dir, filename)
        
        # Salvar imagem com alta qualidade
        # Configurações para máxima qualidade JPEG
        jpeg_params = [cv2.IMWRITE_JPEG_QUALITY, 95]  # Qualidade 95% (máximo recomendado)
        
        # Alternativa: salvar como PNG para qualidade sem perdas (arquivo maior)
        # filename = f"{emotion}_{timestamp:.1f}s_conf{confidence:.2f}.png"
        # filepath = os.path.join(emotion_dir, filename)
        # png_params = [cv2.IMWRITE_PNG_COMPRESSION, 1]  # Compressão mínima
        # cv2.imwrite(filepath, frame, png_params)
        
        cv2.imwrite(filepath, frame, jpeg_params)
        return filepath

    def process_video(self, video_path, output_dir="output_frames", skip_minutes=10):
        """
        Processa o vídeo e extrai frames de emoções
        """
        print(f"Processando vídeo: {video_path}")
        
        # Criar diretório de saída
        os.makedirs(output_dir, exist_ok=True)
        
        # Abrir vídeo
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Erro ao abrir o vídeo")
            return
        
        # Obter informações do vídeo
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"FPS: {fps}, Total de frames: {total_frames}, Duração: {duration/60:.1f} minutos")
        
        # Pular os primeiros minutos (publicidades)
        skip_frames = int(skip_minutes * 60 * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, skip_frames)
        
        # Processar a cada N frames para eficiência
        frame_skip = max(1, int(fps // 2))  # Processar 2 frames por segundo
        frame_count = skip_frames
        
        print(f"Iniciando processamento (pulando {skip_minutes} minutos iniciais)...")
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            self.stats['total_frames'] += 1
            
            # Pular frames para eficiência
            if frame_count % frame_skip != 0:
                frame_count += 1
                continue
            
            current_timestamp = frame_count / fps
            
            # Verificar qualidade da imagem
            if self.is_blurry(frame):
                self.stats['quality_rejected'] += 1
                frame_count += 1
                continue
            
            # Extrair faces
            face_regions = self.extract_face_region(frame)
            
            if not face_regions:
                frame_count += 1
                continue
            
            # Processar cada face
            for face_img, face_coords in face_regions:
                # Verificar se os olhos estão fechados
                if self.are_eyes_closed(face_img):
                    continue
                
                # Classificar emoção
                emotion, confidence = self.classify_emotion(face_img)
                
                if emotion and self.should_save_frame(emotion, confidence, current_timestamp):
                    # Salvar frame completo (não apenas a face)
                    filepath = self.save_frame(frame, emotion, confidence, current_timestamp, output_dir)
                    print(f"Frame salvo: {emotion} (conf: {confidence:.2f}) em {current_timestamp/60:.1f}min - {filepath}")
                    
                    self.last_emotion_time[emotion] = current_timestamp
                    self.stats['saved_frames'] += 1
                else:
                    self.stats['duplicate_rejected'] += 1
            
            self.stats['processed_frames'] += 1
            frame_count += 1
            
            # Mostrar progresso
            if self.stats['processed_frames'] % 100 == 0:
                elapsed = time.time() - start_time
                progress = (frame_count - skip_frames) / (total_frames - skip_frames) * 100
                print(f"Progresso: {progress:.1f}% - Frames salvos: {self.stats['saved_frames']} - Tempo: {elapsed/60:.1f}min")
        
        cap.release()
        self.print_statistics()

    def print_statistics(self):
        """
        Imprime estatísticas do processamento
        """
        print("\n" + "="*50)
        print("ESTATÍSTICAS DO PROCESSAMENTO")
        print("="*50)
        print(f"Total de frames analisados: {self.stats['total_frames']}")
        print(f"Frames processados: {self.stats['processed_frames']}")
        print(f"Frames rejeitados por qualidade: {self.stats['quality_rejected']}")
        print(f"Frames rejeitados por duplicata: {self.stats['duplicate_rejected']}")
        print(f"Frames salvos: {self.stats['saved_frames']}")
        print("\nEmoções capturadas por categoria:")
        
        for emotion, times in self.captured_emotions.items():
            print(f"  {emotion}: {len(times)} frames")

def main():
    parser = argparse.ArgumentParser(description='Processador de Frames de Emoções em Podcasts')
    parser.add_argument('url', help='URL do YouTube do podcast')
    parser.add_argument('--output', '-o', default='output_frames', help='Diretório de saída')
    parser.add_argument('--skip-minutes', '-s', type=int, default=10, 
                       help='Minutos a pular no início (padrão: 10)')
    parser.add_argument('--emotion-threshold', '-e', type=float, default=0.7,
                       help='Limiar mínimo para emoções (padrão: 0.7)')
    
    args = parser.parse_args()
    
    # Criar processador
    processor = PodcastFrameProcessor(emotion_threshold=args.emotion_threshold)
    
    # Baixar vídeo
    video_path = processor.download_video(args.url)
    
    if video_path:
        try:
            # Processar vídeo
            processor.process_video(video_path, args.output, args.skip_minutes)
            print(f"\nProcessamento concluído! Frames salvos em: {args.output}")
        finally:
            # Limpar arquivo temporário
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"Arquivo temporário removido: {video_path}")
    else:
        print("Falha ao baixar o vídeo")

if __name__ == "__main__":
    main()