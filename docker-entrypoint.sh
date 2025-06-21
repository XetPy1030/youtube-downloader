#!/bin/bash
set -e

echo "🐳 YouTube Downloader Bot - Docker Entrypoint"

# Функция ожидания доступности базы данных
wait_for_db() {
    echo "⏳ Ожидание доступности базы данных..."
    
    while ! python -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.close()
    print('✅ База данных доступна')
except Exception as e:
    print(f'❌ База данных недоступна: {e}')
    sys.exit(1)
" 2>/dev/null; do
        echo "🔄 Ожидание базы данных..."
        sleep 2
    done
}

# Функция инициализации aerich
init_aerich() {
    echo "🔧 Инициализация Aerich..."
    
    # Проверяем, инициализирован ли aerich
    if [ ! -f "aerich.ini" ]; then
        echo "🚀 Инициализируем Aerich..."
        aerich init -t db_config.TORTOISE_ORM
        echo "✅ Aerich инициализирован"
    else
        echo "✅ Aerich уже инициализирован"
    fi
    
    # Проверяем, есть ли миграции
    if [ ! -d "migrations" ]; then
        echo "📦 Создаем начальную миграцию..."
        aerich init-db
        echo "✅ Начальная миграция создана"
    else
        echo "✅ Миграции уже существуют"
        
        # Применяем миграции
        echo "🔄 Применяем миграции..."
        aerich upgrade
        echo "✅ Миграции применены"
    fi
}

# Функция проверки настроек
check_settings() {
    echo "🔍 Проверка настроек..."
    
    if [ -z "$BOT_TOKEN" ]; then
        echo "❌ BOT_TOKEN не установлен!"
        exit 1
    fi
    
    if [ -z "$ADMIN_IDS" ]; then
        echo "⚠️ ADMIN_IDS не установлены - бот будет работать без администраторов"
    fi
    
    echo "✅ Настройки корректны"
}

# Основная логика
main() {
    echo "🎬 Запуск YouTube Downloader Bot..."
    
    # Проверяем настройки
    check_settings
    
    # Ждем базу данных
    wait_for_db
    
    # Инициализируем aerich
    init_aerich
    
    echo "🎉 Инициализация завершена!"
    echo "🚀 Запускаем бота..."
    
    # Запускаем команду переданную в docker
    exec "$@"
}

# Запускаем основную функцию
main "$@" 