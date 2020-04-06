import glob
import os
from logging.config import fileConfig
from enum import Enum

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from configparser import ConfigParser, ExtendedInterpolation


def generate_db_uri():
    return 'mysql://' + CONFIG.get('rds-aurora-mysql-opendemic-username') + ':' + \
           CONFIG.get('rds-aurora-mysql-opendemic-password') + '@' + \
           CONFIG.get('rds-aurora-mysql-opendemic-host') + ':' + \
           CONFIG.get('rds-aurora-mysql-opendemic-port') + '/' + \
           CONFIG.get('rds-aurora-mysql-opendemic-database')


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config_parser = ConfigParser(interpolation=ExtendedInterpolation())

# read .ini files
file_paths = glob.glob('./config/*.ini')
config_parser.read(filenames=file_paths)


# create environment Enum class


class Environments(Enum):
    DEFAULT = 'DEFAULT'
    DEVELOPMENT = 'DEVELOPMENT'
    PRODUCTION = 'PRODUCTION'


# get current environment
try:
    global ENV
    ENV = os.environ['FLASK_ENV'].upper()
    assert ENV in [i.name for i in list(Environments)]
except KeyError as e:
    raise KeyError("Unable to find `FLASK_ENV` environment variable.")

try:
    global LOCAL
    LOCAL = bool(int(os.environ['LOCAL']))
except KeyError as e:
    raise KeyError("Unable to find `LOCAL` environment variable.")

global CONFIG
CONFIG = config_parser[ENV]

config.set_main_option('sqlalchemy.url', generate_db_uri())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
