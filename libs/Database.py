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
                "CREATE TABLE IF NOT EXISTS guild_settings (guild_id bigint NOT NULL PRIMARY KEY, settings_int char(2) NOT NULL, raito_float FLOAT NOT NULL, auto_remove BOOLEAN, manual_remove BOOLEAN)")
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

    @check_connection
    async def add_guild_setting(self, guild_id: int, settings_int: str, raito_float: float, auto_remove: bool, manual_remove: bool):
        async with self.pool.acquire() as con:
            await con.execute("INSERT INTO guild_settings (guild_id, settings_int, raito_float, auto_remove, manual_remove) VALUES ($1, $2, $3, $4, $5)", guild_id, settings_int, raito_float, auto_remove, manual_remove)
            return True

    @check_connection
    async def get_guild_setting(self, guild_id: int):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM guild_settings WHERE guild_id = $1", guild_id)
            if data:
                result = {"AutoRemove": data[0].get("auto_remove"), "ManualRemove": data[0].get("manual_remove"), "Value":data[0].get("settings_int"), "Ratio": data[0].get("raito_float")}
                return result
            else:
                return None

    @check_connection
    async def update_guild_setting(self, guild_id: int, settings_int: str, raito_float: float):
        async with self.pool.acquire() as con:
            auto_remove, manual_remove = list(map(bool, list(map(int, list(settings_int)))))
            await con.execute("UPDATE guild_settings SET settings_int = $2, raito_float = $3, auto_remove = $4, manual_remove = $5 WHERE guild_id = $1", guild_id, settings_int, raito_float, auto_remove, manual_remove)
            return True

    @check_connection
    async def delete_guild_setting(self, guild_id: int):
        async with self.pool.acquire() as con:
            await con.execute("DELETE FROM guild_settings WHERE guild_id = $1", guild_id)
            return True

    @check_connection
    async def get_all_guild_settings(self):
        async with self.pool.acquire() as con:
            data = await con.fetch("SELECT * FROM guild_settings")
            return data


class DebugDatabase(ProductionDatabase):
    async def execute(self, sql):
        logging.info(f"executing sql: {sql}")

    async def fetch(self, sql):
        logging.info(f"fetching by sql: {sql}")

    async def add_guild_setting(self, guild_id: int, settings_int: str, raito_float: float, auto_remove: bool, manual_remove: bool):
        logging.info(f"adding guild setting: {guild_id}, {settings_int}, {raito_float}, {auto_remove}, {manual_remove}")
        return True

    async def get_guild_setting(self, guild_id: int):
        logging.info(f"getting guild setting: {guild_id}")
        return {"AutoRemove": True, "ManualRemove": True, "Value": "11", "Ratio": 0.85}

    async def update_guild_setting(self, guild_id: int, settings_int: str, raito_float: float):
        logging.info(f"updating guild setting: {guild_id}, {settings_int}, {raito_float}")
        return True

    async def delete_guild_setting(self, guild_id: int):
        logging.info(f"deleting guild setting: {guild_id}")
        return True

    async def get_all_guild_settings(self):
        logging.info("getting all guild settings")
        return []


if env.DEBUG == 1:
    Database = DebugDatabase
else:
    Database = ProductionDatabase
