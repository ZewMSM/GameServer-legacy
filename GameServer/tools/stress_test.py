import json
import logging
import random

import aiohttp

from ZewSFS import SFSClient
from ZewSFS.Types import SFSObject


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s/%(name)s:\t%(message)s'
)

logger = logging.getLogger('StressTest')


class TestClient:
    sfs_client: SFSClient
    user_id: int

    async def init(self, user_id: int):
        logger.info(f'Player #{user_id}: Connecting to server...')
        self.sfs_client = SFSClient()
        self.user_id = user_id
        await self.sfs_client.connect('127.0.0.1', 9933)

        login_params = SFSObject()
        login_params.putUtfString("access_key", 'nigga')
        login_params.putUtfString("token", f'ID:{user_id}')
        login_params.putUtfString("last_update_version", '')
        login_params.putUtfString("client_os", '18.1')
        login_params.putUtfString("client_platform", 'ios')
        login_params.putUtfString("client_device", 'iPad8,6')
        login_params.putUtfString("raw_device_id", '56B30EF0-DBD1-5755-9040-B649B587DE1E')
        login_params.putUtfString("client_version", '4.6.1')

        await self.sfs_client.send_login_request("MySingingMonsters", f'ID:{user_id}', "", login_params)
        logger.info(f'Player #{user_id}: Logging...')
        while 1:
            cmd, params = await self.sfs_client.wait_requests(["gs_initialized", "gs_player_banned", "gs_client_version_error", "gs_display_generic_message", "game_settings"])
            if cmd == "gs_initialized":
                logger.info(f'Player #{user_id}: Logged!')
                return self
            elif cmd == "gs_player_banned":
                raise RuntimeError(params.get("reason"))
            elif cmd == "gs_client_version_error":
                raise RuntimeError("Client version is outdated.")
            elif cmd == "gs_display_generic_message":
                raise RuntimeError("Generic message: " + params.getUtfString("message"))



    async def ask_monsters(self):
        logger.info(f'Player #{self.user_id}: Requesting monsters...')
        resp = len((await self.sfs_client.request("db_monster", SFSObject())).get('monsters_data'))
        logger.info(f'Player #{self.user_id}: Got {resp} monsters.')

    async def ask_player(self):
        logger.info(f'Player #{self.user_id}: Requesting player...')
        await self.sfs_client.request("gs_player", SFSObject())
        logger.info(f'Player #{self.user_id}: Got player.')


async def single_task(user_id: int):
    try:
        client = await TestClient().init(user_id)
        await client.ask_player()
    except:
        logger.info(f'Player #{user_id}: Kicked')

async def main():
    while 1:
        await asyncio.gather(*[single_task(i) for i in range(500)])

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())