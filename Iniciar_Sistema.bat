@echo off
title Servidor - Gerenciamento de Rotina
echo Iniciando o sistema...

:: Abre o navegador no endereço do sistema (espera 2 segundos para o servidor subir)
start "" "http://127.0.0.1:5000"

:: Inicia o aplicativo Flask
python app.py

pause