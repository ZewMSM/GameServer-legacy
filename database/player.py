import json
import logging
import time
from typing import List

from ZewSFS.Types import SFSObject, SFSArray, Long, Double, Bool, Int
from database import PlayerDB, PlayerIslandDB, PlayerStructureDB, PlayerEggDB, PlayerMonsterDB
from database.base_adapter import BaseAdapter
from database.island import Island
from database.level import Level
from database.monster import Monster
from database.structure import Structure

logger = logging.getLogger('GameServer/Player')


class Player(BaseAdapter):
    _db_model = PlayerDB
    _game_id_key = 'bbb_id'
    _specific_sfs_datatypes = {
        "friend_gift": Long,
        "egg_wildcards": Long,
        "is_admin": Int,
        "last_login": Long,
        "active_island": Long,
        "speed_up_credit": Long
    }

    is_admin: bool = False
    player_groups: List['int'] = [40, 45, 51]
    premium: bool = True
    display_name: str = 'New Player'
    friend_gift: int = 0
    country: str = 'UK'

    diamonds: int = 1_999_999_999
    coins: int = 1_999_999_999
    diamonds_spent: int = 0
    egg_wildcards: int = 999_999_999
    keys: int = 999_999_999
    food: int = 1_999_999_999
    level: int = 100
    relics: int = 999_999_999
    xp: int = 0
    starpower: int = 999_999_999
    ethereal_currency: int = 999_999_999
    total_starpower_collected: int = 0
    moniker_id: int = None

    active_island: int = -1
    avatar: dict = {'pp_type': 0, 'pp_info': 0}

    battle_level: int = 1
    battle_xp: int = 0
    battle_loadout: dict = {"slot2": 0, "slot1": 0, "slot0": 0}  # JSON
    battle_loadout_versus: dict = {"slot2": 0, "slot1": 0, "slot0": 0}  # JSON
    battle_max_training_level: int = 10
    battle_medals: int = 0
    pvp_season0: dict = {"schedule_started_on": 0, "campaign_id": 0}
    pvp_season1: dict = {"schedule_started_on": 0, "campaign_id": 0}
    prev_rank: int = 0
    prev_tier: int = -1
    prizes: str = None  # Can me None

    daily_cumulative_login_calendar_id: int = 1  # TODO: Add DailyCumulativeLoginCalendar Database
    daily_cumulative_login_next_collect: int = 0
    daily_cumulative_login_reward_idx: int = 0
    daily_cumulative_login_total: int = 0

    daily_relic_purchase_count: int = 0
    next_relic_reset: int = 0
    relic_diamond_cost: int = 1
    speed_up_credit: int = 8

    cached_reward_day: int = 1
    reward_day: int = 1
    daily_bonus_amount: int = 0
    daily_bonus_type: str = 'none'
    rewards_total: int = 0
    scaled_daily_reward: list = []
    next_daily_login: int = 0

    client_platform: str = 'pc'
    client_tutorial_setup: str = "breedingAddOnBridged"

    has_promo: bool = False
    has_free_ad_scratch: bool = False
    has_scratch_off_m: bool = False
    has_scratch_off_s: bool = False
    flip_game_time: int = -1
    monster_scratch_time: int = 0
    currency_scratch_time: int = 0

    purchases_amount: int = 0
    purchases_total: int = 0

    date_created: int = 0
    last_login: int = 0
    last_client_version: str = '0.0.0'

    inventory: list = []  # {'items': SFSArray()}
    new_mail: bool = False
    owned_island_themes: List[int] = []  # JSON

    last_collect_all: int = 0
    last_relic_purchase: int = 0
    show_welcomeback: bool = False
    referral: int = 0  # Can be NONE if dont used

    extra_ad_params: str = ""
    email_invite_reward: int = 0
    fb_invite_reward: int = 0
    twitter_invite_reward: int = 0
    last_fb_post_reward: int = 0
    third_party_ads: bool = False
    third_party_video_ads: bool = False

    last_changed: int = None

    islands: list['PlayerIsland']

    async def update_sfs(self, params: SFSObject):
        params.putLong('bbb_id', self.id)
        params.putLong('user', self.id)
        params.putLong('user_id', self.id)

        params.putLong('coins_actual', self.coins)
        params.putLong('diamonds_actual', self.diamonds)
        params.putLong('food_actual', self.food)
        params.putLong('coins_actual', self.coins)
        params.putLong('keys_actual', self.keys)
        params.putLong('ethereal_currency_actual', self.ethereal_currency)
        params.putLong('starpower_actual', self.starpower)
        params.putLong('relics_actual', self.relics)
        params.putLong('egg_wildcards_actual', self.egg_wildcards)

        params.putSFSObject('avatar', SFSObject()
                            .putUtfString('pp_info', str(self.avatar.get('pp_info', '0')))
                            .putInt('pp_type', int(self.avatar.get('pp_type', 0)))
                            .putLong('user_id', self.id))

        params.putSFSObject('battle', SFSObject()
                            .putInt('level', self.battle_level)
                            .putInt('xp', self.battle_xp)
                            .putInt('max_training_level', self.battle_max_training_level)
                            .putInt('medals', self.battle_medals)
                            .putLong('user_id', self.id)
                            .putUtfString('loadout', json.dumps(self.battle_loadout))
                            .putUtfString('loadout_versus', json.dumps(self.battle_loadout_versus)))

        params.putSFSObject('costumes', SFSObject()
                            .putSFSArray('items', SFSArray())
                            .putIntArray('unlocked', []))

        params.putSFSObject('daily_cumulative_login', SFSObject()
                            .putInt('calendar_id', self.daily_cumulative_login_calendar_id)
                            .putInt('reward_idx', self.daily_cumulative_login_reward_idx)
                            .putInt('total', self.daily_cumulative_login_total))

        params.putSFSObject('pvpSeason0',
                            SFSObject().putInt('campaign_id', self.pvp_season0.get('campaign_id', 0)).putLong(
                                'schedule_started_on',
                                self.pvp_season0.get('schedule_started_on', 0)))  # TODO: Add PVP SEASON
        params.putSFSObject('pvpSeason1',
                            SFSObject().putInt('campaign_id', self.pvp_season1.get('campaign_id', 0)).putLong(
                                'schedule_started_on',
                                self.pvp_season1.get('schedule_started_on', 0)))  # TODO: Add PVP SEASON

        params.putSFSArray('achievements', SFSArray())
        params.putSFSArray('active_island_themes', SFSArray())
        params.putSFSArray('islands', SFSArray())
        params.putSFSArray('tracks', SFSArray())
        params.putSFSArray('songs', SFSArray())
        params.putSFSArray('mailbox', SFSArray())
        params.putSFSObject('inventory', SFSObject().putSFSArray('items', SFSArray()))

        params.putLong("monsterScratchTime", self.monster_scratch_time)
        params.putLong("nextDailyLogin", self.next_daily_login)
        params.putIntArray("owned_island_themes", [])

        params.putSFSArray("scaled_daily_reward", SFSArray())
        params.putSFSArray("timed_events", SFSArray())
        params.putSFSObject("unlocks", SFSObject())

        islands = SFSArray()
        for island in self.islands:
            islands.addSFSObject(await island.to_sfs_object())

        params.putSFSArray('islands', islands)
        params.putLong("last_login", round(self.last_login))

        return params

    async def before_save(self):
        self.pvp_season0 = json.dumps(self.pvp_season0)
        self.pvp_season1 = json.dumps(self.pvp_season1)
        self.avatar = json.dumps(self.avatar)
        self.battle_loadout = json.dumps(self.battle_loadout)
        self.battle_loadout_versus = json.dumps(self.battle_loadout_versus)
        self.player_groups = json.dumps(self.player_groups)
        self.scaled_daily_reward = json.dumps(self.scaled_daily_reward)
        self.inventory = json.dumps(self.inventory)
        self.owned_island_themes = json.dumps(self.owned_island_themes)

    async def after_save(self):
        self.pvp_season0 = json.loads(self.pvp_season0)
        self.pvp_season1 = json.loads(self.pvp_season1)
        self.avatar = json.loads(self.avatar)
        self.battle_loadout = json.loads(self.battle_loadout)
        self.battle_loadout_versus = json.loads(self.battle_loadout_versus)
        self.player_groups = json.loads(self.player_groups)
        self.scaled_daily_reward = json.loads(self.scaled_daily_reward)
        self.inventory = json.loads(self.inventory)
        self.owned_island_themes = json.loads(self.owned_island_themes)

    async def on_load_complete(self):
        if type(self.pvp_season1) is str:
            self.pvp_season0 = json.loads(self.pvp_season0)
            self.pvp_season1 = json.loads(self.pvp_season1)
            self.avatar = json.loads(self.avatar)
            self.battle_loadout = json.loads(self.battle_loadout)
            self.battle_loadout_versus = json.loads(self.battle_loadout_versus)
            self.player_groups = json.loads(self.player_groups)
            self.scaled_daily_reward = json.loads(self.scaled_daily_reward)
            self.inventory = json.loads(self.inventory)
            self.owned_island_themes = json.loads(self.owned_island_themes)

        self.islands = await PlayerIsland.load_all_by(PlayerIslandDB.user_id, self.id)

        if len(self.islands) == 0:
            self.islands.append(await PlayerIsland.create_new_island(self.id, 1))

        if self.get_island(self.active_island) is None:
            self.active_island = self.islands[0].id

    async def create_new_player(self):
        logger.info(f'Creating new player(bbb_id={self.id})')

        player_island = await PlayerIsland.create_new_island(self.id, 1)

        self.islands = [player_island]
        self.active_island = player_island.id

    async def check_prices(self, *args, coins: int = None, diamonds: int = None, food: int = None,
                           starpower: int = None, medals: int = None,
                           relics: int = None, keys: int = None, obj: Island | Monster | Structure = None,
                           check_all: bool = False, charge_if_can: bool = True,
                           eth_instead_of_coins: bool = False):
        if obj is not None:
            if coins is None: coins = (obj.cost_coins if not eth_instead_of_coins else obj.cost_eth_currency)
            if diamonds is None: diamonds = obj.cost_diamonds
            if starpower is None: starpower = obj.cost_starpower
            if medals is None: medals = obj.cost_medals
            if relics is None: relics = obj.cost_relics
            if keys is None: keys = obj.cost_keys

        if coins is None: coins = 0
        if diamonds is None: diamonds = 0
        if starpower is None: starpower = 0
        if medals is None: medals = 0
        if relics is None: relics = 0
        if keys is None: keys = 0
        if food is None: food = 0

        checks = {
            diamonds: (self.diamonds, 'diamonds'),
            relics: (self.relics, 'relics'),
            keys: (self.keys, 'keys'),
            coins: (self.coins, 'coins') if not eth_instead_of_coins else (self.ethereal_currency, 'ethereal_currency'),
            starpower: (self.starpower, 'starpower'),
            medals: (self.battle_medals, 'battle_medals'),
            food: (self.food, 'food'),
        }

        if check_all:
            for need, (have, curr) in checks.items():
                if have < need:
                    return False
            if charge_if_can:
                for need, (have, curr) in checks.items():
                    self.__setattr__(curr, have - need)
                await self.save()
        else:
            for need, (have, curr) in checks.items():
                if need != 0:
                    if (ok := have >= need) and charge_if_can:
                        self.__setattr__(curr, have - need)
                        await self.save()
                    return ok

        return True

    @property
    def get_active_island(self):
        for island in self.islands:
            if island.id == self.active_island:
                return island

    def get_island(self, user_island_id):
        for island in self.islands:
            if island.id == user_island_id:
                return island

    def get_island_by_id(self, island_id):
        for island in self.islands:
            if island.island_id == island_id:
                return island

    async def add_currency(self, currency: str, amount: int):
        amount = int(amount)
        if currency == "coins":
            self.coins += amount
        elif currency == "diamonds":
            self.diamonds += amount
        elif currency == "keys":
            self.keys += amount
        elif currency == "relics":
            self.relics += amount
        elif currency == "starpower":
            self.starpower += amount
            # self.total_starpower_collected += amount
        elif currency == "medals":
            self.battle_medals += amount
        elif currency == "speed_up_credit":
            self.speed_up_credit += amount
        elif currency == "xp":
            if self.level < 100:
                self.xp += amount
                if self.xp >= (await Level.load_by_id(self.level + 1)).xp:
                    self.level += 1
                    self.xp = 0
        elif currency == "food":
            self.food += amount
        elif currency == 'eth' or currency == 'ethereal_currency':
            self.ethereal_currency += amount
        else:
            raise ValueError(f"Unknown currency: {currency}")

        await self.save()

    def get_properties(self):
        props = SFSArray()
        props.addSFSObject(SFSObject().putLong('coins_actual', self.coins))
        props.addSFSObject(SFSObject().putLong('diamonds_actual', self.diamonds))
        props.addSFSObject(SFSObject().putLong('keys_actual', self.keys))
        props.addSFSObject(SFSObject().putLong('relics_actual', self.relics))
        props.addSFSObject(SFSObject().putLong('starpower_actual', self.starpower))
        props.addSFSObject(SFSObject().putLong('diamonds_spent', self.diamonds_spent))
        props.addSFSObject(SFSObject().putLong('xp', self.xp))
        props.addSFSObject(SFSObject().putInt('level', self.level))
        props.addSFSObject(SFSObject().putLong('medals', self.battle_medals))
        props.addSFSObject(SFSObject().putLong('speed_up_credit', self.speed_up_credit))
        props.addSFSObject(SFSObject().putLong('food_actual', self.food))
        # props.addSFSObject(SFSObject().putLong())

        return props


