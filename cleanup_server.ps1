# =================================================================
# PowerShell скрипт для очистки сервера и подготовки к Python
# Запуск: .\cleanup_server.ps1
# =================================================================

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "🧹 Подготовка сервера к Python версии" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

# Параметры подключения
$SERVER_NAME = "sigmatrade-20251108-210354"
$ZONE = "europe-north1-a"
$PROJECT = "telegram-bot-444304"
$SERVER_DIR = "/opt/sigmatrade"

Write-Host "[1/5] Проверка подключения к GCP..." -ForegroundColor Yellow

# Проверка что gcloud доступен
try {
    $gcloudVersion = gcloud version 2>&1 | Select-String "Google Cloud SDK"
    Write-Host "✅ Google Cloud SDK установлен: $gcloudVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Google Cloud SDK не найден! Установите gcloud CLI" -ForegroundColor Red
    Write-Host "https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Проверка что сервер запущен
Write-Host "`n[2/5] Проверка статуса сервера..." -ForegroundColor Yellow
$serverStatus = gcloud compute instances list --filter="name=$SERVER_NAME" --format="value(status)" 2>$null

if ($serverStatus -ne "RUNNING") {
    Write-Host "⚠️  Сервер не запущен. Статус: $serverStatus" -ForegroundColor Yellow
    $response = Read-Host "Запустить сервер? (yes/no)"
    if ($response -eq "yes") {
        Write-Host "Запуск сервера..." -ForegroundColor Yellow
        gcloud compute instances start $SERVER_NAME --zone=$ZONE --project=$PROJECT
        Write-Host "Ожидание запуска (30 сек)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        Write-Host "✅ Сервер запущен" -ForegroundColor Green
    } else {
        Write-Host "❌ Отменено" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Сервер работает" -ForegroundColor Green
}

# Копирование скрипта на сервер
Write-Host "`n[3/5] Копирование скрипта очистки на сервер..." -ForegroundColor Yellow

$scriptPath = Join-Path $PSScriptRoot "server_cleanup.sh"
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Файл server_cleanup.sh не найден!" -ForegroundColor Red
    exit 1
}

try {
    gcloud compute scp $scriptPath "${SERVER_NAME}:${SERVER_DIR}/server_cleanup.sh" --zone=$ZONE --project=$PROJECT
    Write-Host "✅ Скрипт скопирован на сервер" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка копирования скрипта: $_" -ForegroundColor Red
    exit 1
}

# Выполнение скрипта на сервере
Write-Host "`n[4/5] Запуск скрипта очистки на сервере..." -ForegroundColor Yellow
Write-Host "⚠️  ВНИМАНИЕ: Этот скрипт остановит текущий бот и очистит данные!" -ForegroundColor Red
Write-Host "⚠️  Все данные будут сохранены в бэкапы!" -ForegroundColor Yellow
$confirm = Read-Host "`nПродолжить? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "❌ Отменено пользователем" -ForegroundColor Red
    exit 0
}

Write-Host "`n🚀 Запуск очистки сервера..." -ForegroundColor Cyan
Write-Host "Это займет 5-10 минут...`n" -ForegroundColor Yellow

try {
    # Запуск скрипта на сервере
    gcloud compute ssh $SERVER_NAME --zone=$ZONE --project=$PROJECT --command="cd $SERVER_DIR && chmod +x server_cleanup.sh && bash server_cleanup.sh"
    
    Write-Host "`n✅ Скрипт выполнен успешно!" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Ошибка выполнения скрипта: $_" -ForegroundColor Red
    Write-Host "Попробуйте подключиться вручную:" -ForegroundColor Yellow
    Write-Host "  gcloud compute ssh $SERVER_NAME --zone=$ZONE" -ForegroundColor Cyan
    Write-Host "  cd $SERVER_DIR" -ForegroundColor Cyan
    Write-Host "  bash server_cleanup.sh" -ForegroundColor Cyan
    exit 1
}

# Проверка результата
Write-Host "`n[5/5] Проверка результата..." -ForegroundColor Yellow

$checkCommand = @"
cd $SERVER_DIR && \
echo '=== Python версия ===' && python3.11 --version && \
echo '=== Poetry версия ===' && poetry --version && \
echo '=== Свободное место ===' && df -h / | grep -E 'Filesystem|/$' && \
echo '=== Docker контейнеры ===' && docker ps -a && \
echo '=== Структура директорий ===' && ls -la /opt/sigmatrade/app/ 2>/dev/null || echo 'Структура не создана'
"@

try {
    gcloud compute ssh $SERVER_NAME --zone=$ZONE --project=$PROJECT --command=$checkCommand
    Write-Host "`n✅ Проверка завершена" -ForegroundColor Green
} catch {
    Write-Host "`n⚠️  Не удалось выполнить проверку, но скрипт был запущен" -ForegroundColor Yellow
}

# Итоговая информация
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "✅ Сервер подготовлен к Python версии!" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

Write-Host "📋 Следующие шаги:" -ForegroundColor Cyan
Write-Host "  1. Подключиться к серверу:" -ForegroundColor White
Write-Host "     gcloud compute ssh $SERVER_NAME --zone=$ZONE" -ForegroundColor Gray
Write-Host "`n  2. Прочитать инструкцию:" -ForegroundColor White
Write-Host "     cat /opt/sigmatrade/PYTHON_DEPLOYMENT_NEXT_STEPS.md" -ForegroundColor Gray
Write-Host "`n  3. Склонировать Python код:" -ForegroundColor White
Write-Host "     cd /opt/sigmatrade" -ForegroundColor Gray
Write-Host "     git clone -b Migration-to-Python https://github.com/YOURUSER/sigmatradebot.git ." -ForegroundColor Gray
Write-Host "`n  4. Настроить .env и запустить бота" -ForegroundColor White

Write-Host "`n📦 Бэкапы сохранены в:" -ForegroundColor Cyan
Write-Host "  /opt/sigmatrade/backups/typescript_final_*" -ForegroundColor Gray

Write-Host "`n🎉 Готово! Теперь можно разворачивать Python версию!" -ForegroundColor Green

# Опция открыть SSH сессию
Write-Host "`n" -ForegroundColor White
$openSSH = Read-Host "Открыть SSH подключение к серверу сейчас? (yes/no)"
if ($openSSH -eq "yes") {
    Write-Host "Подключение к серверу..." -ForegroundColor Cyan
    gcloud compute ssh $SERVER_NAME --zone=$ZONE --project=$PROJECT
}

Write-Host "`n✨ Скрипт завершен!" -ForegroundColor Green

