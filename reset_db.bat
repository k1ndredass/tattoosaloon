@echo off
echo Остановите сервер Django (Ctrl+C), если он запущен
pause
echo Удаление старой базы данных...
if exist db.sqlite3 del db.sqlite3
echo Создание новой базы данных...
python manage.py migrate
echo База данных успешно создана!
pause

