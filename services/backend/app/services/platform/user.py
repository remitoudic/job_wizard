from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from database_pkg.models.user import User, UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

class UserService:
    def get_by_email(self, session: Session, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()
    


    def authenticate(self, session: Session, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(session, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def update_last_login(self, session: Session, db_user: User) -> User:
        db_user.last_login = datetime.utcnow()
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    def create(self, session: Session, user_create: UserCreate) -> User:
        db_obj = User.model_validate(
            user_create, 
            update={"hashed_password": get_password_hash(user_create.password)}
        )
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def update(self, session: Session, db_user: User, user_in: UserUpdate) -> User:
        user_data = user_in.model_dump(exclude_unset=True)
        if "password" in user_data and user_data["password"]:
            hashed_password = get_password_hash(user_data["password"])
            del user_data["password"]
            user_data["hashed_password"] = hashed_password
        
        db_user.sqlmodel_update(user_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

user_service = UserService()
