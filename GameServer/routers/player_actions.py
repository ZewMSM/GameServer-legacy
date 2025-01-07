import asyncio

from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSObject

router = SFSRouter()


@router.on_request('gs_player')
async def send_player_data(client: SFSServerClient, request: SFSObject):
    for i in range(20):
        if client is not None:

            if i == 3:
                await client.send_extension("gs_display_generic_message",
                                            SFSObject().putBool("force_logout", False)
                                            .putUtfString("msg", "WAIT_PLEASE_HEAVY_LOAD_ON_SERVER_MESSAGE"))
            elif i == 10:
                await client.send_extension("gs_display_generic_message",
                                            SFSObject().putBool("force_logout", False)
                                            .putUtfString("msg", "EXTREMELY_HEAVY_LOAD_ON_SERVER_MESSAGE"))
            if client.player is None:
                await asyncio.sleep(1)
            else:
                pdata =  SFSObject().putSFSObject('player_object', await client.player.to_sfs_object())
                print(pdata.tokenize())
                return pdata
        else:
            return None

    await client.send_extension("gs_display_generic_message",
                                SFSObject().putBool("force_logout", False)
                                .putUtfString("msg", "SERVER_PIZDA_MESSAGE"))

    await client.kick()
    return 'Error'


@router.on_request('gs_set_displayname')
async def update_display_name(client: SFSServerClient, params: SFSObject):
    new_name = str(params.get('newName', ""))

    async with client.player as player:
        player.display_name = new_name

    return SFSObject().putBool('success', True).putUtfString("displayName", new_name)


@router.on_request('gs_set_avatar')
async def update_avatar(client: SFSServerClient, params: SFSObject):
    pp_info = str(params.get('pp_info', ""))

    async with client.player as player:
        player.avatar['pp_info'] = pp_info

    return SFSObject().putBool('success', True).putUtfString('pp_info', str(player.avatar.get('pp_info', pp_info))).putInt('pp_type', int(player.avatar.get('pp_type', 0)))


@router.on_request('gs_set_moniker')
async def set_moniker(client: SFSServerClient, params: SFSObject):
    new_moniker = int(params.get('moniker_id', 0))

    async with client.player as player:
        player.moniker_id = new_moniker

    return SFSObject().putBool('success', True).putInt("id", new_moniker)
