from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import yaml

with open("/app/config/storage/storage_conf.yml", "r") as f:
    app_config = yaml.safe_load(f.read())

DATABASE_CONFIG = app_config["datastore"]


# Build the database URL dynamically using the values from the configuration file
db_url = f"mysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['hostname']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['db']}"

# Create the engine using the dynamically generated URL
engine = create_engine(db_url)


def create_tables():
    Base.metadata.create_all(engine)


def drop_tables():
    Base.metadata.drop_all(engine)


def make_session():
    return sessionmaker(bind=engine)()
