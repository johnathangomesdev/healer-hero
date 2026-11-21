@echo off
rem Arraste uma ou mais folhas (PNG) em cima deste arquivo para cortar as peças.
if "%~1"=="" (
  echo Arraste a imagem da folha em cima deste arquivo.
  pause
  exit /b
)
:loop
if "%~1"=="" goto fim
python "%~dp0cortar_pecas.py" "%~1"
shift
goto loop
:fim
pause
