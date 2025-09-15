# test_service.py
import requests
import time
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# --- URLs сервисов ---
REC_SERVICE_URL = "http://127.0.0.1:8000"
EVENT_STORE_URL = "http://127.0.0.1:8001"

# --- Данные для тестов ---
# Пользователь С персональными рекомендациями
storage_options = {
    "key": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "client_kwargs": {'endpoint_url': "https://storage.yandexcloud.net"}
}
OFFLINE_RECS_PATH = f's3://{S3_BUCKET_NAME}/recsys/recommendations/recommendations.parquet'
df = pd.read_parquet(OFFLINE_RECS_PATH, storage_options=storage_options)
USER_WITH_RECS = df['user_id'].iloc[0]

# Пользователь БЕЗ персональных рекомендаций
# Вычисляем ID пользователя, которого нет в данных
# Находим максимальный ID в датафрейме и добавляем 1
USER_WITHOUT_RECS = df['user_id'].max() + 1

# Треки для добавления в историю
TEST_TRACKS = [df['item_id'].iloc[0], df['item_id'].iloc[1]]

def test_endpoint(description, user_id):
    print(f"--- {description} ---")
    try:
        response = requests.get(f"{REC_SERVICE_URL}/recommendations/{user_id}")
        response.raise_for_status()
        print(f"Статус: {response.status_code}")
        print("Ответ:", response.json())
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
    print("-" * 25 + "\n")

def add_event(user_id, item_id):
    print(f"Добавляем событие: пользователь {user_id}, трек {item_id}")
    try:
        requests.post(f"{EVENT_STORE_URL}/put", params={"user_id": user_id, "item_id": item_id})
    except requests.RequestException as e:
        print(f"Ошибка при добавлении события: {e}")

if __name__ == "__main__":
    print("Начало тестирования сервиса рекомендаций...\n")
    
    # Сценарий 1: Пользователь без персональных рекомендаций
    test_endpoint("Сценарий 1: Пользователь без персональных рек-й (ожидаем топ популярных)", USER_WITHOUT_RECS)
    
    # Сценарий 2: Пользователь с персональными рек-ми, но без онлайн-истории
    test_endpoint(f"Сценарий 2: Пользователь {USER_WITH_RECS} с офлайн-реками, без онлайн-истории", USER_WITH_RECS)

    # Сценарий 3: Пользователь с персональными рек-ми и онлайн-историей
    print(f"--- Сценарий 3: Пользователь {USER_WITH_RECS} с офлайн-реками и онлайн-историей ---")
    # Добавляем события в историю
    add_event(USER_WITH_RECS, TEST_TRACKS[0])
    time.sleep(0.5) # Небольшая пауза
    add_event(USER_WITH_RECS, TEST_TRACKS[1])
    print("\nЗапрашиваем смешанные рекомендации...")
    test_endpoint(f"Результат для пользователя {USER_WITH_RECS} после добавления событий", USER_WITH_RECS)

    print("Тестирование завершено.")