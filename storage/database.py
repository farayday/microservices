import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from models import Base
import yaml
from dotenv import load_dotenv
import os

CONFIG_DIR = os.getenv("CONFIG_DIR", "/app/config/dev")
CONFIG_FILE = os.path.join(CONFIG_DIR, "storage_conf.yml")

with open(CONFIG_FILE, "r") as f:
    app_config = yaml.safe_load(f.read())

DATABASE_CONFIG = app_config["datastore"]

user = os.getenv("MYSQL_USER", "default_user")
password = os.getenv("MYSQL_PASSWORD", "default_password")
db = os.getenv("MYSQL_DATABASE", "default_db")

db_url = (
    f"mysql://{user}:{password}@"
    f"{DATABASE_CONFIG['hostname']}:{DATABASE_CONFIG['port']}/{db}"
)

# Create the engine using the dynamically generated URL
engine = create_engine(db_url)


def create_tables():
    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(engine)
            print(f"Successfully created database tables after {attempt+1} attempts")
            return
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(
                    f"Database connection failed: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})"
                )
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")
                raise


def drop_tables():
    Base.metadata.drop_all(engine)


def make_session():
    return sessionmaker(bind=engine)()
