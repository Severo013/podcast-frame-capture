"""
Script de exemplo para testar o FrameProcessor

Este script demonstra como usar o processador de frames programaticamente
"""

from FrameProcessor import PodcastFrameProcessor

def test_processor():
    # URL de exemplo (substitua por uma URL real para testar)
    youtube_url = "https://www.youtube.com/watch?v=EXEMPLO"
    
    # Criar processador com configurações personalizadas
    processor = PodcastFrameProcessor(
        emotion_threshold=0.75,  # Emoções mais fortes
        blur_threshold=120.0,    # Menos tolerante a blur
        eye_closure_threshold=0.3
    )
    
    print("Testando o processador de frames...")
    print(f"URL: {youtube_url}")
    print(f"Limiar de emoção: {processor.emotion_threshold}")
    print(f"Limiar de blur: {processor.blur_threshold}")
    
    # Baixar e processar vídeo
    video_path = processor.download_video(youtube_url, "test_video.mp4")
    
    if video_path:
        try:
            processor.process_video(
                video_path, 
                output_dir="test_output", 
                skip_minutes=5  # Pular menos tempo para teste
            )
            print("Teste concluído com sucesso!")
        except Exception as e:
            print(f"Erro durante o processamento: {e}")
        finally:
            # Limpar
            import os
            if os.path.exists(video_path):
                os.remove(video_path)
    else:
        print("Falha no download - verifique a URL")

if __name__ == "__main__":
    print("="*50)
    print("TESTE DO PODCAST FRAME PROCESSOR")
    print("="*50)
    print("ATENÇÃO: Substitua a URL de exemplo por uma URL real!")
    print("="*50)
    
    # Descomente a linha abaixo para executar o teste
    # test_processor()
    
    print("Para executar o teste, edite este arquivo e descomente a chamada test_processor()")
