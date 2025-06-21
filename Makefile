.PHONY: help dev prod dev-up dev-down prod-up prod-down dev-logs prod-logs clean

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)YouTube Downloader Bot - Команды Docker Compose$(NC)"
	@echo ""
	@echo "$(YELLOW)Разработка:$(NC)"
	@echo "  dev-up        Запустить сервисы для разработки (DB + Redis)"
	@echo "  dev-down      Остановить сервисы разработки"
	@echo "  dev-logs      Посмотреть логи сервисов разработки"
	@echo "  dev-shell-db  Подключиться к shell PostgreSQL"
	@echo "  dev-shell-redis  Подключиться к shell Redis"
	@echo ""
	@echo "$(YELLOW)Продакшн:$(NC)"
	@echo "  prod-up       Запустить все сервисы для продакшена"
	@echo "  prod-down     Остановить продакшн сервисы"
	@echo "  prod-logs     Посмотреть логи продакшн сервисов"
	@echo "  prod-restart  Перезапустить продакшн сервисы"
	@echo ""
	@echo "$(YELLOW)Общие:$(NC)"
	@echo "  clean         Очистить все контейнеры и volumes"
	@echo "  status        Показать статус всех контейнеров"
	@echo ""

# ===========================================
# КОМАНДЫ ДЛЯ РАЗРАБОТКИ
# ===========================================

dev-up: ## Запустить сервисы для разработки
	@echo "$(GREEN)Запуск сервисов для разработки...$(NC)"
	DB_PORT=5432 REDIS_PORT=6379 docker compose --profile development up -d
	@echo "$(GREEN)Сервисы запущены!$(NC)"
	@echo "$(YELLOW)PostgreSQL:$(NC) localhost:5432"
	@echo "$(YELLOW)Redis:$(NC) localhost:6379"

dev-down: ## Остановить сервисы разработки
	@echo "$(RED)Остановка сервисов разработки...$(NC)"
	docker compose --profile development down

dev-logs: ## Посмотреть логи сервисов разработки
	docker compose --profile development logs -f

dev-shell-db: ## Подключиться к shell PostgreSQL
	docker exec -it youtube-downloader-db psql -U youtube_user -d youtube_bot

dev-shell-redis: ## Подключиться к shell Redis
	docker exec -it youtube-downloader-redis redis-cli

# ===========================================
# КОМАНДЫ ДЛЯ ПРОДАКШЕНА
# ===========================================

prod-up: ## Запустить все сервисы для продакшена
	@echo "$(GREEN)Запуск продакшн сервисов...$(NC)"
	docker compose --profile production up -d --build
	@echo "$(GREEN)Продакшн сервисы запущены!$(NC)"

prod-down: ## Остановить продакшн сервисы
	@echo "$(RED)Остановка продакшн сервисов...$(NC)"
	docker compose --profile production down

prod-logs: ## Посмотреть логи продакшн сервисов
	docker compose --profile production logs -f

prod-restart: ## Перезапустить продакшн сервисы
	@echo "$(YELLOW)Перезапуск продакшн сервисов...$(NC)"
	docker compose --profile production down
	docker compose --profile production up -d --build

# ===========================================
# ОБЩИЕ КОМАНДЫ
# ===========================================

status: ## Показать статус всех контейнеров
	@echo "$(GREEN)Статус контейнеров:$(NC)"
	docker compose ps

clean: ## Очистить все контейнеры и volumes
	@echo "$(RED)Внимание! Это удалит ВСЕ контейнеры и данные!$(NC)"
	@read -p "Вы уверены? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose --profile development --profile production down -v; \
		docker system prune -f; \
		echo "$(GREEN)Очистка завершена!$(NC)"; \
	else \
		echo "$(YELLOW)Отменено.$(NC)"; \
	fi

# Показать справку по умолчанию
default: help 