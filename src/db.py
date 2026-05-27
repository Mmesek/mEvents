import os
from typing import Annotated, TypeVar, get_type_hints

import dotenv
import msgspec
import supabase
from postgrest._sync.request_builder import SyncRequestBuilder, SyncSelectRequestBuilder, SyncQueryRequestBuilder

dotenv.load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supa = supabase.create_client(SUPABASE_URL, SUPABASE_KEY, options=supabase.ClientOptions(auto_refresh_token=False))
s = supa.schema("forms")


T = TypeVar("T")
NotSerializable = Annotated[T, "not_serializable"]


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
        return {
            k: v
            for k, v in msgspec.structs.asdict(self).items()
            if not k.startswith("_")
            and getattr(get_type_hints(self.__class__, include_extras=True)[k], "__metadata__", [()])[0]
            != "not_serializable"
            and v
        }

    @classmethod
    def get(cls: T, query: SyncSelectRequestBuilder) -> list[T]:
        return [cls.from_dict(i) for i in query.execute().data]

    @classmethod
    def get_one(cls: T, query: SyncQueryRequestBuilder) -> T:
        return cls.from_dict(query.execute().data[0])

    @classmethod
    def maybe_one(cls: T, query: SyncSelectRequestBuilder) -> T | None:
        if data := query.maybe_single().execute():
            return cls.from_dict(data.data)

    @classmethod
    def select(cls, auth: str = None, select: str = "*") -> SyncSelectRequestBuilder:
        return cls.table(auth).select(select)

    def insert(self, auth: str = None):
        return self.table(auth).insert(self.to_dict()).execute().data

    def update(self, auth: str = None):
        return self.table(auth).update(self.to_dict()).execute().data

    def upsert(self, auth: str = None):
        return self.table(auth).upsert(self.to_dict()).execute().data

    def delete(self, auth: str = None):
        return self.table(auth).delete().execute().data
