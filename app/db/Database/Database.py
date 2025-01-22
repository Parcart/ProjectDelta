import asyncio
import inspect
import os
from pathlib import Path
from urllib.parse import quote_plus

from alembic import command, context
from alembic.autogenerate import compare_metadata
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

import alembic.config
from sqlalchemy import URL, engine_from_config, pool, create_engine, Connection

from .DatabaseAdmin import DatabaseAdmin
from .DatabaseConfirm import DatabaseConfirm
from .DatabaseMessage import DatabaseMessage
from .DatabaseTransaction import DatabaseTransaction
from .DatabaseUser import DatabaseUser
from .DatabaseUserSession import DatabaseUserSession
from ..schema import Base


class Database:
    def __init__(self, instance, url_object: URL):
        self.instance = instance
        self.User = DatabaseUser(instance)
        self.UserSession = DatabaseUserSession(instance)
        self.Transaction = DatabaseTransaction(instance)
        self.Confirm = DatabaseConfirm(instance)
        self.Admin = DatabaseAdmin(instance)
        self.Message = DatabaseMessage(instance)
        # self.UserProfile = DatabaseUserProfile(instance)

    async def checkDatabase(self):
        class_path = inspect.getfile(self.__class__)
        print("Class path:", class_path)
        # Получаем директорию, убирая имя файла
        directory_path = Path(class_path).parent
        # Формируем полный путь к конфигурационному файлу
        config_path = directory_path / 'alembic.ini'
        alembic_config = alembic.config.Config(config_path)
        script = ScriptDirectory.from_config(alembic_config)
        env_context = EnvironmentContext(
            alembic_config,
            script,
            as_sql=False,
        )

        async with self.instance.db_engine.connect() as conn:
            def get_diff(connection):
                env_context.configure(connection=connection, target_metadata=Base.metadata)
                return compare_metadata(env_context.get_context(), Base.metadata)

            diff = await conn.run_sync(get_diff)

        def diff_action():
            def run_auto_migration():
                try:
                    command.revision(alembic_config, autogenerate=True)
                    command.upgrade(alembic_config, 'head')
                except Exception as e:
                    raise e

            if diff:
                run_auto_migration()

        diff_action()
