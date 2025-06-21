-- Инициализация базы данных для YouTube Downloader Bot
-- Этот файл выполняется автоматически при первом запуске PostgreSQL контейнера

-- Настройки для оптимальной работы
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'none';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Создаем расширения
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Настройки производительности
ALTER SYSTEM SET effective_cache_size = '256MB';
ALTER SYSTEM SET shared_buffers = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '16MB';
ALTER SYSTEM SET work_mem = '4MB';

-- Логирование
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Применяем настройки
SELECT pg_reload_conf(); 