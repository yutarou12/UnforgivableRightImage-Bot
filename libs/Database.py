import logging
from functools import wraps

import asyncpg

import libs.env as env


class ProductionDatabase:
    def __init__(self):
        self.pool = None

    async def setup(self):
        self.pool = await asyncpg.create_pool(f"postgresql://{env.POSTGRESQL_USER}:{env.POSTGRESQL_PASSWORD}@{env.POSTGRESQL_HOST_NAME}:{env.POSTGRESQL_PORT}/{env.POSTGRESQL_DATABASE_NAME}")

        async with self.pool.acquire() as conn:
            await conn.execute(
                "CREATE TABLE IF NOT EXISTS guild_settings (user_id bigint NOT NULL PRIMARY KEY, uid char(10) NOT NULL)")

        return self.pool

    def check_connection(func):
        @wraps(func)
        async def inner(self, *args, **kwargs):
            self.pool = self.pool or await self.setup()
            return await func(self, *args, **kwargs)

        return inner

    @check_connection
    async def execute(self, sql):
        async with self.pool.acquire() as con:
            await con.execute(sql)

    @check_connection
    async def fetch(self, sql):
        async with self.pool.acquire() as con:
            data = await con.fetch(sql)
        return data


class DebugDatabase(ProductionDatabase):
    async def execute(self, sql):
        logging.info(f"executing sql: {sql}")

    async def fetch(self, sql):
        (logging.info(f"fetching by sql: {sql}"))


if env.DEBUG == 1:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
