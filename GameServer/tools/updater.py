import asyncio
import json
import logging

import aiohttp

from ZewSFS.Client import SFSClient
from ZewSFS.Types import SFSObject
from database import init_database
from database.daily_cumulative_login import DailyCumulativeLogin
from database.flip_board import FlipBoard, FlipLevel
from database.gene import Gene, AttunerGene
from database.island import Island, IslandMonster, IslandStructure, IslandThemeData
from database.level import Level
from database.monster import Monster, MonsterCostume, FlexEggs, RareMonsterData, EpicMonsterData, MonsterHome, \
    MonsterLevel
from database.scratch_offer import ScratchOffer
from database.store import StoreItem, StoreGroup, StoreCurrency, StoreReplacement
from database.structure import Structure
from database.stuff import NucleusReward, EntityAltCosts, TitanSoulLevel, TimedEvents, GameSettings

logging.basicConfig(level=logging.DEBUG)


class Updater:
    username: str
    password: str
    login_type: str
    client_version: str
    access_key: str

    access_token: str
    user_game_id: str

    server_ip: str
    content_url: str

    async def _init(self, username: str, password: str, login_type: str, client_version: str, access_key: str):
        self.username = username
        self.password = password
        self.login_type = login_type
        self.client_version = client_version
        self.access_key = access_key

        async with aiohttp.ClientSession() as session:
            async with session.post('https://auth.bbbgame.net/auth/api/token', data={
                "g": 1,
                "u": self.username,
                "p": self.password,
                "t": self.login_type,
                "auth_version": "2.0.0",
            }) as resp:
                auth_response = json.loads(await resp.text())
                if not auth_response.get("ok"):
                    raise RuntimeError(auth_response.get("message"))

                self.access_token = auth_response.get("access_token")
                self.user_game_id = auth_response.get("user_game_id")[0]

            async with session.post('https://msm-auth.bbbgame.net/pregame_setup.php', headers={"Authorization": self.access_token}, data={
                'client_version': self.client_version,
                'access_key': self.access_key,
                "device_model": "iPhone 13 Pro",
                "device_vendor": "Apple",
                "platform": 'ios',
            }) as resp:
                pregame_response = json.loads(await resp.text())
                if not pregame_response.get("ok"):
                    raise RuntimeError(pregame_response.get("message"))

                self.server_ip = pregame_response.get("serverIp")
                self.content_url = pregame_response.get("contentUrl")

            return self


