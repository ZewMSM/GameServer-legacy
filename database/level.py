from sqlalchemy import select

from database import LevelDB
from database.base_adapter import BaseAdapter


class Level(BaseAdapter):
    _db_model = LevelDB
    _game_id_key = 'level'

    xp: int
    title: str = None
    max_bakeries: int
