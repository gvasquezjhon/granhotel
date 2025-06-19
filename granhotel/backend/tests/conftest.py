import pytest
from typing import Generator, Any
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from alembic.config import Config
from alembic import command
import os

# Import settings and base model from the app
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app as main_app # Import the main FastAPI app

# Use a separate test database
# Ensure alembic.ini is found relative to the backend directory
# The script is run from /app, so paths in alembic_cfg need to be correct
# or alembic.ini needs to be specified with its full path from /app
ALEMBIC_INI_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
# __file__ for conftest.py is /app/granhotel/backend/tests/conftest.py
# os.path.dirname(__file__) is /app/granhotel/backend/tests
# os.path.dirname(os.path.dirname(__file__)) is /app/granhotel/backend

TEST_DATABASE_URL = settings.DATABASE_URL.replace("db/granhoteldb", "db/granhoteldb_test") if "db/granhoteldb" in settings.DATABASE_URL else settings.DATABASE_URL + "_test"


engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    # Run Alembic migrations
    alembic_cfg = Config(ALEMBIC_INI_PATH) # Assumes alembic.ini is in backend/
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    # Create the test database if it doesn't exist (PostgreSQL specific)
    # This is a simplified approach; robust solutions might involve docker-entrypoint scripts
    # or specific database management commands. For now, we assume the DB service is up
    # and we just need to ensure the granhoteldb_test database exists within it.
    # This part is tricky as create_engine doesn't create the DB itself.
    # For tests, often the database server is configured to allow user to create DBs,
    # or the DB is pre-created by CI/Docker setup.
    # Let's assume for now the DB server allows creation or it's pre-created.
    # SQLAlchemy itself cannot create a database, only tables.

    # For SQLite, the file would be created automatically. For PostgreSQL, the DB must exist.
    # A common pattern is to connect to a default 'postgres' db and issue 'CREATE DATABASE'
    # This is complex to do here cleanly. We'll rely on the DB being available or
    # the user having created it for now.

    # Before running migrations, ensure all tables are dropped (optional, for cleaner state)
    # Base.metadata.drop_all(bind=engine) # This can be problematic if migrations are not perfectly in sync

    command.upgrade(alembic_cfg, "head")
    yield
    # Optional: Downgrade migrations after tests
    # command.downgrade(alembic_cfg, "base")
    # For a truly clean state, dropping the database or all tables is better
    Base.metadata.drop_all(bind=engine) # Drop all tables after tests run


@pytest.fixture(scope="session")
def db_engine():
    # The engine is already created above, migrations applied by autouse fixture
    yield engine
    # engine.dispose() # Clean up engine connections if necessary

@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, Any, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    # Use a regular Session for tests, not TestingSessionLocal directly with bind
    # This ensures it uses the connection and transaction correctly.
    db_session = Session(bind=connection)
    # db_session = TestingSessionLocal(bind=connection) # This should also work

    yield db_session

    db_session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, Any, None]:
    # Dependency override for get_db
    def override_get_db():
        # The db fixture already provides a session that is transaction-managed
        yield db

    main_app.dependency_overrides[get_db] = override_get_db
    with TestClient(main_app) as c:
        yield c
    del main_app.dependency_overrides[get_db] # Clean up override
