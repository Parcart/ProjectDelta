import asyncio
import functools
import os
from asyncio import current_task
from typing import Any, Coroutine, TypeVar, Optional, Sequence
import pymysql
from dotenv import load_dotenv
from sqlalchemy import CursorResult, Result, URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, async_scoped_session
from db.Database import Database

T = TypeVar('T')

load_dotenv()


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__call__()
        return cls._instance


def retry_connection(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        attempt = 0
        while True:
            attempt += 1
            try:
                return await func(*args, **kwargs)
            except pymysql.err.OperationalError as e:
                print(f"Ошибка подключения: {e}. Попытка {attempt}")
                await asyncio.sleep(1)

    return wrapper


class DAO(Database, metaclass=Singleton):

    def __init__(self):
        url_object = URL.create(
            drivername=os.getenv("DRIVERNAME"),
            username=os.getenv("DB_LOGIN"),
            password=os.getenv("DB_PASSWORD"),  # plain (unescaped) text
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
        )
        print(url_object.render_as_string())
        self.db_engine = create_async_engine(url_object, pool_recycle=3, pool_pre_ping=True)
        self.Session = async_scoped_session(async_sessionmaker(bind=self.db_engine), current_task)
        super().__init__(self)

    @retry_connection
    async def GetSingle(self, stmt) -> Coroutine[Any, Optional[T], Any]:
        async with self.Session() as sess:
            result = await sess.scalars(stmt)
            return result.first()

    @retry_connection
    async def GetAll(self, stmt) -> Coroutine[Any, Sequence[T], Any]:
        async with self.Session() as sess:
            result = await sess.scalars(stmt)
            return result.all()

    @retry_connection
    async def ExecuteNonQuery(self, stmt) -> Result[Any] | CursorResult[Any]:
        async with self.Session() as sess:
            try:
                result = await sess.execute(stmt)
                await sess.commit()
                return result
            except Exception as e:
                raise e

    @retry_connection
    async def ExecuteListNonQuery(self, db_objects: list):
        async with self.Session() as sess:
            try:
                sess.add_all(db_objects)
                await sess.flush()
                dicts = [(obj.__class__,
                          {column.name: getattr(obj, column.name) for column in obj.__table__.columns})
                         for obj in db_objects]
                new_objects = [obj[0](**obj[1]) for obj in dicts]
                await sess.commit()
                return new_objects
            except Exception as e:
                print(e)
                raise e

    @retry_connection
    async def ExecuteListNonQueryIgnoreObj(self, db_objects: list):
        async with self.Session() as sess:
            try:
                async with sess.begin():
                    sess.add_all(db_objects)
                await sess.commit()
                return True
            except Exception as e:
                print(e)
                await sess.rollback()
                raise e

    @retry_connection
    async def ExecuteListNonQueryIgnore(self, db_objects: list):
        async with self.Session() as sess:
            try:
                for obj in db_objects:
                    await sess.execute(obj)
                await sess.commit()
                return True
            except Exception as e:
                print(e)
                raise e

