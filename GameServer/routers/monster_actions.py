import json
import time
import traceback

from Crypto.SelfTest.IO.test_PKCS8 import clear_key

from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject, SFSArray
from database.gene import Gene
from database.monster import Monster
from database.player import PlayerIsland, PlayerStructure, PlayerEgg, PlayerMonster
from database.structure import Structure

router = SFSRouter()


@router.on_request('gs_move_monster')
async def move_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')
    pos_x = params.get('pos_x')
    pos_y = params.get('pos_y')
    volume = params.get('volume')

    async with client.player.get_active_island.get_monster(user_monster_id) as user_monster:
        if user_monster is None:
            return 'Invalid monster ID.'

        if pos_x is not None:
            user_monster.pos_x = pos_x
        if pos_y is not None:
            user_monster.pos_y = pos_y
        if volume is not None:
            user_monster.volume = volume
        else:
            volume = user_monster.volume

    await client.send_extension("gs_update_monster", SFSObject()
                                .putLong('user_monster_id', user_monster_id)
                                .putInt('pos_x', user_monster.pos_x)
                                .putInt('pos_y', user_monster.pos_y)
                                .putDouble('volume', volume))
    return SFSObject().putBool('success', True)


@router.on_request('gs_flip_monster')
async def flip_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')
    flipped = params.get('flipped')

    async with client.player.get_active_island.get_monster(user_monster_id) as user_monster:
        if user_monster is None:
            return 'Invalid monster ID.'

        if flipped is not None:
            user_monster.flip = bool(flipped)
        else:
            user_monster.flip = not user_monster.flip

    await client.send_extension("gs_update_monster", SFSObject()
                                .putLong('user_monster_id', user_monster_id)
                                .putInt('flip', user_monster.flip))
    return SFSObject().putBool('success', True)


@router.on_request('gs_name_monster')
async def name_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')
    name = params.get('name')

    async with client.player.get_active_island.get_monster(user_monster_id) as user_monster:
        if user_monster is None:
            return 'Invalid monster ID.'

        user_monster.name = name

    await client.send_extension("gs_update_monster", SFSObject()
                                .putLong('user_monster_id', user_monster_id)
                                .putInt('flip', user_monster.name))
    return SFSObject().putBool('success', True)


@router.on_request('gs_mute_monster')
async def mute_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')
    muted = params.get('muted')

    async with client.player.get_active_island.get_monster(user_monster_id) as user_monster:
        if user_monster is None:
            return 'Invalid monster ID.'

        if muted is not None:
            user_monster.muted = bool(muted)
        else:
            user_monster.muted = not user_monster.muted

    await client.send_extension("gs_update_monster", SFSObject()
                                .putLong('user_monster_id', user_monster_id)
                                .putInt('muted', int(user_monster.muted)))
    return SFSObject().putBool('success', True)


@router.on_request('gs_mega_monster_message')
async def mega_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')
    mega_enable = params.get('mega_enable')
    permanent = params.get('permanent', False)

    async with client.player.get_active_island.get_monster(user_monster_id) as user_monster:
        if user_monster is None:
            return 'Invalid monster ID.'

        mega_data = user_monster.mega_data

        if mega_enable is not None:
            if mega_data.permega or mega_data.finished_at > time.time() * 1000:
                mega_data.enabled = mega_enable
            else:
                return 'Monster don\'t have a mega'
        else:
            if mega_data.permega:
                return 'You don\'t needed to buy this stuff'
            else:
                if not await client.player.check_prices(diamonds=20 if permanent else 2):
                    return 'You don\'t have enough diamonds'

                mega_data.enabled = True
                mega_data.permega = permanent
                if not permanent:
                    mega_data.started_at = round(time.time() * 1000)
                    mega_data.finished_at = round((time.time() + 60 * 60 * 24) * 1000)

    await client.send_extension("gs_update_monster", SFSObject()
                                .putLong('user_monster_id', user_monster_id)
                                .putSFSObject('megamonster', mega_data.to_sfs())
                                .putSFSArray("properties", client.player.get_properties()))
    return SFSObject().putBool('success', True)


@router.on_request('gs_sell_monster')
async def sell_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')

    active_island = client.player.get_active_island
    user_monster = active_island.get_monster(user_monster_id)
    if user_monster is None:
        return 'Invalid monster ID.'

    if not active_island.is_gold_island():
        if active_island.is_ethereal_island():
            await client.player.add_currency('eth', round(user_monster.monster.cost_eth_currency * 0.75))
        elif active_island.is_amber_island():
            await client.player.add_currency('relics', round(user_monster.monster.cost_relics * 0.75))
        else:
            await client.player.add_currency('coins', round(user_monster.monster.cost_coins * 0.75))

    if user_monster.child_monster_id is not None:
        cisland: 'PlayerIsland' = client.player.get_island(user_monster.child_island_id)
        cmonster = cisland.get_monster(user_monster.child_monster_id)
        try:
            if cmonster.monster_id not in cisland.monsters_sold:
                cisland.monsters_sold.append(cmonster.monster_id)

            cisland.monsters.remove(cmonster)
            await cmonster.remove()
            await client.send_extension("gs_update_sold_monsters", SFSObject()
                                        .putLong("island_id", cisland.id)
                                        .putUtfString("monsters_sold", json.dumps(list(cisland.monsters_sold))))
            await client.send_extension("gs_sell_monster", SFSObject()
                                        .putBool('success', True)
                                        .putLong('user_gi_monster_id', user_monster.child_monster_id)
                                        .putSFSArray('properties', client.player.get_properties()))
        except:
            traceback.print_exc()

    if user_monster.parent_monster_id is not None:
        pisland: 'PlayerIsland' = client.player.get_island(user_monster.parent_island_id)
        async with pisland.get_monster(user_monster.parent_monster_id) as pmonster:
            pmonster.child_monster_id = None
            pmonster.child_island_id = None

    client.player.get_active_island.monsters.remove(user_monster)
    await user_monster.remove()

    return SFSObject().putBool('success', True).putLong('user_monster_id', user_monster_id).putSFSArray('properties',
                                                                                                        client.player.get_properties())


