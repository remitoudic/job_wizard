from sqlmodel import SQLModel, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jobwizard:jobwizard123@postgres:5432/jobwizard")

engine = create_engine(DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)
