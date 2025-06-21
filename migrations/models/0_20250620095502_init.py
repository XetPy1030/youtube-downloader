from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "telegram_id" BIGINT NOT NULL UNIQUE,
    "username" VARCHAR(255),
    "first_name" VARCHAR(255),
    "last_name" VARCHAR(255),
    "is_admin" BOOL NOT NULL DEFAULT False,
    "is_blocked" BOOL NOT NULL DEFAULT False,
    "language_code" VARCHAR(10),
    "total_downloads" INT NOT NULL DEFAULT 0,
    "total_download_size" BIGINT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_activity" TIMESTAMPTZ
);
COMMENT ON COLUMN "users"."telegram_id" IS 'Telegram ID пользователя';
COMMENT ON COLUMN "users"."username" IS 'Telegram username';
COMMENT ON COLUMN "users"."first_name" IS 'Имя пользователя';
COMMENT ON COLUMN "users"."last_name" IS 'Фамилия пользователя';
COMMENT ON COLUMN "users"."is_admin" IS 'Является ли администратором';
COMMENT ON COLUMN "users"."is_blocked" IS 'Заблокирован ли пользователь';
COMMENT ON COLUMN "users"."language_code" IS 'Код языка';
COMMENT ON COLUMN "users"."total_downloads" IS 'Общее количество скачиваний';
COMMENT ON COLUMN "users"."total_download_size" IS 'Общий размер скачанных файлов';
COMMENT ON COLUMN "users"."created_at" IS 'Дата регистрации';
COMMENT ON COLUMN "users"."updated_at" IS 'Дата последнего обновления';
COMMENT ON COLUMN "users"."last_activity" IS 'Последняя активность';
COMMENT ON TABLE "users" IS 'Пользователи бота';
CREATE TABLE IF NOT EXISTS "videos" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "video_id" VARCHAR(255) NOT NULL UNIQUE,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "duration" INT,
    "view_count" BIGINT,
    "like_count" BIGINT,
    "channel_name" VARCHAR(255),
    "channel_id" VARCHAR(255),
    "upload_date" DATE,
    "thumbnail_url" TEXT,
    "available_formats" JSONB,
    "file_size" BIGINT,
    "quality" VARCHAR(50),
    "format_id" VARCHAR(50),
    "download_count" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "videos"."video_id" IS 'YouTube ID видео';
COMMENT ON COLUMN "videos"."title" IS 'Название видео';
COMMENT ON COLUMN "videos"."description" IS 'Описание видео';
COMMENT ON COLUMN "videos"."duration" IS 'Длительность в секундах';
COMMENT ON COLUMN "videos"."view_count" IS 'Количество просмотров';
COMMENT ON COLUMN "videos"."like_count" IS 'Количество лайков';
COMMENT ON COLUMN "videos"."channel_name" IS 'Название канала';
COMMENT ON COLUMN "videos"."channel_id" IS 'ID канала';
COMMENT ON COLUMN "videos"."upload_date" IS 'Дата загрузки видео';
COMMENT ON COLUMN "videos"."thumbnail_url" IS 'URL превью';
COMMENT ON COLUMN "videos"."available_formats" IS 'Доступные форматы';
COMMENT ON COLUMN "videos"."file_size" IS 'Размер файла в байтах';
COMMENT ON COLUMN "videos"."quality" IS 'Качество видео';
COMMENT ON COLUMN "videos"."format_id" IS 'ID формата';
COMMENT ON COLUMN "videos"."download_count" IS 'Количество скачиваний';
COMMENT ON COLUMN "videos"."created_at" IS 'Дата добавления';
COMMENT ON COLUMN "videos"."updated_at" IS 'Дата обновления';
COMMENT ON TABLE "videos" IS 'YouTube видео';
CREATE TABLE IF NOT EXISTS "download_history" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "status" VARCHAR(11) NOT NULL DEFAULT 'pending',
    "quality" VARCHAR(50),
    "format_type" VARCHAR(20) NOT NULL DEFAULT 'mp4',
    "file_size" BIGINT,
    "download_speed" DOUBLE PRECISION,
    "file_path" TEXT,
    "telegram_file_id" VARCHAR(255),
    "error_message" TEXT,
    "metadata" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "started_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "video_id" INT NOT NULL REFERENCES "videos" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "download_history"."status" IS 'Статус скачивания';
COMMENT ON COLUMN "download_history"."quality" IS 'Выбранное качество';
COMMENT ON COLUMN "download_history"."format_type" IS 'Тип формата';
COMMENT ON COLUMN "download_history"."file_size" IS 'Размер файла в байтах';
COMMENT ON COLUMN "download_history"."download_speed" IS 'Скорость скачивания в Мб/с';
COMMENT ON COLUMN "download_history"."file_path" IS 'Путь к скачанному файлу';
COMMENT ON COLUMN "download_history"."telegram_file_id" IS 'ID файла в Telegram';
COMMENT ON COLUMN "download_history"."error_message" IS 'Сообщение об ошибке';
COMMENT ON COLUMN "download_history"."metadata" IS 'Дополнительные метаданные';
COMMENT ON COLUMN "download_history"."created_at" IS 'Дата создания';
COMMENT ON COLUMN "download_history"."started_at" IS 'Дата начала скачивания';
COMMENT ON COLUMN "download_history"."completed_at" IS 'Дата завершения';
COMMENT ON COLUMN "download_history"."user_id" IS 'Пользователь';
COMMENT ON COLUMN "download_history"."video_id" IS 'Видео';
COMMENT ON TABLE "download_history" IS 'История скачиваний';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