class DatabaseUpdater(Updater):
    sfs_client: SFSClient

    async def init(self, username: str, password: str, login_type: str, client_version: str, access_key: str):
        await self._init(username, password, login_type, client_version, access_key)

        self.sfs_client = SFSClient()
        await self.sfs_client.connect(self.server_ip, 9933)

        login_params = SFSObject()
        login_params.putUtfString("access_key", self.access_key)
        login_params.putUtfString("token", self.access_token)
        login_params.putUtfString("last_update_version", '')
        login_params.putUtfString("client_os", '18.1')
        login_params.putUtfString("client_platform", 'ios')
        login_params.putUtfString("client_device", 'iPad8,6')
        login_params.putUtfString("raw_device_id", '56B30EF0-DBD1-5755-9040-B649B587DE1E')
        login_params.putUtfString("client_version", self.client_version)

        await self.sfs_client.send_login_request("MySingingMonsters", self.user_game_id, "", login_params)
        while 1:
            cmd, params = await self.sfs_client.wait_requests(["gs_initialized", "gs_player_banned", "gs_client_version_error", "gs_display_generic_message", "game_settings"])
            if cmd == "gs_initialized":
                return True
            elif cmd == "gs_player_banned":
                raise RuntimeError(params.get("reason"))
            elif cmd == "gs_client_version_error":
                raise RuntimeError("Client version is outdated.")
            elif cmd == "gs_display_generic_message":
                raise RuntimeError("Generic message: " + params.getUtfString("message"))
            elif cmd == 'game_settings' and 'user_game_settings' in params:
                for data in params.get('user_game_settings'):
                    obj = await GameSettings.from_sfs_object(data)
                    await obj.update_if_exists()
                    await obj.save()

    async def update_genes(self):
        response = await self.sfs_client.request('db_gene')
        for data in response.get('genes_data'):
            obj = await Gene.from_sfs_object(data)
            await obj.save()

    async def update_levels(self):
        response = await self.sfs_client.request('db_level')
        for data in response.get('level_data'):
            obj = await Level.from_sfs_object(data)
            await obj.save()

    async def update_scratch_offers(self):
        response = await self.sfs_client.request('db_scratch_offs')
        for data in response.get('scratch_offs'):
            obj = await ScratchOffer.from_sfs_object(data)
            await obj.save()

    async def update_monsters(self):
        async def monster_task(data):
            obj = await Monster.from_sfs_object(data)
            for level in data.get('levels', []):
                async with await MonsterLevel.from_sfs_object(level) as lvl:
                    lvl.monster_id = obj.id
                    await lvl.update_if_exists()
            await obj.save()

        response = await self.sfs_client.request('db_monster')
        await asyncio.gather(*[asyncio.create_task(monster_task(data)) for data in response.get('monsters_data')])

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_monster')
            await asyncio.gather(*[asyncio.create_task(monster_task(data)) for data in response.get('monsters_data')])

    async def update_structures(self):
        response = await self.sfs_client.request('db_structure')
        for data in response.get('structures_data'):
            obj = await Structure.from_sfs_object(data)
            await obj.save()

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_structure')
            for data in response.get('structures_data'):
                obj = await Structure.from_sfs_object(data)
                await obj.save()

    async def update_islands(self):
        async def update_i_task(dat):
            obj = await Island.from_sfs_object(dat)
            await obj.save()

            await asyncio.gather(*[asyncio.create_task(update_c_task(IslandMonster, monster, obj.id)) for monster in dat.get('monsters')])
            await asyncio.gather(*[asyncio.create_task(update_c_task(IslandStructure, structure, obj.id)) for structure in dat.get('structures')])

        async def update_c_task(cls, dat, iid):
            x_obj = await cls.from_sfs_object(dat)
            x_obj.island_id = iid
            await x_obj.update_if_exists()
            await x_obj.save()

        response = await self.sfs_client.request('db_island_v2')
        await asyncio.gather(*[asyncio.create_task(update_i_task(data)) for data in response.get('islands_data')])

    async def update_island_themes(self):
        response = await self.sfs_client.request('db_island_themes')
        for data in response.get('island_theme_data'):
            obj = await IslandThemeData.from_sfs_object(data)
            await obj.save()

    async def update_store(self):
        response = await self.sfs_client.request('db_store_v2')
        for data in response.get('store_item_data'):
            obj = await StoreItem.from_sfs_object(data)
            await obj.save()
        for data in response.get('store_group_data'):
            obj = await StoreGroup.from_sfs_object(data)
            await obj.save()
        for data in response.get('store_currency_data'):
            obj = await StoreCurrency.from_sfs_object(data)
            await obj.save()

    async def update_costumes(self):
        response = await self.sfs_client.request('db_costumes')
        for data in response.get('costume_data'):
            obj = await MonsterCostume.from_sfs_object(data)
            await obj.save()

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_costumes')
            for data in response.get('costume_data'):
                obj = await MonsterCostume.from_sfs_object(data)
                await obj.save()

    async def update_flip_boards(self):
        response = await self.sfs_client.request('gs_flip_boards')
        for data in response.get('flip_boards'):
            obj = await FlipBoard.from_sfs_object(data)
            await obj.save()

    async def update_flip_levels(self):
        response = await self.sfs_client.request('gs_flip_levels')
        for data in response.get('flip_levels'):
            obj = await FlipLevel.from_sfs_object(data)
            await obj.save()

    async def update_daily_cumulative_login(self):
        response = await self.sfs_client.request('db_daily_cumulative_login')
        for data in response.get('daily_cumulative_login_data'):
            obj = await DailyCumulativeLogin.from_sfs_object(data)
            await obj.save()

    async def update_flexeggdefs(self):
        response = await self.sfs_client.request('db_flexeggdefs')
        for data in response.get('flex_egg_def_data'):
            obj = await FlexEggs.from_sfs_object(data)
            await obj.save()

    async def update_attuner_genes(self):
        response = await self.sfs_client.request('db_attuner_gene')
        for data in response.get('attuner_gene_data'):
            obj = await AttunerGene.from_sfs_object(data)
            await obj.save()

    async def update_loot(self):
        response = await self.sfs_client.request('db_loot')
        # for data in response.get('loot_data'):
        #     obj = await AttunerGene.from_sfs_object(data)
        #     await obj.save()

    async def update_nucleus_reward(self):
        response = await self.sfs_client.request('db_nucleus_reward')
        for data in response.get('nucleus_reward_data'):
            obj = await NucleusReward.from_sfs_object(data)
            await obj.save()

    async def update_alt_costs(self):
        response = await self.sfs_client.request('db_entity_alt_costs')
        for data in response.get('entity_alt_data'):
            obj = await EntityAltCosts.from_sfs_object(data)
            await obj.save()

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_entity_alt_costs')
            for data in response.get('entity_alt_data'):
                obj = await EntityAltCosts.from_sfs_object(data)
                await obj.save()

    async def update_store_replacements(self):
        response = await self.sfs_client.request('db_store_replacements')
        for data in response.get('store_replacement_data'):
            obj = await StoreReplacement.from_sfs_object(data)
            await obj.save()

    async def update_titan_souls_levels(self):
        response = await self.sfs_client.request('db_titansoul_levels')
        for data in response.get('titansoul_level_data'):
            obj = await TitanSoulLevel.from_sfs_object(data)
            await obj.save()

    async def update_timed_events(self):
        response = await self.sfs_client.request('gs_timed_events')
        for data in response.get('timed_event_list'):
            obj = await TimedEvents.from_sfs_object(data)
            await obj.save()

    async def update_rare_monster_data(self):
        response = await self.sfs_client.request('gs_rare_monster_data')
        for data in response.get('rare_monster_data'):
            obj = await RareMonsterData.from_sfs_object(data)
            await obj.save()

    async def update_epic_monster_data(self):
        response = await self.sfs_client.request('gs_epic_monster_data')
        for data in response.get('epic_monster_data'):
            obj = await EpicMonsterData.from_sfs_object(data)
            await obj.save()

    async def update_monster_home_data(self):
        response = await self.sfs_client.request('gs_monster_island_2_island_data')
        for data in response.get('monster_island_2_island_data'):
            obj = await MonsterHome.from_sfs_object(data)
            await obj.update_if_exists()
            await obj.save()

    async def update_cant_breed(self):
        response = await self.sfs_client.request('gs_cant_breed')
        async with GameSettings() as obj:
            obj.key = 'cant_breed_monsters'
            obj.value = json.dumps(response.get('monsterIds'))
            await obj.update_if_exists()

    async def test(self):
        response = await self.sfs_client.request('gs_move_structure', SFSObject().putLong('user_structure_id', 3).putInt('pos_x', 200).putInt('pos_y', 50))
        await self.sfs_client.read_response()
        await self.sfs_client.read_response()
        await self.sfs_client.read_response()


async def main():
    await init_database()
    updater = DatabaseUpdater()
    await updater.init('jp34cx4h8w2p', 'nvmgj529rzxgnhctvh2t', 'anon', '4.5.0', '58ffe1b7-1620-4534-982a-9f71bdb476fe')
    # await updater.test()
    await updater.update_monsters()
    return
    await updater.update_genes()
    await updater.update_levels()
    await updater.update_scratch_offers()
    await updater.update_structures()
    await updater.update_islands()
    await updater.update_island_themes()
    await updater.update_store()
    await updater.update_costumes()
    await updater.update_flip_boards()
    await updater.update_flip_levels()
    await updater.update_daily_cumulative_login()
    await updater.update_flexeggdefs()
    await updater.update_attuner_genes()
    await updater.update_loot()
    await updater.update_nucleus_reward()
    await updater.update_alt_costs()
    await updater.update_store_replacements()
    await updater.update_titan_souls_levels()
    await updater.update_timed_events()
    await updater.update_rare_monster_data()
    await updater.update_epic_monster_data()
    await updater.update_monster_home_data()
    await updater.update_cant_breed()


if __name__ == '__main__':
    asyncio.run(main())
