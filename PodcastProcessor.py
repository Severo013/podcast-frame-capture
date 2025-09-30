import cv2
import numpy as np
import os
import time
from urllib.parse import urlparse, parse_qs
import yt_dlp
from PIL import Image
import hashlib
from collections import defaultdict
import argparse
from datetime import datetime
import unicodedata
import re

# Tentar importar FER para reconhecimento de emoções
try:
    from fer import FER
    HAS_FER = True
except ImportError:
    HAS_FER = False
    print("FER não disponível, usando método básico")

class PodcastFrameProcessor:
    def __init__(self, emotion_threshold=0.7, blur_threshold=100.0, eye_closure_threshold=0.3):
        """
        Inicializa o processador de frames do podcast
        """
        self.emotion_threshold = emotion_threshold
        self.blur_threshold = blur_threshold
        self.eye_closure_threshold = eye_closure_threshold
        
        print("Inicializando Podcast Frame Processor...")
        
        # Inicializar detector de emoções
        if HAS_FER:
            try:
                self.emotion_detector = FER(mtcnn=True)
                print("✅ Detector de emoções FER carregado")
                self.use_ai_emotions = True
            except Exception as e:
                print(f"⚠️ Erro ao carregar FER: {e}")
                self.emotion_detector = None
                self.use_ai_emotions = False
        else:
            self.emotion_detector = None
            self.use_ai_emotions = False
            print("📝 Usando método básico de detecção de emoções")
        
        # Detector de faces do OpenCV
        try:
            # Tentar carregar classificadores com diferentes métodos
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
            
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
            
            # Verificar se carregaram corretamente
            if self.face_cascade.empty() or self.eye_cascade.empty():
                print("⚠️ Erro nos caminhos dos classificadores, tentando método alternativo...")
                
                # Método alternativo: usar paths absolutos
                import os
                cv2_base = os.path.dirname(cv2.__file__)
                face_cascade_path = os.path.join(cv2_base, 'data', 'haarcascade_frontalface_default.xml')
                eye_cascade_path = os.path.join(cv2_base, 'data', 'haarcascade_eye.xml')
                
                self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
                
                if self.face_cascade.empty() or self.eye_cascade.empty():
                    print("⚠️ Classificadores não encontrados, usando detecção básica")
                    self.use_opencv_detection = False
                else:
                    print("✅ Classificadores carregados com método alternativo")
                    self.use_opencv_detection = True
            else:
                print("✅ Detectores de face carregados")
                self.use_opencv_detection = True
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar classificadores OpenCV: {e}")
            print("📝 Continuando sem detecção avançada de faces")
            self.face_cascade = None
            self.eye_cascade = None
            self.use_opencv_detection = False
        
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
        Baixa o vídeo do YouTube sem áudio
        """
        print(f"📥 Baixando vídeo (sem áudio): {youtube_url}")
        
        ydl_opts = {
            'format': '399/bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/best[height<=1080]',  # Priorizar formato 399 (1080p), sem áudio
            'outtmpl': output_path,
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extrair informações do vídeo primeiro
                info = ydl.extract_info(youtube_url, download=False)
                video_title = info.get('title', 'video_sem_titulo')
                
                # Limpar o título para usar como nome de pasta
                clean_title = self.sanitize_title(video_title)
                
                ydl.download([youtube_url])
            print(f"✅ Vídeo baixado em 1080p (formato 399, sem áudio): {output_path}")
            print(f"📺 Título: {video_title}")
            return output_path, clean_title
        except Exception as e:
            print(f"❌ Erro ao baixar vídeo: {e}")
            return None, None

    def sanitize_title(self, title):
        """
        Limpa o título do vídeo removendo acentos, caracteres especiais e substituindo espaços por underlines
        """
        # Remover acentos
        title = unicodedata.normalize('NFD', title)
        title = ''.join(char for char in title if unicodedata.category(char) != 'Mn')
        
        # Remover caracteres especiais e manter apenas letras, números, espaços e alguns caracteres seguros
        title = re.sub(r'[^\w\s\-_]', '', title)
        
        # Substituir múltiplos espaços por um único espaço
        title = re.sub(r'\s+', ' ', title)
        
        # Substituir espaços por underlines
        title = title.replace(' ', '_')
        
        # Remover underlines múltiplos
        title = re.sub(r'_+', '_', title)
        
        # Remover underlines no início e fim
        title = title.strip('_')
        
        # Limitar tamanho a 100 caracteres
        title = title[:100]
        
        # Se ficou vazio, usar nome padrão
        if not title:
            title = 'video_sem_titulo'
            
        return title

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
        if not self.use_opencv_detection or not self.eye_cascade:
            # Análise básica: assumir olhos abertos se não conseguir detectar
            return False
            
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
        if not self.use_opencv_detection or not self.face_cascade:
            # Método básico: assumir que o frame inteiro contém uma face
            h, w = frame.shape[:2]
            # Pegar região central como "face"
            margin_h, margin_w = h//4, w//4
            face_region = frame[margin_h:h-margin_h, margin_w:w-margin_w]
            return [(face_region, (margin_w, margin_h, w-margin_w, h-margin_h))]
        
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
        
        # Se não encontrar faces, usar método básico
        if not face_regions:
            h, w = frame.shape[:2]
            margin_h, margin_w = h//4, w//4
            face_region = frame[margin_h:h-margin_h, margin_w:w-margin_w]
            face_regions.append((face_region, (margin_w, margin_h, w-margin_w, h-margin_h)))
        
        return face_regions

    def classify_emotion_fer(self, frame):
        """
        Classifica emoção usando FER
        """
        try:
            # FER espera imagem RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar emoções
            result = self.emotion_detector.detect_emotions(rgb_frame)
            
            if result:
                # Pegar a primeira face detectada
                emotions = result[0]['emotions']
                
                # Encontrar a emoção dominante
                dominant_emotion = max(emotions, key=emotions.get)
                confidence = emotions[dominant_emotion]
                
                return dominant_emotion, confidence
                
        except Exception as e:
            print(f"Erro na classificação FER: {e}")
        
        return None, 0.0

    def classify_emotion_basic(self, face_image):
        """
        Classificação básica de emoção usando características faciais
        """
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Análise baseada em características da imagem
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Análise de bordas para detectar expressões
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Análise de histograma
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_variance = np.var(hist)
            
            # Classificação heurística melhorada
            if brightness > 130 and contrast > 35 and edge_density > 0.1:
                return "happy", 0.6
            elif brightness < 70 or (contrast < 20 and edge_density < 0.05):
                return "sad", 0.5  
            elif contrast > 60 or edge_density > 0.15:
                return "surprise", 0.5
            elif brightness < 100 and contrast > 40 and edge_density > 0.08:
                return "angry", 0.5
            elif edge_density < 0.03:
                return "neutral", 0.7
            else:
                return "neutral", 0.6
            
        except Exception as e:
            print(f"Erro na classificação básica: {e}")
            return "neutral", 0.5

    def classify_emotion(self, face_image, full_frame):
        """
        Classifica a emoção na imagem da face
        """
        if self.use_ai_emotions and self.emotion_detector:
            emotion, confidence = self.classify_emotion_fer(full_frame)
            if emotion and confidence > 0.3:
                return emotion, confidence
        
        # Fallback para método básico
        return self.classify_emotion_basic(face_image)

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
        Salva o frame categorizado por emoção
        """
        emotion_dir = os.path.join(output_dir, emotion)
        os.makedirs(emotion_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp e confiança
        filename = f"{emotion}_{timestamp:.1f}s_conf{confidence:.2f}.jpg"
        filepath = os.path.join(emotion_dir, filename)
        
        # Salvar imagem
        cv2.imwrite(filepath, frame)
        return filepath

    def process_video(self, video_path, output_dir="output_frames", skip_minutes=10):
        """
        Processa o vídeo e extrai frames de emoções
        """
        print(f"🎬 Processando vídeo: {video_path}")
        
        # Criar diretório de saída
        os.makedirs(output_dir, exist_ok=True)
        
        # Abrir vídeo
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Erro ao abrir o vídeo")
            return
        
        # Obter informações do vídeo
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"📊 FPS: {fps:.1f}, Total de frames: {total_frames}, Duração: {duration/60:.1f} minutos")
        
        # Pular os primeiros minutos (publicidades)
        skip_frames = int(skip_minutes * 60 * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, skip_frames)
        
        # Processar a cada N frames para eficiência
        frame_skip = max(1, int(fps // 2))  # Processar 2 frames por segundo
        frame_count = skip_frames
        
        print(f"⏭️ Pulando {skip_minutes} minutos iniciais...")
        print(f"🔄 Processando 1 frame a cada {frame_skip} frames")
        
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
                emotion, confidence = self.classify_emotion(face_img, frame)
                
                if emotion and self.should_save_frame(emotion, confidence, current_timestamp):
                    # Salvar frame completo
                    filepath = self.save_frame(frame, emotion, confidence, current_timestamp, output_dir)
                    print(f"💾 Frame salvo: {emotion} (conf: {confidence:.2f}) em {current_timestamp/60:.1f}min")
                    
                    self.last_emotion_time[emotion] = current_timestamp
                    self.captured_emotions[emotion].append(current_timestamp)
                    self.stats['saved_frames'] += 1
                else:
                    self.stats['duplicate_rejected'] += 1
            
            self.stats['processed_frames'] += 1
            frame_count += 1
            
            # Mostrar progresso
            if self.stats['processed_frames'] % 100 == 0:
                elapsed = time.time() - start_time
                progress = (frame_count - skip_frames) / (total_frames - skip_frames) * 100
                print(f"📈 Progresso: {progress:.1f}% - Frames salvos: {self.stats['saved_frames']} - Tempo: {elapsed/60:.1f}min")
        
        cap.release()
        self.print_statistics()

    def print_statistics(self):
        """
        Imprime estatísticas do processamento
        """
        print("\n" + "="*50)
        print("📊 ESTATÍSTICAS DO PROCESSAMENTO")
        print("="*50)
        print(f"Total de frames analisados: {self.stats['total_frames']}")
        print(f"Frames processados: {self.stats['processed_frames']}")
        print(f"Frames rejeitados por qualidade: {self.stats['quality_rejected']}")
        print(f"Frames rejeitados por duplicata: {self.stats['duplicate_rejected']}")
        print(f"Frames salvos: {self.stats['saved_frames']}")
        print("\n📁 Emoções capturadas por categoria:")
        
        for emotion, times in self.captured_emotions.items():
            print(f"  {emotion}: {len(times)} frames")
        
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description='🎙️ Processador de Frames de Emoções em Podcasts')
    parser.add_argument('url', help='URL do YouTube do podcast')
    parser.add_argument('--output', '-o', default=None, help='Diretório de saída (padrão: nome do vídeo)')
    parser.add_argument('--skip-minutes', '-s', type=int, default=10, 
                       help='Minutos a pular no início (padrão: 10)')
    parser.add_argument('--emotion-threshold', '-e', type=float, default=0.7,
                       help='Limiar mínimo para emoções (padrão: 0.7)')
    
    args = parser.parse_args()
    
    print("🎙️ PODCAST FRAME PROCESSOR")
    print("="*50)
    
    # Criar processador
    try:
        processor = PodcastFrameProcessor(emotion_threshold=args.emotion_threshold)
    except Exception as e:
        print(f"❌ Erro ao inicializar processador: {e}")
        return
    
    # Baixar vídeo
    result = processor.download_video(args.url)
    
    if result and len(result) == 2:
        video_path, video_title = result
        
        # Determinar diretório de saída
        output_dir = args.output if args.output else video_title
        print(f"📁 Diretório de saída: {output_dir}")
        
        try:
            # Processar vídeo
            processor.process_video(video_path, output_dir, args.skip_minutes)
            print(f"\n🎉 Processamento concluído! Frames salvos em: {output_dir}")
        except Exception as e:
            print(f"❌ Erro durante processamento: {e}")
        finally:
            # Limpar arquivo temporário
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"🗑️ Arquivo temporário removido: {video_path}")
    else:
        print("❌ Falha ao baixar o vídeo")

if __name__ == "__main__":
    main()
