from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database import async_session, News, select, func
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    async with async_session() as session:
        total_news = await session.scalar(select(func.count(News.id)))
        triggered_news = await session.scalar(select(func.count(News.id)).where(News.triggered == True))
        published_news = triggered_news  # для простоты считаем, что все триггерные опубликованы
    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_news": total_news,
        "triggered_news": triggered_news,
        "published_news": published_news
    })
