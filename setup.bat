@echo off
echo ================================================
echo     PODCAST FRAME PROCESSOR - INICIALIZACAO
echo ================================================
echo.

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

REM Verificar dependencias
echo Verificando dependencias...
python check_dependencies.py

echo.
echo ================================================
echo     PRONTO PARA USO!
echo ================================================
echo.
echo Para processar um podcast, use:
echo python FrameProcessor.py "URL_DO_YOUTUBE"
echo.
echo Exemplo:
echo python FrameProcessor.py "https://www.youtube.com/watch?v=abc123" --output meus_frames
echo.
echo Pressione qualquer tecla para continuar...
pause > nul
