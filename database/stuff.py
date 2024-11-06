from sqlalchemy import select

from ZewSFS.Types import Int, SFSObject, SFSArray
from database import NucleusRewardDB, EntityAltCostsDB, TitanSoulLevelDB, TimedEventsDB, GameSettingsDB, Session
from database.base_adapter import BaseAdapter


class NucleusReward(BaseAdapter):
    _db_model = NucleusRewardDB
    _game_id_key = 'monster_sets'

    types: list[int] = []
    last_changed: int = None


class EntityAltCosts(BaseAdapter):
    _db_model = EntityAltCostsDB
    _game_id_key = 'id'
    _specific_sfs_datatypes = {'id': Int}

    cost_coins: int = 0
    cost_keys: int = 0
    cost_eth_currency: int = 0
    cost_diamonds: int = 0
    cost_relics: int = 0
    cost_starpower: int = 0
    entity_id: int = 0
    island: int = 0
    last_changed: int = None


class TitanSoulLevel(BaseAdapter):
    _db_model = TitanSoulLevelDB
    _game_id_key = 'level'
    _specific_sfs_datatypes = {'id': Int}

    min_links: int = 0
    power: int = 0
    song_part: int = 0
    last_changed: int = None


class TimedEvents(BaseAdapter):
    _db_model = TimedEventsDB
    _game_id_key = 'id'

    start_date: int = 0
    end_date: int = 0
    event_type: str = ''
    data: str = ''
    event_id: int
    last_changed: int = None

    async def update_sfs(self, params: SFSObject):
        return params.putSFSArray('data', SFSArray.from_json(self.data))


class GameSettings(BaseAdapter):
    _db_model = GameSettingsDB
    _game_id_key = 'id'

    key: str = ''
    value: str = ''
    last_changed: int = None

    async def update_if_exists(self):
        async with Session() as session:
            db_instance = (await session.execute(select(GameSettingsDB).where(GameSettingsDB.key == self.key))).scalar_one_or_none()
            if db_instance:
                self.id = db_instance.id

    @staticmethod
    async def load_by_key(key: str) -> 'GameSettings':
        return await GameSettings.load_one_by(GameSettingsDB.key, key)
