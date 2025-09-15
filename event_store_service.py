from fastapi import FastAPI
from collections import defaultdict, deque

MAX_HISTORY_LENGTH = 10

user_history = defaultdict(lambda: deque(maxlen=MAX_HISTORY_LENGTH))

app = FastAPI(title="Event Store Service")

@app.post("/put")
async def put_event(user_id: int, item_id: int):
    """Сохраняет событие (прослушивание трека) для пользователя."""
    user_history[user_id].appendleft(item_id)
    return {"status": "ok", "user_id": user_id, "item_id": item_id}

@app.get("/get/{user_id}")
async def get_history(user_id: int):
    """Возвращает историю последних прослушиваний пользователя."""
    return {"user_id": user_id, "history": list(user_history[user_id])}