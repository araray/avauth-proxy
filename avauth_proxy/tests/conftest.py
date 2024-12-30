import pytest
import subprocess

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # For in-memory or ephemeral DB:
    # 1) Create the database connection
    # 2) Run `alembic upgrade head` against that DB
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    yield
    # teardown if needed
