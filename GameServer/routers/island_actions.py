from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject, SFSArray
from database.island import Island
from database.player import PlayerIsland

router = SFSRouter()


@router.on_request('gs_buy_island')
async def buy_island(client: SFSServerClient, params: SFSObject):
    island_id = int(params.get('island_id'))
    if island_id == 0:
        return 'Invalid island id'

    island_name = params.get('island_name')
    no_change_island = params.get('no_change_island', False)
    island = await Island.load_by_id(island_id)
    if island is None:
        return 'Invalid island id'

    if client.player.get_island_by_id(island_id) is not None:
        return 'Island already owned'
    if island.island_type == 9:  # TODO: Add tribal support
        return 'Tribal island isn\'t supported yet.'

    if not await client.player.check_prices(obj=island):
        return 'You don\'t have enough currency to buy this shit'

    player_island = await PlayerIsland.create_new_island(client.player.id, island_id)
    client.player.islands.append(player_island)

    return (SFSObject().putBool('success', True).putSFSArray('properties', client.player.get_properties())
            .putSFSObject('user_island', await player_island.to_sfs_object()).putBool("no_change_island", no_change_island))


@router.on_request('gs_change_island')
async def change_island(client: SFSServerClient, params: SFSObject):
    user_island_id = params.get('user_island_id')
    user_structure_focus = params.get('user_structure_focus')
    user_monster_focus = params.get('user_monster_focus')

    async with client.player as player:
        if player.active_island == user_island_id:
            return 'You already own this island'
        if player.get_island(user_island_id) is None:
            return 'Invalid island id'
        player.active_island = user_island_id

    async with player.get_active_island:
        player.get_active_island.last_player_level = player.level

    resp = SFSObject()
    resp.putBool('success', True)
    resp.putLong('user_island_id', user_island_id)
    if user_structure_focus is not None:
        resp.putLong('user_structure_focus', user_structure_focus)
    if user_monster_focus is not None:
        resp.putLong('user_monster_focus', user_monster_focus)

    return resp


@router.on_request('gs_save_island_warp_speed')
async def set_warp_speed(client: SFSServerClient, params: SFSObject):
    warp_speed = params.get('warp_speed')
    if warp_speed is None:
        return

    async with client.player.get_active_island as island:
        island.warp_speed = round(warp_speed, 4)

    return SFSObject().putBool('success', True)
