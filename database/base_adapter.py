import asyncio
import pickle
from datetime import datetime
from typing import TypeVar, Type, List, Any

from sqlalchemy import select

from ZewSFS.Types import SFSObject, SFSArray, Long
from . import Session, Base, RedisSession

T = TypeVar('T', bound='BaseAdapter')


class BaseAdapterMeta(type):
    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        cls._db_model = dct.get('_db_model')
        return cls


class BaseAdapter(metaclass=BaseAdapterMeta):
    _db_model: Type[Base]
    _enable_caching: bool = True
    _game_id_key = 'id'
    _specific_sfs_datatypes = {}

    id: int = None

    date_created: int = round(datetime.now().timestamp() * 1000)
    last_updated: int = round(datetime.now().timestamp() * 1000)

    async def save(self):
        await self.before_save()

        async with Session() as session:
            db_instance = await session.get(self._db_model, self.id)

            if db_instance is None:
                db_instance = self._db_model()
                db_instance.id = self.id
                session.add(db_instance)

            for field, value in self.to_dict().items():
                setattr(db_instance, field, value)

            await session.flush()
            await session.refresh(db_instance)
            self.id = db_instance.id

            await self.after_save()
            await session.commit()

        if self._enable_caching:
            asyncio.create_task(RedisSession.hset(f"{self._db_model.__tablename__}_db", str(self.id), pickle.dumps(self.to_dict())))

    @classmethod
    async def load_by_id(cls: Type[T], id: int) -> T:  # match_type: ignore
        if cls._enable_caching and (params := await RedisSession.hget(f"{cls._db_model.__tablename__}_db", str(id))) is not None:
            return await cls.from_dict(pickle.loads(params))
        async with Session() as session:
            db_instance = await session.get(cls._db_model, id)
            if db_instance:
                return await cls.from_db_instance(db_instance)

        assert Exception('Object is not exists.')

    @classmethod
    async def load_one_by(cls: Type[T], query_class, query) -> T:
        async with Session() as session:  # type: AsyncSession
            stmt = select(cls._db_model).where(query_class == query)
            result = await session.execute(stmt)
            db_instance = result.scalar_one_or_none()
            if db_instance:
                return await cls.from_db_instance(db_instance)

        raise ValueError("Object not found in load_one_by")

    @classmethod
    async def load_all_by(cls: Type[T], query_class, query) -> List[T]:
        async with Session() as session:  # type: AsyncSession
            stmt = select(cls._db_model).where(query_class == query)
            result = await session.execute(stmt)
            db_instances = result.scalars().all()

        # Можно убрать параллелизацию, если она не даёт прироста
        return [await cls.from_db_instance(db_inst) for db_inst in db_instances]

    @classmethod
    async def load_all(cls: Type[T], cached=True) -> List[T]:
        if cls._enable_caching and cached and (objects := await RedisSession.hgetall(f"{cls._db_model.__tablename__}_db")) != {}:
            return [await cls.from_dict(pickle.loads(params)) for params in objects.values()]
        async with Session() as session:
            result = await session.execute(select(cls._db_model))
            db_instances = result.scalars().all()
            return await asyncio.gather(*[asyncio.create_task(cls.from_db_instance(db_instance)) for db_instance in db_instances])

    @classmethod
    async def from_db_instance(cls: Type[T], db_instance: Base) -> T:
        instance = cls()
        for field in cls._db_model.__table__.columns.keys():
            setattr(instance, field, getattr(db_instance, field))

        await instance.on_load_complete()

        # Кэшируем синхронно для согласованности (можете сделать и через create_task)
        if cls._enable_caching:
            try:
                await RedisSession.hset(
                    f"{cls._db_model.__tablename__}_db",
                    str(instance.id),
                    pickle.dumps(instance.to_dict())
                )
            except:
                pass

        return instance

    def to_dict(self) -> dict:
        obj = {}
        for field in self._db_model.__table__.columns.keys():
            if field == 'id':
                obj[self._game_id_key] = getattr(self, field)
            else:
                obj[field] = getattr(self, field)
        return obj

    @classmethod
    async def from_dict(cls: Type[T], params: dict) -> T:
        instance = cls()
        for field, value in params.items():
            if field == cls._game_id_key:
                setattr(instance, 'id', value)
            else:
                setattr(instance, field, value)
        await instance.on_load_complete()
        return instance

    async def to_sfs_object(self) -> SFSObject:
        obj = SFSObject()
        for field in self._db_model.__table__.columns.keys():
            key = self._game_id_key if field == 'id' else field
            val = getattr(self, field)
            if val is None:
                continue
            sds = {'id': Long, 'date_created': Long, 'last_updated': Long} | self._specific_sfs_datatypes
            if field in sds:
                obj.set_item(key, sds.get(field)(name=key, value=val))
            else:
                obj.putAny(key, val)
        return await self.update_sfs(obj)

    @classmethod
    async def from_sfs_object(cls: Type[T], obj: SFSObject) -> T:
        instance = cls()
        values = obj.get_value()
        for field, val_container in values.items():
            # Если внутри ещё один SFSObject/SFSArray
            if isinstance(val_container, (SFSObject, SFSArray)):
                val = val_container.to_json()
            else:
                val = val_container.get_value()

            if field == cls._game_id_key:
                setattr(instance, 'id', val)
            else:
                setattr(instance, field, val)

        await instance.on_sfs_load_complete()
        await instance.on_load_complete()
        return instance

    async def remove(self):
        async with Session() as session:
            db_instance = await session.get(self._db_model, self.id)
            if db_instance:
                await session.delete(db_instance)
                await session.commit()

        if self._enable_caching:
            try:
                await RedisSession.hdel(f"{self._db_model.__tablename__}_db", str(self.id))
            except:
                ...

        await self.on_remove()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.save()

    def __repr__(self):
        fvars = ', '.join([f'{k}={repr(v)}' for k, v in vars(self).items()])
        return f"{self.__class__.__name__}({fvars})"

    def __str_(self):
        fvars = ', '.join([f'{k}={repr(v)}' for k, v in vars(self).items()])
        return f"{self.__class__.__name__}({fvars})"

    async def on_load_complete(self):
        return

    async def after_save(self):
        return

    async def before_save(self):
        return

    async def on_sfs_load_complete(self):
        return

    async def update_sfs(self, params: SFSObject):
        return params

    async def on_remove(self):
        ...
