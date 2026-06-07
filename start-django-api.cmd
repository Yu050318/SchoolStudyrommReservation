@echo off
cd /d "%~dp0django_backend"
python manage.py runserver 127.0.0.1:3001
