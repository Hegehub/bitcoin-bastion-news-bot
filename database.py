# В файле database.py добавить в модель News:
class News(Base):
    # ... существующие поля ...
    triggered = Column(Boolean, default=False)
    price_change = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
