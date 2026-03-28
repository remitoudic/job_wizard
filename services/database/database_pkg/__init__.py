from sqlmodel import SQLModel, create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jobwizard:jobwizard123@postgres:5432/jobwizard")

engine = create_engine(DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)
    try:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN profile_picture_url VARCHAR;'))
    except Exception:
        pass