class PlayerIsland(BaseAdapter):
    _db_model = PlayerIslandDB
    _game_id_key = 'user_island_id'
    _specific_sfs_datatypes = {'user_id': Long}

    island_id: int = None
    user_id: int = None
    last_baked: str = '{}'
    costumes_owned: str = '[]'
    likes: int = 0
    dislikes: int = 0
    last_player_level: int = 0
    light_torch_flag: bool = False
    warp_speed: float = 1.0
    monsters_sold: str = '[]'
    monsters_sold_ids: list[int]
    name: str = None

    last_changed: int = None

    island: 'Island'
    structures: list['PlayerStructure'] = None
    eggs: list['PlayerEgg'] = None
    monsters: list['PlayerMonster'] = None

    async def before_save(self):
        self.last_baked = json.dumps(self.last_baked)
        self.costumes_owned = json.dumps(self.costumes_owned)
        self.monsters_sold = json.dumps(self.monsters_sold_ids)

    async def after_save(self):
        self.last_baked = json.loads(self.last_baked)
        self.costumes_owned = json.loads(self.costumes_owned)

    async def on_load_complete(self):
        if type(self.last_baked) is str:
            self.last_baked = json.loads(self.last_baked)
            self.costumes_owned = json.loads(self.costumes_owned)

        self.island = await Island.load_by_id(int(self.island_id))
        self.structures = await PlayerStructure.load_all_by(PlayerStructureDB.user_island_id, self.id)
        self.eggs = await PlayerEgg.load_all_by(PlayerEggDB.user_island_id, self.id)
        self.monsters = await PlayerMonster.load_all_by(PlayerMonsterDB.user_island_id, self.id)

        self.monsters_sold_ids = json.loads(self.monsters_sold)
        if type(self.monsters_sold_ids) is str:
            self.monsters_sold_ids = []

    async def update_sfs(self, params: SFSObject):
        params.putLong('user', self.user_id)
        params.putInt('island', self.island.id)
        params.putInt('type', self.island.island_type)
        params.putInt('num_torches', 0)  # TODO: Add torches
        params.putUtfString("costumes_owned", json.dumps(self.costumes_owned))
        params.putUtfString('monsters_sold', json.dumps(list(self.monsters_sold_ids)))

        params.putSFSArray("baking", SFSArray())  # TODO: Add baking
        params.putSFSArray("breeding", SFSArray())  # TODO: Add breeding
        params.putSFSObject("costume_data", SFSObject().putSFSArray('costumes', SFSArray()))  # TODO: Add costumes
        params.putSFSArray("fuzer", SFSArray())  # TODO: Add fuzer
        params.putSFSArray("monsters", SFSArray())
        params.putSFSArray("torches", SFSArray())  # TODO: Add torches
        params.putSFSArray("last_baked", SFSArray())
        params.putSFSArray("tiles", SFSArray())

        structures = SFSArray()
        for structure in self.structures:
            structures.addSFSObject(await structure.to_sfs_object())
        params.putSFSArray("structures", structures)

        eggs = SFSArray()
        for egg in self.eggs:
            eggs.addSFSObject(await egg.to_sfs_object())
        params.putSFSArray("eggs", eggs)

        monsters = SFSArray()
        for monster in self.monsters:
            monsters.addSFSObject(await monster.to_sfs_object())
        params.putSFSArray("monsters", monsters)

        return params

    @staticmethod
    async def create_new_island(user_id: int, island_id: int):
        async with PlayerIsland() as self:
            self.island_id = island_id
            self.user_id = user_id
            self.monsters_sold_ids = []
        await self.on_load_complete()
        logger.info(f'Created new island(island_id={self.island.id}) for player(bbb_id={self.user_id})')

        from GameServer.tools.player_island_factory import PlayerIslandFactory
        await PlayerIslandFactory.create_initial_structures(self)

        return self

    def is_gold_island(self):
        return self.island_id == 6

    def is_shuga_island(self):
        return self.island_id == 8

    def is_tribal_island(self):
        return self.island_id == 9

    def is_wublin_island(self):
        return self.island_id == 10

    def is_celestial_island(self):
        return self.island_id == 12

    def is_amber_island(self):
        return self.island_id == 22

    def is_composer_island(self):
        return self.island_id == 11

    def is_battle_island(self):
        return self.island_id == 20

    def is_seasonal_island(self):
        return self.island_id == 21

    def is_myth_island(self):
        return self.island_id == 23

    def is_workshop_island(self):
        return self.island_id == 24

    def is_nexus_island(self):
        return self.island_id == 25

    def is_box_island(self):
        return self.is_amber_island() or self.is_wublin_island() or self.is_celestial_island()

    def is_ethereal_island(self):
        return self.island_id in (7, 19, 24)

    def has_max_structures(self, structure_type):
        if structure_type in ('decoration', 'obstacle'):
            return False

        count = 0
        for structure in self.structures:
            if structure.structure.structure_type == structure_type:
                count += 1

        if structure_type in ('breeding', 'nursery'):
            return count >= 2

        if structure_type == 'torch':
            return count >= 10

        if structure_type == 'bakery':
            return count >= 5

        return count >= 1

    def get_structure(self, user_structure_id):
        for structure in self.structures:
            if structure.id == user_structure_id:
                return structure

    def get_structures_by_type(self, structure_type):
        for structure in self.structures:
            if structure.structure.structure_type.lower() == structure_type.lower():
                yield structure

    def get_egg(self, user_egg_id):
        for egg in self.eggs:
            if egg.id == user_egg_id:
                return egg

    def get_monster(self, user_monster_id):
        for monster in self.monsters:
            if monster.id == user_monster_id:
                return monster


