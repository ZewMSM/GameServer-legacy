import json

from sqlalchemy import select
from sqlalchemy.util import await_only

from ZewSFS.Types import Int, SFSObject, SFSArray
from database import MonsterDB, MonsterCostumeDB, FlexEggsDB, RareMonsterDataDB, EpicMonsterDataDB, MonsterHomeDB, \
    Session, MonsterLevelDB
from database.base_adapter import BaseAdapter


class Monster(BaseAdapter):
    _db_model = MonsterDB
    _game_id_key = 'monster_id'
    _specific_sfs_datatypes = {'id': Int}

    cost_diamonds: int = 0
    cost_coins: int = 0
    cost_keys: int = 0
    cost_sale: int = 0
    cost_starpower: int = 0
    cost_medals: int = 0
    cost_relics: int = 0
    cost_eth_currency: int = 0

    size_x: int = 0
    size_y: int = 0
    y_offset: int = 0

    name: str = ''
    common_name: str = ''
    description: str = ''
    class_name: str = ''
    genes: str = ''

    view_in_market: bool = False
    view_in_starmarket: bool = False
    premium: bool = False
    box_monster: bool = False
    movable: bool = False

    requirements: list[int] = None
    happiness: list[int] = None
    min_level: int = 0

    entity_id: int = 0
    entity_type: str = 'monster'

    graphic: str = ''

    build_time: int = 0
    beds: int = 0
    xp: int = 0
    time_to_fill_sec: int = 0

    keywords: str = ''
    min_server_version: str = ''
    levelup_island: int = 0

    levels: list['MonsterLevel']

    async def on_sfs_load_complete(self):
        self.happiness = [int(h.get('entity')) for h in json.loads(self.happiness)]
        self.requirements = []  # int(h.get('entity')) for h in json.loads(self.requirements) # TODO: Fix

    async def update_sfs(self, params: SFSObject):
        hap = SFSArray()
        for en in self.happiness:
            hap.addSFSObject(SFSObject().putInt('entity', en).putInt('value', 1))
        params.putSFSArray('happiness', hap)

        params.putSFSArray('requirements', SFSArray())  # TODO: Fix

        params.putUtfString('class', self.class_name)
        params.putSFSObject('graphic', SFSObject.from_json(self.graphic))
        params.putUtfString('genes', 'Q')

        levels = SFSArray()
        for level in await MonsterLevel.load_all_by(MonsterLevelDB.monster_id, self.id):
            levels.addSFSObject(await level.to_sfs_object())
        params.putSFSArray('levels', levels)  # TODO: Fix
        return params

    async def on_load_complete(self):
        self.levels = await MonsterLevel.load_all_by(MonsterLevelDB.monster_id, self.id)


class MonsterCostume(BaseAdapter):
    _db_model = MonsterCostumeDB
    _game_id_key = 'id'

    min_version: str = "0.9.0"
    ignore_locks: bool = False
    always_visible: bool = False
    hidden: bool = True
    keywords: str = ''
    medalCost: int = 0
    sellCost: int = 0
    etherealSellCost: int = 0
    diamondCost: int = 0
    alt_icon_name: str = ''
    unlock_teleport: bool = True
    breed_chance: float = 0
    file: str = ""
    monster_id: int = 0
    alt_text: str = ''
    name: str = ""
    action: int = 0
    alt_icon_sheet: str = ''
    common_name: str = ''
    unlock_purchased: bool = False


class FlexEggs(BaseAdapter):
    _db_model = FlexEggsDB
    _game_id_key = 'id'

    cost_coins: int = 0
    cost_diamonds: int = 0
    xp: int = 0
    mastertext_desc: str = ''
    _def: str

    async def on_sfs_load_complete(self):
        self._def = self.__dict__.get('def')

    async def update_sfs(self, params: SFSObject):
        return params.putSFSObject('def', SFSObject.from_json(self._def))


class RareMonsterData(BaseAdapter):
    _db_model = RareMonsterDataDB
    _game_id_key = 'common_id'

    rare_id: int = 0
    last_changed: int = None


class EpicMonsterData(BaseAdapter):
    _db_model = EpicMonsterDataDB
    _game_id_key = 'common_id'

    epic_id: int = 0
    last_changed: int = None


class MonsterHome(BaseAdapter):
    _db_model = MonsterHomeDB
    _game_id_key = 'id'

    source_monster: int = 0
    source_island: int = 0
    dest_monster: int = 0
    dest_island: int = 0
    last_changed: int = None

    async def update_if_exists(self):
        async with Session() as session:
            db_instance = (await session.execute(
                select(MonsterHomeDB).where(MonsterHomeDB.source_monster == self.source_monster).where(
                    MonsterHomeDB.source_island == self.source_island))).scalar_one_or_none()
            if db_instance:
                self.id = db_instance.id


class MonsterLevel(BaseAdapter):
    _db_model = MonsterLevelDB
    _game_id_key = 'id'

    monster_id: int = 0
    level: int = 1
    coins: int = 0
    max_coins: int = 0
    food: int = 0
    max_ethereal: int = 0
    ethereal_currency: int = 0

    last_changed: int = None

    monster: 'Monster'

    async def update_if_exists(self):
        async with Session() as session:
            db_instance = (await session.execute(
                select(MonsterLevelDB).where(MonsterLevelDB.monster_id == self.monster_id).where(
                    MonsterLevelDB.level == self.level))).scalar_one_or_none()
            if db_instance:
                self.id = db_instance.id