@echo off
rem Запуск: run.bat [--config файл]   Тесты: run.bat test
cd /d "%~dp0"
set PYTHONPATH=src
if "%1"=="test" (
    python -m unittest discover -s tests -v
    exit /b %errorlevel%
)
python -m depviz %*
