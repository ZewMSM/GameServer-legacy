from datetime import datetime
from typing import AsyncIterable

from sqlalchemy import select

from ZewSFS.Types import Int, SFSObject, SFSArray
from database import IslandDB, IslandMonsterDB, IslandStructureDB, Session, IslandThemeDataDB
from database.base_adapter import BaseAdapter


class Island(BaseAdapter):
    _db_model = IslandDB
    _game_id_key = 'island_id'
    _specific_sfs_datatypes = {'id': Int}

    # Basic information
    name: str = ''
    short_name: str = ''
    description: str = ''
    first_time_visit_desc: str = ''
    first_time_visit_menu: str = ''

    # Costs
    cost_coins: int = 0
    cost_keys: int = 0
    cost_relics: int = 0
    cost_diamonds: int = 0
    cost_starpower: int = 0
    cost_medals: int = 0
    cost_eth_currency: int = 0

    # Requirements and settings
    min_level: int = 0
    min_server_version: str = '0.0.0'
    enabled: bool = True
    island_type: int = 0
    island_lock: int = 0
    has_nursery_scratch: bool = True
    has_book: bool = True

    # Graphics and audio
    graphic: str = ''
    iconSheet: str = ''
    iconSprite: str = ''
    torch_graphic: str = ''
    midi: str = ''
    ambient_track: str = ''

    # Structures
    castle_structure_id: int = 0
    grid: str = ''

    async def update_sfs(self, params: SFSObject):
        params.putSFSObject('graphic', SFSObject.from_json(self.graphic))

        monsters = SFSArray()
        for monster in await IslandMonster.load_all_by(IslandMonsterDB.island_id, self.id):
            monsters.addSFSObject(await monster.to_sfs_object())
        params.putSFSArray('monsters', monsters)

        structures = SFSArray()
        for structure in await IslandStructure.load_all_by(IslandStructure.island_id, self.id):
            structures.addSFSObject(await structure.to_sfs_object())
        params.putSFSArray('structures', structures)
        params.putInt('island_lock', 1)
        return params

    async def load_monsters(self) -> AsyncIterable:
        for monster in await IslandMonster.load_all_by(IslandMonsterDB.island_id, self.id):
            yield monster


class IslandMonster(BaseAdapter):
    _db_model = IslandMonsterDB
    _game_id_key = 'id'
    _specific_sfs_datatypes = {'id': Int, 'monster': Int, 'island_id': Int}

    island_id: int = 0
    monster: int = 0
    bom: bool = False
    book_y: int = 0
    book_x: int = 0
    instrument: str = ''
    book_flip: bool = False
    book_z: int = 0
    last_changed: int = datetime.now().timestamp() * 1000

    async def update_if_exists(self):
        async with Session() as session:
            db_instance = (await session.execute(select(IslandMonsterDB).where(IslandMonsterDB.island_id == self.island_id).where(IslandMonsterDB.monster == self.monster))).scalar_one_or_none()
            if db_instance:
                self.id = db_instance.id


class IslandStructure(BaseAdapter):
    _db_model = IslandStructureDB
    _game_id_key = 'id'
    _specific_sfs_datatypes = {'id': Int, 'structure': Int, 'island_id': Int}

    island_id: int = 0
    structure: int = 0
    instrument: str
    last_changed: int = datetime.now().timestamp() * 1000

    async def update_if_exists(self):
        async with Session() as session:
            db_instance = (await session.execute(select(IslandStructureDB).where(IslandStructureDB.island_id == self.island_id).where(IslandStructureDB.structure == self.structure))).scalar_one_or_none()
            if db_instance:
                print('FOUND SAME OBJECT, USING HIS ID', db_instance.id)
                self.id = db_instance.id


class IslandThemeData(BaseAdapter):
    _db_model = IslandThemeDataDB
    _game_id_key = 'theme_id'
    _specific_sfs_datatypes = {'id': Int}

    # Identification
    name: str = ''
    theme_id: int = 0
    island: int = 0
    storeitem_id: int = 0

    # Costs
    cost_coins: int = 0
    cost_keys: int = 0
    cost_diamonds: int = 0
    cost_starpower: int = 0
    cost_eth_currency: int = 0
    cost_relics: int = 0

    # Availability
    level: int = 0
    view_in_market: int = 0
    unlocked_entities: str = None

    # Descriptions
    description: str = ''
    modifier_description: str = ''

    # Modifiers
    modifiers: str = None
    _modifiers: dict = None

    # Content
    trees: str = None
    rocks: str = None

    # Placement and Graphics
    placement_id: str = ''
    graphic: str = ''

    # Event Information
    season_event_name: str = None
    month_string: str = None

    # Versioning
    version: str = ''
    last_changed: int = 0

    async def update_sfs(self, params: SFSObject):
        params.putSFSObject('graphic', SFSObject.from_json(self.graphic))
        try:
            params.putSFSObject('modifiers', SFSObject.from_json(self.modifiers))
        except:
            del params['modifiers']
        try:
            params.putSFSObject('trees', SFSObject.from_json(self.trees))
        except:
            params.putSFSObject('trees', SFSObject())
        try:
            params.putSFSObject('rocks', SFSObject.from_json(self.rocks))
        except:
            params.putSFSObject('rocks', SFSObject())
        del params['unlocked_entities']
        del params['date_created']
        return params
