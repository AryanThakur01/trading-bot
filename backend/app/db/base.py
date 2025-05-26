from sqlmodel import create_engine, Session
from app.settings import settings

DATABASE_URI = settings.DATABASE_URI

engine = create_engine(DATABASE_URI, echo=True)


def get_session():
    with Session(engine) as session:
        yield session
