# Django REST Framework Project: CI/CD и Docker

Проект представляет собой API на базе Django REST Framework (DRF), полностью контейнеризированный и готовый к автоматическому развертыванию (CI/CD) через GitHub Actions на виртуальную машину Yandex Cloud.

## Стек технологий
* Backend: Python, Django, DRF
* Database: PostgreSQL
* Redis, Celery
* Nginx
* Docker, Docker Compose, GitHub Actions

---

## Быстрый старт (Локальный запуск)

Вся инфраструктура проекта запускается одной командой. Вам понадобятся только установленные Docker и Docker Compose.

### 1. Клонирование репозитория
```bash
git clone https://github.com/gdeunas/docker_project.git
cd ваш-репозиторий
```

### 2. Настройка окружения
Создайте файл .env в корневом каталоге проекта и заполните его по шаблону:
```bash
# Django настройки
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Настройки базы данных PostgreSQL
POSTGRES_DB=django_db
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Настройки Celery и Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3. Запуск проекта одной командой
```bash
docker compose up --build -d
```
Docker Compose автоматически соберет и запустит контейнеры для:
* web (Django / DRF)
* db (PostgreSQL)
* redis (Брокер сообщений)
* celery (Воркер для фоновых задач)
* nginx (Веб-сервер)

Приложение будет доступно локально по адресу: http://localhost/

---

## Настройка удаленного сервера (Yandex Cloud)

Внимание (экономия баланса): Чтобы не израсходовать стартовый грант в 1000 рублей, запускайте виртуальную машину Yandex Cloud только на время выполнения и проверки задания наставником!

### 1. Подготовка ВМ
1. Создайте ВМ в консоли Yandex Cloud (рекомендуется ОС Ubuntu 22.04 LTS).
2. Подключитесь к ней по SSH: ssh ubuntu@<IP_ВМ>.
3. Установите Docker и Docker Compose:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   sudo systemctl enable --now docker
   ```

### 2. Подготовка директории и окружения
На сервере создайте рабочую директорию /home/ubuntu/app/ и добавьте туда рабочий файл .env (с DEBUG=False и актуальными продакшн-паролями).

---

## Настройка CI/CD через GitHub Actions

При каждом пуше или слиянии (Pull Request) в ветку main запускается автоматический пайплайн проверки и деплоя.

### Шаг 1: Настройка SSH-доступа для GitHub
1. Локально сгенерируйте SSH-ключи:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions"
   ```
2. Публичный ключ (.pub) добавьте на сервере Yandex Cloud в файл ~/.ssh/authorized_keys.
3. Приватный ключ скопируйте для GitHub.

### Шаг 2: Добавление секретов в GitHub
В репозитории перейдите в Settings -> Secrets and variables -> Actions -> New repository secret и добавьте:

* SSH_HOST — Публичный IP-адрес вашей ВМ в Yandex Cloud.
* SSH_USER — Имя пользователя сервера (по умолчанию ubuntu).
* SSH_KEY — Полный текст приватного SSH-ключа (начиная с -----BEGIN RSA PRIVATE KEY-----).

---

## Конфигурация GitHub Actions (.github/workflows/deploy.yml)

В репозиторий добавлен файл пайплайна, выполняющий следующие шаги:
1. Линтинг и Тестирование: Проверка кода (flake8/black) и запуск unit-тестов Django.
2. Проверка сборки: Тестовая сборка Docker-образов для контроля целостности Dockerfile.
3. Автоматический деплой: При успешных тестах подключается по SSH к Yandex Cloud, стягивает изменения (git pull) и перезапускает проект через Docker Compose.

```yaml
name: Django CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install flake8 pytest
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: Run Linters
        run: flake8 .
      - name: Run Tests
        run: python manage.py test

  build-check:
    needs: lint-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test Docker Build
        run: docker compose build

  deploy:
    needs: build-check
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Yandex Cloud via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: \${{ secrets.SSH_HOST }}
          username: \${{ secrets.SSH_USER }}
          key: \${{ secrets.SSH_KEY }}
          script: |
            cd /home/ubuntu/app
            git pull origin main
            docker compose down
            docker compose up --build -d
            docker compose exec -T web python manage.py migrate
            docker compose exec -T web python manage.py collectstatic --no-input
```

---

## Полезные Docker-команды для работы

* Посмотреть статус контейнеров: docker compose ps
* Просмотр логов (онлайн): docker compose logs -f
* Остановка всех сервисов: docker compose down
* Выполнение миграций вручную: docker compose exec web python manage.py migrate
* Создание суперпользователя: docker compose exec web python manage.py createsuperuser
