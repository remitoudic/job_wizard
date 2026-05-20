from database_pkg import init_db


def create_tables():
    print("Creating tables...")
    init_db()
    print("Tables created.")


if __name__ == "__main__":
    create_tables()
