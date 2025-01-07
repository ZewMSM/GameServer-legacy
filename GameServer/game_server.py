import asyncio
import logging
import time

from GameServer.routers.player_actions import router as player_actions_router
from GameServer.routers.island_actions import router as island_actions_router
from GameServer.routers.egg_actions import router as egg_actions_router
from GameServer.routers.monster_actions import router as monster_actions_router
from GameServer.routers.structure_actions import router as structure_actions_router
from GameServer.routers.static_data import router as static_data_router
from GameServer.tools.utils import decrypt_token, generate_bind_link
from ZewSFS import SFSServer
from ZewSFS.Server import SFSServerClient, UnhandledRequest
from ZewSFS.Types import SFSObject, SFSArray
from ZewSFS.Utils import compile_packet
from config import GameConfig
from database.player import Player
from database.stuff import GameSettings

from database.flip_board import FlipBoard, FlipLevel
from database.gene import Gene, AttunerGene
from database.island import Island, IslandThemeData
from database.level import Level
from database.monster import Monster, MonsterCostume, FlexEggs, EpicMonsterData, RareMonsterData, MonsterHome
from database.player import Player
from database.scratch_offer import ScratchOffer
from database.store import StoreItem, StoreGroup, StoreCurrency, StoreReplacement
from database.structure import Structure
from database.stuff import NucleusReward, EntityAltCosts, TitanSoulLevel, TimedEvents, GameSettings

logger = logging.getLogger('GameServer/Main')


class GameServer:
    server: 'SFSServer' = SFSServer()

    @staticmethod
    async def update_cached_databases():
        await asyncio.gather(
            asyncio.create_task(Island.load_all(cached=False)),
            asyncio.create_task(IslandThemeData.load_all(cached=False)),
            asyncio.create_task(Level.load_all(cached=False)),
            asyncio.create_task(Monster.load_all(cached=False)),
            asyncio.create_task(MonsterCostume.load_all(cached=False)),
            asyncio.create_task(RareMonsterData.load_all(cached=False)),
            asyncio.create_task(EpicMonsterData.load_all(cached=False)),
            asyncio.create_task(MonsterHome.load_all(cached=False)),
            asyncio.create_task(FlexEggs.load_all(cached=False)),
            asyncio.create_task(ScratchOffer.load_all(cached=False)),
            asyncio.create_task(StoreGroup.load_all(cached=False)),
            asyncio.create_task(StoreItem.load_all(cached=False)),
            asyncio.create_task(StoreCurrency.load_all(cached=False)),
            asyncio.create_task(StoreReplacement.load_all(cached=False)),
            asyncio.create_task(Structure.load_all(cached=False)),
            asyncio.create_task(NucleusReward.load_all(cached=False)),
            asyncio.create_task(EntityAltCosts.load_all(cached=False)),
            asyncio.create_task(TimedEvents.load_all(cached=False)),
            asyncio.create_task(TitanSoulLevel.load_all(cached=False)),
        )

    @staticmethod
    async def cache_static_data():
        async def cache_task(name):
            request = SFSObject()
            request.putUtfString("c", name)
            request.putInt("r", -1)
            request.putSFSObject("p", await static_data_router.request_handlers.get(name)(None, None))

            packet = SFSObject()
            packet.putByte("c", 1)
            packet.putShort("a", 13)
            packet.putSFSObject("p", request)

            static_data_router.cached_requests[name] = compile_packet(packet)

        await asyncio.gather(
            *[cache_task(name) for name in static_data_router.cached_requests]
        )

    @staticmethod
    async def load_player_object(client: SFSServerClient):
        bbb_id = client.get_arg('bbb_id')
        player = await Player.load_by_id(bbb_id)
        if player is None:
            player = Player()
            player.id = bbb_id
            await player.create_new_player()

        player.last_login = time.time()
        await player.save()
        client.set_arg('player', player)
        client.player = player

    @staticmethod
    async def send_generic_message(sender, message: str, force_logout=False):
        await sender.send_extension("gs_display_generic_message",
                                    SFSObject().putBool("force_logout", force_logout).putUtfString("msg", message))

    @staticmethod
    async def send_banned_message(sender, message: str):
        await sender.send_extension("gs_player_banned", SFSObject().putUtfString("reason", message))

    @staticmethod
    async def error_callback(client: 'SFSServerClient', err: Exception, tb: str):
        if isinstance(err, UnhandledRequest):
            await client.send_extension(err.cmd, SFSObject().putBool('success', False))
        else:
            logger.error(tb)

    @staticmethod
    async def login_callback(client: 'SFSServerClient', username, password, auth_params: SFSObject):
        token: str = auth_params.get("token")
        access_key = auth_params.get("access_key")
        client_os = auth_params.get("client_os")
        client_platform = auth_params.get("client_platform")
        client_version = auth_params.get("client_version")
        bbb_id = None

        if (access_key is None
                or client_version is None
                or client_version not in GameConfig.allowed_versions
                or GameConfig.allowed_versions.get(client_version, None) != access_key):
            await GameServer.send_banned_message(client, 'INVALID_VERSION_MESSAGE')
            return False

        # if token.startswith('ID:'):
        #     bbb_id = int(token.split(':')[1])
        # else:

        decrypted_token = decrypt_token(token)
        if decrypted_token is not None and decrypted_token.get('user_game_ids', [None])[0] == username:
            bbb_id = decrypted_token.get('account_id', None)

        if bbb_id is None:
            await GameServer.send_banned_message(client, 'INVALID_BBB_ID')
            return False

        if not decrypted_token.get('can_play', False):
            bind_link = generate_bind_link(bbb_id)
            await client.send_extension("gs_client_version_error", SFSObject()
                                        .putBool("success", False)
                                        .putUtfString("message", "LINK_NEEDED")
                                        .putSFSArray("urls", SFSArray()
                                                     .addSFSObject(SFSObject()
                                                                   .putUtfString("platform", "android")
                                                                   .putUtfString("url", bind_link)
                                                                   )
                                                     .addSFSObject(SFSObject()
                                                                   .putUtfString("platform", "ios")
                                                                   .putUtfString("url", bind_link)
                                                                   )
                                                     )
                                        )
            return False

        client.set_arg('username', username)
        client.set_arg('client_version', client_version)
        client.set_arg('client_os', client_os)
        client.set_arg('client_platform', client_platform)
        client.set_arg('bbb_id', bbb_id)
        client.set_arg('start_time', round(time.time()))
        client.set_arg('player', None)

        game_settings = SFSArray()
        for setting in await GameSettings.load_all():
            game_settings.addSFSObject(await setting.to_sfs_object())

        asyncio.create_task(GameServer.load_player_object(client))

        await client.send_extension('game_settings', SFSObject().putSFSArray('user_game_settings', game_settings))
        await GameServer.send_generic_message(client, f'Welcome to ZewMSM!\n\nServer online is: {len(GameServer.server.clients)}!')
        await client.send_extension('gs_initialized', SFSObject().putLong('bbb_id', bbb_id))
        return True

    @staticmethod
    async def start():
        GameServer.server.error_callback = GameServer.error_callback
        GameServer.server.login_callback = GameServer.login_callback

        await GameServer.cache_static_data()

        GameServer.server.include_router(static_data_router)
        GameServer.server.include_router(player_actions_router)
        GameServer.server.include_router(island_actions_router)
        GameServer.server.include_router(structure_actions_router)
        GameServer.server.include_router(egg_actions_router)
        GameServer.server.include_router(monster_actions_router)

        await GameServer.update_cached_databases()
        await GameServer.server.serve_forever()
