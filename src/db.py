import os
from typing import TypeVar

import dotenv
import msgspec
import supabase
from postgrest._sync.request_builder import SyncRequestBuilder, SyncSelectRequestBuilder, SyncQueryRequestBuilder

dotenv.load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supa = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
s = supa.schema("forms")


T = TypeVar("T")


class Base(msgspec.Struct):
    __schema__ = "forms"

    def __init_subclass__(cls, schema: str = None, **kwargs):
        if schema:
            cls.__schema__ = schema
        return super().__init_subclass__(**kwargs)

    @classmethod
    def table(cls, auth: str = None) -> SyncRequestBuilder:
        stmt = supa.schema(cls.__schema__)
        if auth:
            stmt = stmt.auth(auth)
        return stmt.table(cls.__name__)

    @classmethod
    def from_dict(cls: T, json: dict) -> T:
        return msgspec.convert(json, cls)

    def to_dict(self):
        return {k: v for k, v in msgspec.structs.asdict(self).items() if not k.startswith("_")}

    @classmethod
    def get(cls: T, query: SyncSelectRequestBuilder) -> list[T]:
        return [cls.from_dict(i) for i in query.execute().data]

    @classmethod
    def get_one(cls: T, query: SyncQueryRequestBuilder) -> T:
        return cls.from_dict(query.execute().data[0])

    @classmethod
    def select(cls, auth: str = None, select: str = "*") -> SyncSelectRequestBuilder:
        return cls.table(auth).select(select)
