@echo off
echo Instalando Dragon Bot...
winget install Python.Python.3.12
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
echo Pronto! Rode main_gui.py
pause
