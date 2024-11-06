import asyncio
import logging

from GameServer import GameServer
from database import init_database

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s/%(name)s:\t%(message)s'
)


async def main():
    await init_database()
    await GameServer.start()


if __name__ == '__main__':
    asyncio.run(main())
