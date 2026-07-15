import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import engine
from app.core.migrations import migrate_password_hashes


if __name__ == "__main__":
    migrate_password_hashes(engine, settings.AUTH_LEGACY_USER_DEFAULT_PASSWORD)
    print("password_hash migration completed")
