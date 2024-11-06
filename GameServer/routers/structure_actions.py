import time

from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject, SFSArray
from database.player import PlayerIsland, PlayerStructure
from database.structure import Structure

router = SFSRouter()


@router.on_request('gs_buy_structure')
async def buy_structure(client: SFSServerClient, params: SFSObject):
    structure_id = params.get('structure_id')
    pos_x = params.get('pos_x')
    pos_y = params.get('pos_y')
    flip = params.get('flip')
    scale = params.get('scale')

    active_island: PlayerIsland = client.player.get_active_island
    if active_island.is_tribal_island() or active_island.is_composer_island() or active_island.is_gold_island():
        return 'You cannot place structures on this island.'

    structure = await Structure.load_by_id(structure_id)

    if structure.structure_type == 'awakener':  # TODO: Add awakeners!
        return "ZewMSM don't supports awakeners right not...\nStay tuned!"

    if structure.premium and not client.player.premium:
        return 'This structure is premium only.'

    if active_island.has_max_structures(structure.structure_type):
        return 'You have reached the maximum number of this structure type.'

    if not await client.player.check_prices(obj=structure, eth_instead_of_coins=active_island.is_ethereal_island()):
        return 'You don\'t have enough currency to buy this island.'

    await client.player.add_currency('xp', structure.xp)

    async with await PlayerStructure.create_new_structure(active_island.id, structure_id, pos_x, pos_y, True) as user_structure:
        user_structure.flip = bool(flip)
        user_structure.scale = scale
        user_structure.is_complete = True
        user_structure.is_upgrading = None
        user_structure.building_completed = -1
        user_structure.date_created = round(time.time()) * 1000
        user_structure.last_collection = round(time.time()) * 1000

    active_island.structures.append(user_structure)

    response = SFSObject()
    response.putBool('success', True)
    response.putSFSArray('properties', client.player.get_properties())
    response.putSFSObject('user_structure', await user_structure.to_sfs_object())

    await client.send_extension("gs_update_properties", SFSObject().putSFSArray('properties', client.player.get_properties()))
    return response


