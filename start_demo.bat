@echo off
echo Starting Event Management API Demo Environment...
echo.

:: Start Redis in a new window
echo Starting Redis Server...
start "Redis Server" cmd /k "redis-server"

:: Wait a couple of seconds to ensure Redis is up
timeout /t 2 /nobreak >nul

:: Start the Flask API in a new window
echo Starting Flask App...
start "Flask API" cmd /k ".\venv\Scripts\activate && python app.py"

:: Start Celery Worker in a new window (using pool=solo for Windows compatibility)
echo Starting Celery Worker...
start "Celery Worker" cmd /k ".\venv\Scripts\activate && celery -A app.celery_app worker --loglevel=info --pool=solo"

:: Start Celery Beat in a new window
echo Starting Celery Beat...
start "Celery Beat" cmd /k ".\venv\Scripts\activate && celery -A app.celery_app beat --loglevel=info"

echo.
echo All services are starting up in separate windows!
echo Once they are ready, you can access the Swagger UI at: http://localhost:5000/apidocs
echo.
pause
