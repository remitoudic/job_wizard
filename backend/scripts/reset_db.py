
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from sqlmodel import Session, select, SQLModel, text
from app.core.db import engine
# Import from the installed package 'src' instead of local 'database' path
from src.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_superuser_local():
    print("Creating superuser...")
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "remitoudic@gmail.com")).first()
        if not user:
            user = User(
                email="remitoudic@gmail.com",
                first_name="Remi",
                surname="Toudic",
                username="remitoudic",
                hashed_password=get_password_hash("remitoudic"),
                is_superuser=True,
                job_title="System Administrator"
            )
            session.add(user)
            session.commit()
            print("Superuser user created.")
        else:
            print("Superuser already exists.")

def reset_db():
    print("Dropping all tables using CASCADE...")
    with Session(engine) as session:
        # Drop all tables with CASCADE to handle circular dependencies
        session.exec(text("DROP SCHEMA public CASCADE;"))
        session.exec(text("CREATE SCHEMA public;"))
        session.exec(text("GRANT ALL ON SCHEMA public TO public;"))
        session.commit()
    print("Tables dropped.")
    
    print("Creating all tables...")
    SQLModel.metadata.create_all(engine)
    print("Tables created.")
    
    print("Seeding data...")
    try:
        create_superuser_local()
        print("Seeding complete.")
    except Exception as e:
        print(f"Error seeding data: {e}")

if __name__ == "__main__":
    reset_db()