@router.on_request('gs_move_structure')
async def move_structure(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')
    pos_x = params.get('pos_x')
    pos_y = params.get('pos_y')
    scale = params.get('scale')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if user_structure.structure.structure_type in ('castle', 'obstacle'):
            return 'This structure cannot be moved.'

        user_structure.pos_x = pos_x
        user_structure.pos_y = pos_y
        user_structure.scale = scale

    response = SFSObject()
    response.putLong('user_structure_id', user_structure_id)
    response.putSFSArray('properties', SFSArray()
                         .addSFSObject(SFSObject().putInt('pos_x', pos_x))
                         .addSFSObject(SFSObject().putInt('pos_y', pos_y)))

    await client.send_extension("gs_move_structure", SFSObject().putBool('success', True))
    await client.send_extension("gs_update_structure", response)


@router.on_request('gs_mute_structure')
async def mute_structure(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')
    muted = params.get('muted')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if muted is not None:
            user_structure.muted = bool(muted)
        else:
            user_structure.muted = not user_structure.muted

    await client.send_extension("gs_update_structure", SFSObject()
                                .putLong('user_structure_id', user_structure_id)
                                .putSFSArray('properties', SFSArray().addSFSObject(SFSObject().putInt('muted', muted))))
    return SFSObject().putBool('success', True)


@router.on_request('gs_flip_structure')
async def flip_structure(client: 'SFSServerClient', params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')
    flipped = params.get('flipped')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if flipped is not None:
            user_structure.flip = bool(flipped)
        else:
            user_structure.flip = not user_structure.flip

    response = SFSObject()
    response.putLong('user_structure_id', user_structure_id)
    response.putSFSArray('properties', SFSArray().addSFSObject(SFSObject().putInt('flip', user_structure.flip)))

    await client.send_extension("gs_update_structure", SFSObject()
                                .putLong('user_structure_id', user_structure_id)
                                .putSFSArray('properties', SFSArray().addSFSObject(SFSObject().putInt('flip', user_structure.flip))))
    return SFSObject().putBool('success', True)


@router.on_request('gs_finish_structure')
async def finish_structure(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        current_time = round(time.time() * 1000)
        if user_structure.building_completed > current_time:
            return 'This structure is not ready to be finished.'

        await client.player.add_currency('xp', user_structure.structure.xp)
        user_structure.is_complete = True
        user_structure.is_upgrading = False
        user_structure.building_completed = current_time

    await client.send_extension("gs_update_structure",
                                SFSObject().putLong('user_structure_id', user_structure_id)
                                .putSFSArray('properties', SFSArray()
                                             .addSFSObject(SFSObject().putInt('is_complete', 1))
                                             .addSFSObject(SFSObject().putInt('is_upgrading', 0))))

    return SFSObject().putBool('success', True).putLong('user_structure_id', user_structure_id)


@router.on_request('gs_collect_from_mine')
async def collect_from_mine(client: SFSServerClient, params: 'SFSObject'):
    async with client.player.get_active_island.get_structure_by_type('mine') as mine:
        if mine is None:
            return 'Mine not found.'

        current_time = round(time.time() * 1000)
        ctime = mine.structure.extra.get('time') * 1000
        if mine.last_collection + ctime > current_time:
            return 'Mine is not ready to be collected.'

        diamonds = mine.structure.extra.get('diamonds')
        if diamonds is not None:
            await client.player.add_currency('diamonds', diamonds)

        mine.last_collection = current_time

    await client.send_extension("gs_update_structure",
                                SFSObject().putLong('user_structure_id', mine.user_structure_id)
                                .putSFSArray('properties',
                                             SFSArray().addSFSObject(SFSObject().putLong('last_collection', mine.last_collection))))
    return SFSObject().putBool('success', True)


@router.on_request('gs_sell_structure')
async def sell_structure(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if user_structure.structure.structure_type in ('castle', 'obstacle'):
            return 'This structure cannot be sold.'

        active_island = client.player.get_active_island
        if active_island.is_ethereal_island():
            await client.player.add_currency('eth', round(user_structure.structure.cost_eth_currency * 0.75))
        elif active_island.is_amber_island():
            await client.player.add_currency('relics', round(user_structure.structure.cost_relics * 0.75))
        else:
            await client.player.add_currency('coins', round(user_structure.structure.cost_coins * 0.75))

    client.player.get_active_island.structures.remove(user_structure)
    await user_structure.remove()

    response = SFSObject()
    response.putBool('success', True)
    response.putLong('user_structure_id', user_structure_id)
    response.putSFSArray('properties', client.player.get_properties())

    return response


@router.on_request('gs_start_upgrade_structure')
async def start_upgrade_structure(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if user_structure.is_upgrading:
            return 'This structure is already upgrading.'

        if user_structure.structure.upgrades_to is None:
            return 'This structure cannot be upgraded.'

        new_structure = await Structure.load_by_id(user_structure.structure.upgrades_to)
        if not await client.player.check_prices(obj=new_structure, eth_instead_of_coins=client.player.get_active_island.is_ethereal_island()):
            return 'You do not have enough currency to upgrade this structure.'

        user_structure.is_upgrading = True
        user_structure.is_complete = False
        user_structure.building_completed = round(time.time() + new_structure.build_time) * 1000
        user_structure.date_created = round(time.time() * 1000)

    await client.send_extension("gs_update_structure",
                                SFSObject().putBool('success', True)
                                           .putLong('user_structure_id', user_structure_id)
                                           .putSFSArray('properties',
                                                        client.player.get_properties().addSFSObject(SFSObject().putInt('is_upgrading', 1))
                                                                      .addSFSObject(SFSObject().putInt('is_complete', 0))
                                                                      .addSFSObject(SFSObject().putLong('building_completed', user_structure.building_completed))
                                                                      .addSFSObject(SFSObject().putLong('date_created', user_structure.date_created))))
    return SFSObject().putBool('success', True)


@router.on_request('gs_finish_upgrade_structure')
async def finish_upgrade_structure(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if user_structure.building_completed > round(time.time() * 1000):
            return 'This structure is not ready to be finished.'

        if not user_structure.is_upgrading:
            return 'This structure is not upgrading.'

        user_structure.is_complete = True
        user_structure.structure_id = user_structure.structure.upgrades_to
        user_structure.is_upgrading = False
        user_structure.building_completed = round(time.time() * 1000)

    await client.player.add_currency('xp', user_structure.structure.xp)

    return (SFSObject().putBool('success', True)
            .putLong('user_structure_id', user_structure_id)
            .putSFSObject('user_structure', await user_structure.to_sfs_object())
            .putSFSArray('properties', client.player.get_properties()))


@router.on_request('gs_speed_up_structure')
async def speed_up_structure(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if not user_structure.is_upgrading:
            return 'Only UPGRADING structures are supported.'

        if user_structure.building_completed < round(time.time() * 1000):
            return 'This structure does not require speedup.'

        cost = round((user_structure.building_completed - time.time() * 1000) // (1000 * 60 * 60)) * 1 + 1
        if not await client.player.check_prices(diamonds=cost):
            return 'You don\'t have enough diamonds!'

        user_structure.building_completed = round(time.time() * 1000)

    await client.player.add_currency('xp', user_structure.structure.xp)
    await client.send_extension("gs_update_structure",
                                SFSObject().putLong('user_structure_id', user_structure_id)
                                           .putSFSArray('properties',
                                                        SFSArray().addSFSObject(SFSObject().putLong('building_completed', round(time.time() * 1000)))))
    return SFSObject().putBool('success', True).putLong('user_structure_id', user_structure_id)


@router.on_request('gs_clear_obstacle')
async def clear_obstacle(client: SFSServerClient, params: 'SFSObject'):
    user_structure_id = params.get('user_structure_id')

    async with client.player.get_active_island.get_structure(user_structure_id) as user_structure:
        if user_structure is None:
            return 'Invalid structure ID.'

        if user_structure.structure.structure_type != 'obstacle':
            return 'This structure cannot be cleared.'

        client.player.get_active_island.structures.remove(user_structure)
        await user_structure.remove()

    await client.player.add_currency('xp', user_structure.structure.xp)
    await client.send_extension("gs_update_structure",
                                SFSObject().putBool('success', True)
                                           .putLong('user_structure_id', user_structure_id)
                                           .putSFSArray('properties', client.player.get_properties()))
    return SFSObject().putBool('success', True)