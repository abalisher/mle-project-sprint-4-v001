# recommendations_service.py
import pandas as pd
from fastapi import FastAPI
from contextlib import asynccontextmanager
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# --- Конфигурация ---
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
OFFLINE_RECS_PATH = f's3://{S3_BUCKET_NAME}/recsys/recommendations/recommendations.parquet'
TOP_POPULAR_PATH = f's3://{S3_BUCKET_NAME}/recsys/recommendations/top_popular.parquet'

EVENT_STORE_URL = "http://127.0.0.1:8001"
SIMILAR_ITEMS_URL = "http://127.0.0.1:8002"

offline_recs = None
top_popular_recs = None

# --- Загрузка моделей при старте ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global offline_recs, top_popular_recs
    print("Загрузка офлайн-рекомендаций...")
    storage_options = {
        "key": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "client_kwargs": {'endpoint_url': "https://storage.yandexcloud.net"}
    }
    offline_recs_df = pd.read_parquet(OFFLINE_RECS_PATH, storage_options=storage_options)
    offline_recs = offline_recs_df.groupby('user_id')['item_id'].apply(list).to_dict()
    
    top_popular_recs = pd.read_parquet(TOP_POPULAR_PATH, storage_options=storage_options)['item_id'].tolist()
    
    print("Рекомендации успешно загружены.")
    yield
    print("Сервис останавливается.")


app = FastAPI(title="Recommendations Service", lifespan=lifespan)

# --- Логика смешивания ---
def blend_recommendations(online_recs, offline_recs, k):
    """
    Стратегия смешивания: чередование онлайн и офлайн рекомендаций.
    Онлайн-рекомендации получают приоритет и занимают нечетные места.
    """
    blended = []
    online_idx, offline_idx = 0, 0
    
    # Удаляем дубликаты из офлайн-рекомендаций, чтобы не повторяться
    offline_recs_unique = [item for item in offline_recs if item not in online_recs]
    
    while len(blended) < k:
        # Добавляем онлайн-рекомендацию (нечетные места)
        if online_idx < len(online_recs):
            blended.append(online_recs[online_idx])
            online_idx += 1
        
        # Добавляем офлайн-рекомендацию (четные места)
        if len(blended) < k and offline_idx < len(offline_recs_unique):
            blended.append(offline_recs_unique[offline_idx])
            offline_idx += 1
            
        # Если один из списков закончился, выходим из цикла
        if online_idx >= len(online_recs) and offline_idx >= len(offline_recs_unique):
            break
            
    return blended[:k]


@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int, k: int = 10):
    # 1. Получаем офлайн-рекомендации
    user_offline_recs = offline_recs.get(user_id, top_popular_recs)
    
    # 2. Получаем онлайн-историю пользователя
    try:
        response = requests.get(f"{EVENT_STORE_URL}/get/{user_id}")
        response.raise_for_status()
        user_history = response.json().get("history", [])
    except requests.RequestException:
        user_history = []
        
    # 3. Если истории нет, возвращаем только офлайн-рекомендации
    if not user_history:
        return {"user_id": user_id, "recommendations": user_offline_recs[:k]}
        
    # 4. Генерируем онлайн-рекомендации
    online_recs = []
    for item_id in user_history:
        try:
            response = requests.get(f"{SIMILAR_ITEMS_URL}/similar/{item_id}?k=5")
            response.raise_for_status()
            similar = response.json().get("similar_items", [])
            online_recs.extend(similar)
        except requests.RequestException:
            continue
    
    # Удаляем дубликаты и уже прослушанные треки
    online_recs = [item for item in online_recs if item not in user_history]
    online_recs = list(dict.fromkeys(online_recs)) # Сохраняем порядок
    
    # 5. Смешиваем рекомендации
    final_recs = blend_recommendations(online_recs, user_offline_recs, k)
    
    return {"user_id": user_id, "recommendations": final_recs}