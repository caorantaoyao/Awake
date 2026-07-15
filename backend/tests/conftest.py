import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试环境隔离外部服务：不打真实 SMTP，不连本地 DeerFlow（走 mock 苏格拉底逻辑）。
# 必须在导入 main（触发 settings 实例化）之前设置；环境变量优先级高于 .env。
os.environ["SMTP_ENABLED"] = "false"
os.environ["DEERFLOW_ENABLED"] = "false"

from app.core.database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test_awaken.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