class PlayerStructure(BaseAdapter):
    _db_model = PlayerStructureDB
    _game_id_key = 'user_structure_id'
    _specific_sfs_datatypes = {'user_island_id': Long}

    pos_x: int = 0
    pos_y: int = 0
    flip: bool = False  # int in sfs
    scale: float = 1.0
    muted: bool = False  # int in sfs
    last_collection: int = 0
    date_created: int = 0
    building_completed: int = 0
    is_upgrading: bool = False  # int in sfs
    is_complete: bool = False  # int in sfs
    in_warehouse: bool = False  # int in sfs
    user_island_id: int = None
    structure_id: int = None

    last_changed: int = None

    structure: 'Structure'
    island: 'PlayerIsland'

    async def on_load_complete(self):
        self.structure = await Structure.load_by_id(int(self.structure_id))

    async def get_island(self):
        return await PlayerIsland.load_by_id(int(self.user_island_id))

    async def update_sfs(self, params: SFSObject):
        return params.putLong('island', self.user_island_id).putInt('structure', self.structure_id)

    @staticmethod
    async def create_new_structure(user_island_id, structure_id, pos_x: int, pos_y: int, completed: bool):
        async with PlayerStructure() as self:
            self.user_island_id = user_island_id
            self.structure_id = structure_id
            self.pos_x = pos_x
            self.pos_y = pos_y

            if completed:
                self.is_complete = True
                self.is_upgrading = False
                self.building_completed = int(time.time() * 1000)
                self.date_created = int(time.time() * 1000)
                self.last_collection = int(time.time() * 1000)

        await self.on_load_complete()
        logger.info(
            f'Created new structure(structure_id={self.structure_id}) for island(user_island_id={self.user_island_id})')
        return self

    async def on_remove(self):
        del self


