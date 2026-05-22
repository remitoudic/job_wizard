from sqlmodel import create_engine, text

engine = create_engine("sqlite:///test.db")
with engine.connect() as conn:
    try:
        conn.execute(
            text("ALTER TABLE user ADD COLUMN preferred_language VARCHAR DEFAULT 'en'")
        )
        conn.commit()
        print("Column added successfully to SQLite DB.")
    except Exception as e:
        print(f"Error adding column to SQLite: {e}")

try:
    # Also attempt for Postgres if running locally
    pg_engine = create_engine(
        "postgresql://postgres:postgres@localhost:5432/job_wizard"
    )
    with pg_engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE \"user\" ADD COLUMN preferred_language VARCHAR DEFAULT 'en'"
            )
        )
        conn.commit()
        print("Column added successfully to Postgres DB.")
except Exception as e:
    print(f"Could not add to postgres: {e}")
