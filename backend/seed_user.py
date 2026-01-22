import sys
from sqlmodel import Session, create_engine, select, SQLModel
from app.core.security import get_password_hash
from src.models.user import User

# Connect to exposed port 5434 on localhost
# DB Credentials from .env
DATABASE_URL = "postgresql://jobwizard:jobwizard123@localhost:5434/jobwizard"

def check_and_create():
    try:
        engine = create_engine(DATABASE_URL)
        # Ensure we can connect
        with engine.connect() as conn:
            print("Connected to database successfully.")
        
        with Session(engine) as session:
            email = "remitoudic@gmail.com"
            password = "remitoudic"
            
            # Check if user exists
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()
            
            if user:
                print(f"User {email} already exists.")
                # Optional: Update password to be sure
                # user.hashed_password = get_password_hash(password)
                # session.add(user)
                # session.commit()
                # print("Password updated.")
            else:
                print(f"User {email} not found. Creating...")
                new_user = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    full_name="Remi Toudic",
                    is_superuser=True 
                )
                session.add(new_user)
                session.commit()
                print(f"User {email} created successfully.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_and_create()
