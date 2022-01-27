from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.POSTGRES_DATABASE_URI, echo=True, future=True)

AsyncSessionLocal = sessionmaker(class_=AsyncSession, future=True, expire_on_commit=False,
                                 autocommit=False, autoflush=False, bind=engine)
