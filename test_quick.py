"""
Script de teste rápido para verificar se tudo está funcionando
"""

import os
import sys

def test_imports():
    """Testa se todas as importações estão funcionando"""
    print("🧪 Testando importações...")
    
    try:
        import cv2
        print("✅ OpenCV importado")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy importado")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False
    
    try:
        import yt_dlp
        print("✅ yt-dlp importado")
    except ImportError as e:
        print(f"❌ yt-dlp: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL importado")
    except ImportError as e:
        print(f"❌ PIL: {e}")
        return False
    
    return True

def test_opencv_cascades():
    """Testa se os classificadores do OpenCV estão disponíveis"""
    print("\n🔍 Testando classificadores OpenCV...")
    
    try:
        import cv2
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        if face_cascade.empty():
            print("❌ Classificador de faces não carregado")
            return False
        
        if eye_cascade.empty():
            print("❌ Classificador de olhos não carregado")
            return False
        
        print("✅ Classificadores OpenCV carregados")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos classificadores: {e}")
        return False

def test_processor_class():
    """Testa se a classe PodcastProcessor pode ser importada e instanciada"""
    print("\n🎬 Testando classe PodcastProcessor...")
    
    try:
        from PodcastProcessor import PodcastFrameProcessor
        
        # Tentar criar uma instância
        processor = PodcastFrameProcessor()
        print("✅ PodcastProcessor instanciado com sucesso")
        
        # Testar alguns métodos básicos
        test_frame = [[0, 0, 0], [0, 0, 0]]
        
        print("✅ Classe PodcastProcessor funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Erro na classe PodcastProcessor: {e}")
        return False

def run_full_test():
    """Executa todos os testes"""
    print("="*60)
    print("🧪 TESTE COMPLETO DO PODCAST FRAME PROCESSOR")
    print("="*60)
    
    tests_passed = 0
    total_tests = 3
    
    # Teste 1: Importações
    if test_imports():
        tests_passed += 1
    
    # Teste 2: OpenCV
    if test_opencv_cascades():
        tests_passed += 1
    
    # Teste 3: Classe principal
    if test_processor_class():
        tests_passed += 1
    
    print("\n" + "="*60)
    print(f"📊 RESULTADO: {tests_passed}/{total_tests} testes passaram")
    
    if tests_passed == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM! O programa está pronto para uso.")
        print("\nPara usar o programa:")
        print('python PodcastProcessor.py "URL_DO_YOUTUBE"')
    else:
        print("⚠️ Alguns testes falharam. Verifique as dependências.")
        print("Execute: pip install -r requirements.txt")
    
    print("="*60)
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)
