from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, BigInteger, ForeignKey, Text
from datetime import datetime
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    subscribed_whales = Column(Boolean, default=False)
    subscribed_liquidations = Column(Boolean, default=False)
    subscribed_high_sentiment = Column(Boolean, default=False)  # новости с высокой тональностью (>0.8)
    created_at = Column(DateTime, default=datetime.utcnow)

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String, unique=True, index=True)
    source = Column(String)
    published_at = Column(DateTime)
    sentiment_label = Column(String)   # positive/negative/neutral
    sentiment_score = Column(Float)
    btc_price_at_publish = Column(Float, nullable=True)
    btc_price_1h_later = Column(Float, nullable=True)
    btc_price_6h_later = Column(Float, nullable=True)
    btc_price_24h_later = Column(Float, nullable=True)
    price_change_1h = Column(Float, nullable=True)   # в процентах
    price_change_6h = Column(Float, nullable=True)
    price_change_24h = Column(Float, nullable=True)
    market_trend = Column(String)      # positive/negative/neutral based on 1h change
    matched = Column(Boolean, default=False)  # совпала ли с реакцией (1h)
    published_in_channel = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
