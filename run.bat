@echo off
cd /d "%~dp0"
echo Pulling latest changes...
git pull
if errorlevel 1 echo git pull failed, continuing with local version.
call .venv\Scripts\activate
streamlit run Home.py
