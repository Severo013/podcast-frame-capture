"""
Script de verificação das dependências do Podcast Frame Processor
"""

import sys
import importlib

def check_dependency(module_name, package_name=None):
    """Verifica se uma dependência está instalada e funcionando"""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'Versão desconhecida')
        print(f"✅ {package_name or module_name}: {version}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: NÃO INSTALADO - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {package_name or module_name}: ERRO - {e}")
        return False

def check_opencv():
    """Verificação específica do OpenCV"""
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
        
        # Testar carregamento dos classificadores
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        if face_cascade.empty():
            print("⚠️  OpenCV: Classificador de faces não encontrado")
            return False
        if eye_cascade.empty():
            print("⚠️  OpenCV: Classificador de olhos não encontrado")
            return False
            
        print("✅ OpenCV: Classificadores carregados com sucesso")
        return True
    except Exception as e:
        print(f"❌ OpenCV: ERRO - {e}")
        return False

def check_torch():
    """Verificação específica do PyTorch"""
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        
        # Verificar disponibilidade de CUDA
        if torch.cuda.is_available():
            print(f"✅ CUDA disponível: {torch.cuda.get_device_name(0)}")
            print(f"   Versão CUDA: {torch.version.cuda}")
        else:
            print("ℹ️  CUDA não disponível - processamento será feito na CPU")
        
        return True
    except Exception as e:
        print(f"❌ PyTorch: ERRO - {e}")
        return False

def check_transformers():
    """Verificação específica do Transformers"""
    try:
        from transformers import pipeline
        print("✅ Transformers: Importação bem-sucedida")
        
        # Testar carregamento de um pipeline simples
        print("ℹ️  Testando carregamento do modelo de emoções...")
        try:
            classifier = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-emotion")
            print("✅ Transformers: Modelo de teste carregado com sucesso")
            del classifier  # Liberar memória
        except Exception as e:
            print(f"⚠️  Transformers: Erro ao carregar modelo de teste - {e}")
        
        return True
    except Exception as e:
        print(f"❌ Transformers: ERRO - {e}")
        return False

def main():
    print("="*60)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS - PODCAST FRAME PROCESSOR")
    print("="*60)
    print(f"Python: {sys.version}")
    print("-"*60)
    
    dependencies = [
        ("numpy", "NumPy"),
        ("PIL", "Pillow"),
        ("yt_dlp", "yt-dlp"),
        ("accelerate", "Accelerate"),
    ]
    
    all_good = True
    
    # Verificações básicas
    for module, name in dependencies:
        if not check_dependency(module, name):
            all_good = False
    
    print("-"*60)
    
    # Verificações específicas
    if not check_opencv():
        all_good = False
    
    if not check_torch():
        all_good = False
    
    if not check_transformers():
        all_good = False
    
    print("-"*60)
    
    if all_good:
        print("🎉 TODAS AS DEPENDÊNCIAS ESTÃO FUNCIONANDO!")
        print("O Podcast Frame Processor está pronto para uso.")
    else:
        print("⚠️  ALGUMAS DEPENDÊNCIAS APRESENTARAM PROBLEMAS")
        print("Instale as dependências em falta com:")
        print("pip install -r requirements.txt")
    
    print("="*60)

if __name__ == "__main__":
    main()