class PlayerEgg(BaseAdapter):
    _db_model = PlayerEggDB
    _game_id_key = 'user_egg_id'
    _specific_sfs_datatypes = {'user_island_id': Long, 'user_structure_id': Long, 'laid_on': Long, 'hatches_on': Long}

    user_island_id: int = None
    user_structure_id: int = None
    monster_id: int = 0
    laid_on: int = 0
    hatches_on: int = 0
    previous_name: str = ""
    prev_permamega: dict = {}
    book_value: int = -1

    last_changed: int = None

    monster: 'Monster'
    user_structure: 'PlayerStructure'

    async def on_load_complete(self):
        self.monster = await Monster.load_by_id(self.monster_id)
        self.user_structure = await PlayerStructure.load_by_id(self.user_structure_id)

        if type(self.prev_permamega) is str:
            self.prev_permamega = json.loads(self.prev_permamega)

    async def update_sfs(self, params: SFSObject):
        if self.book_value != -1:
            params.putInt('book_value', self.book_value)

        if self.prev_permamega is not None:
            params.putSFSObject('prev_permamega', SFSObject.from_python_object(self.prev_permamega))

        return params.putLong('island', self.user_island_id).putLong('structure', self.user_structure_id).putInt(
            'monster', self.monster_id)

    async def get_island(self):
        return await PlayerIsland.load_by_id(int(self.user_island_id))

    async def mark_as_viewed(self):
        async with await self.get_island() as island:
            if self.monster_id not in island.monsters_sold_ids:
                island.monsters_sold_ids.append(self.monster_id)

    @staticmethod
    async def create_new_egg(island_id: int, structure_id: int, monster_id: int, hatch_now):
        self = PlayerEgg()
        self.monster_id = monster_id
        self.user_structure_id = structure_id
        self.user_island_id = island_id
        self.laid_on = round(time.time() * 1000)

        await self.on_load_complete()

        if hatch_now:
            self.hatches_on = self.laid_on
        else:
            self.hatches_on = round(
                self.laid_on + 1000 * self.monster.build_time * self.user_structure.structure.extra_params.get(
                    'speed_mod', 1.0))

        await self.save()

        logger.info(f'Created new egg(monster={self.monster_id}) for island(user_island_id={self.user_island_id})')

        return self

    async def before_save(self):
        self.prev_permamega = json.dumps(self.prev_permamega)

    async def after_save(self):
        self.prev_permamega = json.loads(self.prev_permamega)


