import json
import time

from Crypto.SelfTest.IO.test_PKCS8 import clear_key

from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject, SFSArray
from database.gene import Gene
from database.monster import Monster
from database.player import PlayerIsland, PlayerStructure, PlayerEgg, PlayerMonster
from database.structure import Structure

router = SFSRouter()


@router.on_request('gs_viewed_egg')
async def viewedEgg(client: SFSServerClient, params: SFSObject):
    egg_id = int(params.get('user_egg_id'))
    egg = client.player.get_active_island.get_egg(egg_id)
    await egg.mark_as_viewed()

    isl = await egg.get_island()

    await client.send_extension('gs_update_sold_monsters', SFSObject()
                                .putLong('island_id', isl.id)
                                .putUtfString('monsters_sold', json.dumps(list(isl.monster_sold))))

    return SFSObject().putBool('success', True)


@router.on_request('gs_buy_egg')
async def buy_egg(client: SFSServerClient, params: SFSObject):
    structure_id = params.get('structure_id', params.get('nursery_id', 0))

    island: 'PlayerIsland' = client.player.get_active_island

    if structure_id == 0:
        nurseries = list(island.get_structures_by_type('NURSERY'))

        for nur in nurseries:
            if not any([egg.user_structure_id == nur.id for egg in island.eggs]):
                structure_id = nur.id
                break

        if structure_id == 0:
            return 'All nurseries are full!'
    else:
        if any([egg.user_structure.id == structure_id for egg in island.eggs]):
            return 'This egg already exists!'

    structure = island.get_structure(structure_id)
    if structure is None:
        return 'Invalid structure ID.'

    monster_id = params.get('monster_id')
    monster = await Monster.load_by_id(monster_id)

    if monster is None:
        return 'Invalid monster ID.'

    if monster_id not in [m.monster async for m in island.island.load_monsters()]:
        return 'Monster not available!'

    if not await client.player.check_prices(obj=monster, eth_instead_of_coins=island.is_ethereal_island()):
        return 'You don\'t have enough currency to buy this monster.'

    egg = await PlayerEgg.create_new_egg(island.id, structure_id, monster_id, monster.cost_diamonds > 0)
    await egg.mark_as_viewed()

    return SFSObject().putSFSObject('user_egg', await egg.to_sfs_object()).putBool('success', True).putSFSArray('properties', client.player.get_properties())



@router.on_request('gs_hatch_egg')
async def hatchEgg(client: SFSServerClient, params: SFSObject):
    egg_id = int(params.get('user_egg_id'))
    pos_x = int(params.get('pos_x'))
    pos_y = int(params.get('pos_y'))
    flip = int(params.get('flip'))
    store_in_hotel = params.get('store_in_hotel', False)
    name = params.get('name', 'ZewMSM')

    island: 'PlayerIsland' = client.player.get_active_island
    direct_place = True

    user_egg = island.get_egg(egg_id)
    if user_egg is None:
        monster = await Monster.load_by_id(egg_id)
        if monster is None or egg_id not in [m.monster async for m in island.island.load_monsters()]:
            return 'Invalid egg ID.'
        if not await client.player.check_prices(obj=monster, eth_instead_of_coins=island.is_ethereal_island()):
            return 'You don\'t have enough currency to buy this monster.'
        direct_place = True

        if monster.id not in island.monsters_sold_ids:
            async with island:
                island.monsters_sold_ids.append(monster.id)
    else:
        if user_egg.hatches_on > round(time.time() * 1000):
            return 'This egg is not hatched!'

        monster = user_egg.monster

    async with await PlayerMonster.create_new_monster(island.id, monster.id) as user_monster:
        user_monster.pos_x = pos_x
        user_monster.pos_y = pos_y
        user_monster.flip = flip
        user_monster.name = name
        user_monster.in_hotel = store_in_hotel
    client.player.get_active_island.monsters.append(user_monster)
    if user_egg is not None:
        client.player.get_active_island.eggs.remove(user_egg)
        await user_egg.remove()

    response = SFSObject()
    response.putBool('success', True)
    response.putSFSObject('monster', await user_monster.to_sfs_object())
    response.putSFSArray('properties', client.player.get_properties())
    response.putBool('directPlace', direct_place)
    response.putLong('user_egg_id', egg_id)
    response.putLong('island', island.id)
    response.putBool('create_in_storage', store_in_hotel)

    return response