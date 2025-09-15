# Подготовка виртуальной машины

## Склонируйте репозиторий

Склонируйте репозиторий проекта:

```
git clone https://github.com/yandex-praktikum/mle-project-sprint-4-v001.git
```

## Активируйте виртуальное окружение

Используйте то же самое виртуальное окружение, что и созданное для работы с уроками. Если его не существует, то его следует создать.

Создать новое виртуальное окружение можно командой:

```
python3 -m venv env_recsys_start
```

После его инициализации следующей командой

```
. env_recsys_start/bin/activate
```

установите в него необходимые Python-пакеты следующей командой

```
pip install -r requirements.txt
```

### Скачайте файлы с данными

Для начала работы понадобится три файла с данными:
- [tracks.parquet](https://storage.yandexcloud.net/mle-data/ym/tracks.parquet)
- [catalog_names.parquet](https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet)
- [interactions.parquet](https://storage.yandexcloud.net/mle-data/ym/interactions.parquet)
 
Скачайте их в директорию локального репозитория. Для удобства вы можете воспользоваться командой wget:

```
wget https://storage.yandexcloud.net/mle-data/ym/tracks.parquet

wget https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet

wget https://storage.yandexcloud.net/mle-data/ym/interactions.parquet
```

## Запустите Jupyter Lab

Запустите Jupyter Lab в командной строке

```
jupyter lab --ip=0.0.0.0 --no-browser
```

# Расчёт рекомендаций

Код для выполнения первой части проекта находится в файле `recommendations.ipynb`. Изначально, это шаблон. Используйте его для выполнения первой части проекта.

# Сервис рекомендаций
Создайте файл `.env` в корне проекта и укажите в нем ваши креды для S3:
```
S3_BUCKET_NAME="<имя-вашего-бакета>"
AWS_ACCESS_KEY_ID="<ваш-ключ>"
AWS_SECRET_ACCESS_KEY="<ваш-секретный-ключ>"
```

Сервис построен на основе микросервисной архитектуры и включает в себя:
- **Основной сервис рекомендаций (`recommendations_service.py`):** Принимает запросы, смешивает и отдает рекомендации.
- **Сервис событий (`event_store_service.py`):** Хранит в памяти недавнюю историю прослушиваний пользователя.
- **Сервис похожих треков (`similar_items_service.py`):** По ID трека возвращает список похожих, выступая в роли Feature Store для онлайн-рекомендаций.

Откройте три отдельных терминала и запустите в каждом свой сервис:
```bash
# Терминал 1: Event Store
uvicorn event_store_service:app --host 0.0.0.0 --port 8001

# Терминал 2: Similar Items Service
uvicorn similar_items_service:app --host 0.0.0.0 --port 8002

# Терминал 3: Основной сервис рекомендаций
uvicorn recommendations_service:app --host 0.0.0.0 --port 8000
```


# Инструкции для тестирования сервиса

Код для тестирования сервиса находится в файле `test_service.py`.

Откройте четвертый терминал и запустите скрипт для тестирования. Вывод будет сохранен в `test_service.log`.
```bash
python test_service.py > test_service.log 2>&1
```