class MonsterMegaData:
    started_at: int = 0
    finished_at: int = 0
    permega: bool = False
    enabled: bool = False

    def __init__(self, started_at: int, finished_at: int, permega: bool, enabled: bool):
        self.started_at = started_at
        self.finished_at = finished_at
        self.permega = permega
        self.enabled = enabled

    def to_sfs(self):
        data = SFSObject()
        data.putBool('permamega', self.permega)
        data.putBool('currently_mega', self.enabled)
        if not self.permega:
            data.putLong('started_at', self.started_at)
            data.putLong('finished_at', self.finished_at)
        return data

    def to_dict(self):
        return {
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'permega': self.permega,
            'enabled': self.enabled
        }

    @staticmethod
    def from_dict(data: dict):
        return MonsterMegaData(
            data.get('started_at', 0),
            data.get('finished_at', 0),
            data.get('permega', False),
            data.get('enabled', False)
        )

    def update(self):
        if not self.permega:
            if self.finished_at < round(time.time() * 1000) and not self.enabled:
                self.enabled = False

        return self


class PlayerMonster(BaseAdapter):
    _db_model = PlayerMonsterDB
    _game_id_key = 'user_monster_id'
    _specific_sfs_datatypes = {'island': Long, 'last_collection': Long, 'last_feeding': Long, 'volume': Double}

    user_island_id: int
    monster_id: int
    currency_type: str = ""
    time_to_collect: int = 0
    underling_happy: int = 0
    name: str = ""
    last_feeding: int = 0
    level: int = 1
    timed_fed: int = 0
    happy: int = 0
    volume: float = 1.0
    in_hotel: bool = False
    marked_for_deletion: bool = False
    box_data: str = ""
    boxed_eggs: str = ""
    mega_data: 'MonsterMegaData' = None
    eggTimerStart: int = 0
    evolutionUnlocked: bool = False
    powerupOnlocked: bool = False
    evolution_static_data: str = ""
    evolution_flex_data: str = ""
    is_training: bool = False
    training_start: int = 0
    training_end: int = 0
    parent_island_id: int = None
    parent_monster_id: int = None
    child_island_id: int = None
    child_monster_id: int = None
    pos_x: int = 0
    pos_y: int = 0
    muted: bool = False
    flip: bool = False
    last_collection: int = None
    book_value: int = 0
    collected_coins: int = 0
    collected_food: int = 0
    collected_diamonds: int = 0
    collected_starpower: int = 0
    collected_ethereal: int = 0
    collected_medals: int = 0
    collected_relics: float = 0.0
    collected_keys: int = 0

    monster: 'Monster'

    last_changed: int = None

    async def on_load_complete(self):
        self.monster = await Monster.load_by_id(self.monster_id)

        if type(self.mega_data) is str:
            self.mega_data = MonsterMegaData.from_dict(json.loads(self.mega_data))
        elif self.mega_data is None:
            self.mega_data = MonsterMegaData(0, 0, False, False)

    async def before_save(self):
        self.mega_data = json.dumps(self.mega_data.to_dict())

    async def after_save(self):
        self.mega_data = MonsterMegaData.from_dict(json.loads(self.mega_data))

    async def get_island(self):
        return await PlayerIsland.load_by_id(int(self.user_island_id))

    async def update_sfs(self, params: SFSObject):
        params.putLong('island', self.user_island_id)
        params.putInt('monster', self.monster_id)

        if self.collected_food != 0:
            params.putInt('collected_food', self.collected_food)

        if self.collected_coins != 0:
            params.putInt('collected_coins', self.collected_coins)

        if self.collected_diamonds != 0:
            params.putInt('collected_diamonds', self.collected_diamonds)

        if self.collected_starpower != 0:
            params.putInt('collected_starpower', self.collected_starpower)

        if self.collected_ethereal != 0:
            params.putInt('collected_ethereal', self.collected_ethereal)

        if self.collected_medals != 0:
            params.putInt('collected_medals', self.collected_medals)

        if self.collected_relics != 0:
            params.putDouble('collected_relics', self.collected_relics)

        if self.collected_keys != 0:
            params.putInt('collected_keys', self.collected_keys)

        if self.parent_monster_id is not None:
            params.putLong('parent_monster', self.parent_monster_id)

        if self.child_monster_id is not None:
            params.putLong('gi_child_monster', self.child_monster_id)

        if self.parent_island_id is not None:
            params.putLong('parent_island', self.parent_island_id)

        if self.child_island_id is not None:
            params.putLong('gi_child_island', self.child_island_id)

        if self.is_training:
            params.putBool('is_training', self.is_training)
            params.putLong('training_start', self.training_start)
            params.putLong('training_completion', self.training_end)

        if self.mega_data is not None:
            params.putSFSObject('megamonster', self.mega_data.to_sfs())

        if self.boxed_eggs:
            params.putUtfString('boxed_eggs', json.dumps([egg.monster.monster_id for egg in self.boxed_eggs]))

        if self.time_to_collect != 0:
            params.putUtfString('collection_type', self.currency_type)
            params.putLong('random_underling_collection_min', self.time_to_collect)
            params.putLong('underling_collection_happiness', self.underling_happy)

        if self.eggTimerStart != -1:
            params.putLong('eggTimerStart', self.eggTimerStart)
        return params

    @staticmethod
    async def create_new_monster(island_id: int, monster_id: int):
        self = PlayerMonster()
        self.monster_id = monster_id
        self.user_island_id = island_id
        self.last_collection = round(time.time() * 1000)

        await self.on_load_complete()

        await self.save()

        logger.info(f'Created new monster(monster={self.monster_id}) for island(user_island_id={self.user_island_id})')

        return self
