from src import init_db
from src.models import user # Import models to register them with SQLModel

def create_tables():
    print("Creating tables...")
    init_db()
    print("Tables created.")

if __name__ == "__main__":
    create_tables()
