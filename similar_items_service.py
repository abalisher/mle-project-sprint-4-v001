import pandas as pd
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
SIMILAR_ITEMS_PATH = f's3://{S3_BUCKET_NAME}/recsys/recommendations/similar.parquet'

similar_items_df = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global similar_items_df
    print("Загрузка данных о похожих треках...")
    storage_options = {
        "key": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "client_kwargs": {'endpoint_url': "https://storage.yandexcloud.net"}
    }
    similar_items_df = pd.read_parquet(SIMILAR_ITEMS_PATH, storage_options=storage_options)
    # Группируем для быстрого доступа
    similar_items_df = similar_items_df.groupby('item_id_1')['item_id_2'].apply(list).to_dict()
    print("Данные успешно загружены.")
    yield
    print("Сервис останавливается.")


app = FastAPI(title="Similar Items Service", lifespan=lifespan)

@app.get("/similar/{item_id}")
async def get_similar_items(item_id: int, k: int = 10):
    """Возвращает k похожих треков для заданного item_id."""
    similar = similar_items_df.get(item_id, [])
    return {"item_id": item_id, "similar_items": similar[:k]}