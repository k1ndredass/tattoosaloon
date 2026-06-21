Write-Host "Остановите сервер Django (Ctrl+C), если он запущен" -ForegroundColor Yellow
Read-Host "Нажмите Enter для продолжения"

Write-Host "Удаление старой базы данных..." -ForegroundColor Yellow
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "База данных удалена" -ForegroundColor Green
} else {
    Write-Host "База данных не найдена" -ForegroundColor Gray
}

Write-Host "Создание новой базы данных..." -ForegroundColor Yellow
python manage.py migrate

Write-Host "База данных успешно создана!" -ForegroundColor Green
Read-Host "Нажмите Enter для выхода"




