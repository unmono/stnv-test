import sqlite3

import pytest
from pathlib import Path
from argon2 import PasswordHasher

from ..settings import Settings, get_settings
from ..main import app


test_user_data = {
    'username': 'test@user.db',
    'password': '12345678Aa!',
}


test_dir = Path(__file__).parent
db_path = test_dir / 'test_db.sqlite'
init_script = test_dir.parent / '../init.sql'
test_data = test_dir / 'test_data.sql'


test_settings = Settings(
    sql_init=init_script,
    db_path=db_path,
    google_key='',
    secret_key="test-secret-key",
)


@pytest.fixture(scope="session")
def initialize_db():
    conn = sqlite3.connect(db_path)
    with open(init_script, 'r') as script:
        conn.executescript(script.read())
    conn.commit()
    conn.close()


@pytest.fixture(scope="session")
def fill_db_with_data(initialize_db):
    ph = PasswordHasher()
    test_user_data['hash'] = ph.hash(test_user_data['password'])
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO users(email, hash) "
        "VALUES (:username, :hash);",
        test_user_data
    )
    conn.execute(
        "INSERT INTO posts(author_id, title, body) "
        "VALUES "
        "   (1, 'Post from author 1', 'Body of post 1 from author 1. Test User 1, Test Post 1'),"
        "   (1, 'Post from author 1', 'Body of post 2 from author 1. Test User 1, Test Post 2'),"
        "   (1, 'Post from author 1', 'Body of post 3 from author 1. Test User 1, Test Post 3'),"
        "   (2, 'Post from some other author', 'Body of post 4. Some other author');"
    )
    conn.execute(
        "INSERT INTO comments(author_id, post_id, body) "
        "VALUES "
        "   (1, 1, 'Body of comment 1 from author 1 to post 1.'),"
        "   (1, 1, 'Body of comment 2 from author 1 to post 1.'),"
        "   (1, 2, 'Body of comment 3 from author 1 to post 2.'),"
        "   (2, 2, 'Body of comment 4 from some other author.');"
    )
    conn.commit()
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def override_settings(fill_db_with_data):
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    db_path.unlink()
    app.dependency_overrides.pop(get_settings)


@pytest.fixture
def plain_sql_connection():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    yield cursor
    cursor.close()
    conn.close()
