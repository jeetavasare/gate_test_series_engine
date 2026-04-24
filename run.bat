@echo off
setlocal enabledelayedexpansion

set CMD=%1

if "%CMD%"=="" (
    py manage.py runserver
    exit /b
)


if "%CMD%"=="liveserver" (
    python manage.py runserver 0.0.0.0:8000
    exit /b
)


if "%CMD%"=="showmigrations" (
    py manage.py showmigrations
    exit /b
)

if "%CMD%"=="makemigrations" (
    py manage.py makemigrations
    exit /b
)

if "%CMD%"=="migrate" (
    py manage.py migrate
    exit /b
)

if "%CMD%"=="venv" (
    cmd /k ".venv\Scripts\activate"
    exit /b
)

if "%CMD%"=="sudoc" (
    py manage.py createsuperuser
    exit /b
)

echo Invalid command! Use one of: server, liveserver, showmigrations, makemigrations, migrate, venv, sudoc.