@router.on_request('gs_feed_monster')
async def feed_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')
    muted = params.get('muted')

    async with client.player.get_active_island.get_monster(user_monster_id) as user_monster:
        if user_monster is None:
            return 'Invalid monster ID.'

        mlevel = user_monster.monster.levels[user_monster.level - 1]
        if mlevel.level >= len(user_monster.monster.levels):
            return 'This monster is already at max level!'

        if not await client.player.check_prices(food=mlevel.food):
            return 'You don\'t have enough resources to feed this monster!'

        user_monster.timed_fed += 1
        user_monster.last_feeding = round(time.time() * 1000)
        if user_monster.timed_fed >= 4:
            user_monster.timed_fed = 0
            user_monster.level += 1

    await client.send_extension("gs_update_monster", SFSObject()
                                .putLong('user_monster_id', user_monster_id)
                                .putInt('level', user_monster.level)
                                .putInt('times_fed', user_monster.timed_fed)
                                .putSFSArray('properties', client.player.get_properties()))
    return SFSObject().putBool('success', True)


@router.on_request('gs_collect_monster')
async def collect_monster(client: SFSServerClient, params: SFSObject):
    user_monster_id = params.get('user_monster_id')
    muted = params.get('muted')

    async with client.player.get_active_island.get_monster(user_monster_id) as user_monster:
        if user_monster is None:
            return 'Invalid monster ID.'

        mlevel = user_monster.monster.levels[user_monster.level - 1]

        if not client.player.get_active_island.is_ethereal_island():
            reward = round(mlevel.coins * (time.time() * 1000 - user_monster.last_collection) / 1000 / 60)
            reward_type = 'coins'
            if reward > mlevel.max_coins:
                reward = mlevel.max_coins
            user_monster.collected_coins = 0
        else:
            reward = round(mlevel.ethereal_currency * (time.time() * 1000 - user_monster.last_collection) / 1000 / 60)
            reward_type = 'ethereal_currency'
            if reward > mlevel.max_ethereal:
                reward = mlevel.max_ethereal
            user_monster.collected_ethereal = 0

        await client.player.add_currency(reward_type, reward)
        user_monster.last_collection = round(time.time() * 1000)

    update_response = SFSObject()
    update_response.putLong('user_monster_id', user_monster_id)
    update_response.putLong('last_collection', user_monster.last_collection)
    update_response.putInt('collected_coins', user_monster.collected_coins)
    update_response.putSFSArray('properties', client.player.get_properties())

    collect_response = SFSObject().putBool('success', True)
    collect_response.putInt(reward_type, reward)
    collect_response.putLong('user_monster_id', user_monster_id)

    await client.send_extension("gs_update_monster", update_response)
    await client.send_extension("gs_collect_monster", collect_response)


@router.on_request('gs_place_on_gold_island')
async def place_on_gold_island(client: SFSServerClient, params: SFSObject):
    parent_monster_id = params.get('user_monster_id')
    parent_island_id = params.get('user_parent_island_id')
    pos_x = params.get('pos_x')
    pos_y = params.get('pos_y')
    flip = params.get('flip')

    parent_island: 'PlayerIsland' = client.player.get_island(parent_island_id)
    if parent_island is None:
        return 'Invalid island ID.'

    async with parent_island.get_monster(parent_monster_id) as parent_monster:
        if parent_monster is None:
            return 'Invalid monster ID.'

        active_island: 'PlayerIsland' = client.player.get_active_island

        if parent_island.is_gold_island() or parent_island.is_tribal_island() or not active_island.is_gold_island() or parent_monster.monster_id not in [
            m.monster async for m in active_island.island.load_monsters()]:
            return 'Invalid island or monster.'

        if parent_monster.child_monster_id is not None:
            return 'Monster already has a child.'

        if parent_monster.level < 15:
            return 'Monster must be level 15 to breed.'

        if all([x in parent_monster.monster.common_name.lower() for x in ('wubbox', 'epic')]):
            monster = await Monster.load_by_id(670)
        else:
            monster = parent_monster.monster

        async with await PlayerMonster.create_new_monster(active_island.id, monster.id) as user_monster:
            user_monster.pos_x = pos_x
            user_monster.pos_y = pos_y
            user_monster.flip = flip
            user_monster.parent_monster_id = parent_monster.id
            user_monster.parent_island_id = parent_island.id
            user_monster.level = parent_monster.level

        parent_monster.child_monster_id = user_monster.id
        parent_monster.child_island_id = active_island.id

        if parent_monster.monster.id not in active_island.monsters_sold:
            async with active_island:
                active_island.monsters_sold.append(parent_monster.monster.id)

    response = SFSObject()
    response.putBool('success', True)
    response.putSFSObject('monster', await user_monster.to_sfs_object())
    response.putSFSArray('properties', client.player.get_properties())
    response.putLong('user_monster_id', parent_monster_id)

    return response
