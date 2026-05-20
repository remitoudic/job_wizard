import sys
from sqlmodel import Session, select
from passlib.context import CryptContext
from database_pkg import engine
from database_pkg.create_tables import create_tables
from database_pkg.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_superuser():
    print("Creating superuser...")
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == "remitoudic@gmail.com")
        ).first()
        if not user:
            user = User(
                email="remitoudic@gmail.com",
                full_name="Remi Toudic",
                hashed_password=get_password_hash("remitoudic"),
                is_superuser=True,
                job_title="System Administrator",
            )
            session.add(user)
            session.commit()
            print("Superuser user created.")
        else:
            print("Superuser already exists.")


def main():
    args = sys.argv[1:]

    if "--tables-only" in args:
        create_tables()
    else:
        create_tables()
        create_superuser()


if __name__ == "__main__":
    main()
