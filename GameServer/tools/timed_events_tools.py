import asyncio
import json
import logging
import os
import shutil
import time
import zipfile
from asyncio import create_task

import aiohttp

from GameServer.tools.MSMLocalization import MSMLocalization
from ZewSFS.Client import SFSClient
from ZewSFS.Types import SFSObject
from database import init_database, logger
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


class TimedEventsTools:
    @staticmethod
    async def set_unablalible_monsters_event(timeout=24 * 7):
        for monster in await Monster.load_all():
            if monster.view_in_market or monster.view_in_starmarket:
                continue
            async with TimedEvents() as tm:
                tm.data = json.dumps([{"entity": monster.entity_id}])
                tm.id = 200000 + monster.id
                tm.event_type = 'EntityStoreAvailability'
                tm.event_id = 3
                tm.start_date = round(time.time() * 1000)
                tm.end_date = round(time.time() * 1000) + 1000 * 60 * 60 * timeout
                tm.last_updated = 0
                logging.info(f'Monster {monster.common_name} (id={monster.id}) added for {timeout} hours')


async def main():
    await init_database()
    await TimedEventsTools.set_unablalible_monsters_event(5 * 24)


if __name__ == '__main__':
    asyncio.run(main())
