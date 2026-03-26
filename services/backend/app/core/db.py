from sqlmodel import Session
from src import engine

# Re-export or just use them
def get_session():
    with Session(engine) as session:
        yield session

# init_db is imported directly now
