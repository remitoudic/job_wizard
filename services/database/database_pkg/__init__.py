from sqlmodel import SQLModel, create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jobwizard:jobwizard007@postgres:5432/jobwizard")

engine = create_engine(DATABASE_URL)

def init_db():
    # Import all models so SQLModel registers them before create_all
    from database_pkg.models.user import User  # noqa: F401
    from database_pkg.models.user_cv import UserCV  # noqa: F401
    from database_pkg.models.job_status import JobStatus  # noqa: F401
    from database_pkg.models.status_history import ApplicationStatusHistory  # noqa: F401

    SQLModel.metadata.create_all(engine)
    try:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN profile_picture_url VARCHAR;'))
    except Exception:
        pass

    try:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE "applications" ADD COLUMN notes TEXT;'))
    except Exception:
        pass


