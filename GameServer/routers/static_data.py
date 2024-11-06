import json
import time

from sqlalchemy.engine.reflection import cache

from ZewSFS.Server import SFSRouter, SFSServerClient
from ZewSFS.Types import SFSArray, SFSObject
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

router = SFSRouter(cached=True)


@router.on_request('db_gene')
async def send_gene_data(client: SFSServerClient, request: SFSObject):
    genes_data = SFSArray()
    for gene in await Gene.load_all():
        genes_data.addSFSObject(await gene.to_sfs_object())
    return SFSObject().putSFSArray('genes_data', genes_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_level')
async def send_level_data(client: SFSServerClient, request: SFSObject):
    levels_data = SFSArray()
    for level in await Level.load_all():
        levels_data.addSFSObject(await level.to_sfs_object())
    return SFSObject().putSFSArray('levels_data', levels_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_scratch_offs')
async def send_scratch_data(client: SFSServerClient, request: SFSObject):
    offers = SFSArray()
    for sc in await ScratchOffer.load_all():
        offers.addSFSObject(await sc.to_sfs_object())
    return SFSObject().putSFSArray('genes_data', offers).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_monster')
async def send_monster_data(client: SFSServerClient, request: SFSObject):
    monsters_data = SFSArray()
    for monster in (await Monster.load_all()):
        monsters_data.addSFSObject(await monster.to_sfs_object())
    return SFSObject().putSFSArray('monsters_data', monsters_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_structure')
async def send_structure_data(client: SFSServerClient, request: SFSObject):
    structures_data = SFSArray()
    for structure in (await Structure.load_all()):
        structures_data.addSFSObject(await structure.to_sfs_object())
    return SFSObject().putSFSArray('structures_data', structures_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_island_v2')
async def send_island_data(client: SFSServerClient, request: SFSObject):
    islands_data = SFSArray()
    for island in (await Island.load_all()):
        islands_data.addSFSObject(await island.to_sfs_object())
    return SFSObject().putSFSArray('islands_data', islands_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_island_themes')
async def send_themes_data(client: SFSServerClient, request: SFSObject):
    island_theme_data = SFSArray()
    for theme in (await IslandThemeData.load_all()):
        island_theme_data.addSFSObject(await theme.to_sfs_object())
    return SFSObject().putSFSArray('island_theme_data', island_theme_data).putLong('server_time', round(time.time() * 1000)).putLong('last_updated', round(time.time() * 1000))


@router.on_request('db_store_v2')
async def send_store_data(client: SFSServerClient, request: SFSObject):
    items_data = SFSArray()
    for item in (await StoreItem.load_all()):
        items_data.addSFSObject(await item.to_sfs_object())

    groups_data = SFSArray()
    for group in (await StoreGroup.load_all()):
        groups_data.addSFSObject(await group.to_sfs_object())

    currencies_data = SFSArray()
    for curr in (await StoreCurrency.load_all()):
        currencies_data.addSFSObject(await curr.to_sfs_object())

    return SFSObject().putSFSArray('store_item_data', items_data).putSFSArray('store_group_data', groups_data).putSFSArray('store_currency_data', currencies_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_battle')
async def send_battle_data(client: SFSServerClient, request: SFSObject):  # TODO: Add Battle Data
    return SFSObject().putSFSArray("battle_campaign_data", SFSArray()).putLong("server_time", int(time.time() * 1000))


@router.on_request('db_battle_levels')
async def send_battle_levels_data(client: SFSServerClient, request: SFSObject):  # TODO: Add Battle Levels Data
    return SFSObject().putSFSArray("battle_level_data", SFSArray()).putLong("server_time", int(time.time() * 1000))


@router.on_request('db_battle_monster_training')
async def send_battle_training_data(client: SFSServerClient, request: SFSObject):  # TODO: Add Battle Training Data
    return SFSObject().putSFSArray("battle_monster_training_data", SFSArray()).putLong("server_time", int(time.time() * 1000))


@router.on_request('db_battle_monster_actions')
async def send_battle_monster_actions_data(client: SFSServerClient, request: SFSObject):  # TODO: Add Battle Monster Actions Data
    return SFSObject().putSFSArray("battle_monster_actions_data", SFSArray()).putLong("server_time", int(time.time() * 1000))


@router.on_request('db_battle_monster_stats')
async def send_battle_monster_stats(client: SFSServerClient, request: SFSObject):  # TODO: Add Battle Monster Stats Data
    return SFSObject().putSFSArray("battle_monster_stats_data", SFSArray()).putLong("server_time", int(time.time() * 1000))


@router.on_request('db_battle_music')
async def send_battle_music_data(client: SFSServerClient, request: SFSObject):  # TODO: Add Battle Music Data
    return SFSObject().putSFSArray("battle_music_data", SFSArray()).putLong("server_time", int(time.time() * 1000))


@router.on_request('db_costumes')
async def send_costumes_data(client: SFSServerClient, request: SFSObject):
    costume_data = SFSArray()
    for costume in (await MonsterCostume.load_all()):
        costume_data.addSFSObject(await costume.to_sfs_object())
    return SFSObject().putSFSArray('costume_data', costume_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('gs_flip_boards')
async def send_flip_boards(client: SFSServerClient, request: SFSObject):
    flip_boards = SFSArray()
    for board in (await FlipBoard.load_all()):
        flip_boards.addSFSObject(await board.to_sfs_object())
    return SFSObject().putSFSArray('flip_boards', flip_boards).putLong('server_time', round(time.time() * 1000))


@router.on_request('gs_flip_levels')
async def send_flip_levels(client: SFSServerClient, request: SFSObject):
    flip_levels = SFSArray()
    for flip_level in (await FlipLevel.load_all()):
        flip_levels.addSFSObject(await flip_level.to_sfs_object())
    return SFSObject().putSFSArray('flip_levels', flip_levels).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_daily_cumulative_login')
async def send_daily_cumulative_login_data(client: SFSServerClient, request: SFSObject):
    daily_cumulative_login_data = SFSArray()
    for login_data in (await FlipLevel.load_all()):
        daily_cumulative_login_data.addSFSObject(await login_data.to_sfs_object())
    return SFSObject().putSFSArray('daily_cumulative_login_data', daily_cumulative_login_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_flexeggdefs')
async def send_flex_eggs_data(client: SFSServerClient, request: SFSObject):
    flex_egg_def_data = SFSArray()
    for flex_egg in (await FlexEggs.load_all()):
        flex_egg_def_data.addSFSObject(await flex_egg.to_sfs_object())
    return SFSObject().putSFSArray('flex_egg_def_data', flex_egg_def_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_attuner_gene')
async def send_attuner_genes(client: SFSServerClient, request: SFSObject):
    attuner_gene_data = SFSArray()
    for attuner_gene in (await AttunerGene.load_all()):
        attuner_gene_data.addSFSObject(await attuner_gene.to_sfs_object())
    return SFSObject().putSFSArray('attuner_gene_data', attuner_gene_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_loot')
async def send_loot_data(client: SFSServerClient, request: SFSObject):
    return SFSObject().putLong("server_time", int(time.time() * 1000))


@router.on_request('db_nucleus_reward')
async def send_nucleus_reward_data(client: SFSServerClient, request: SFSObject):
    nucleus_reward_data = SFSArray()
    for reward in (await NucleusReward.load_all()):
        nucleus_reward_data.addSFSObject(await reward.to_sfs_object())
    return SFSObject().putSFSArray('nucleus_reward_data', nucleus_reward_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_entity_alt_costs')
async def send_entity_alt_data(client: SFSServerClient, request: SFSObject):
    entity_alt_data = SFSArray()
    for data in (await EntityAltCosts.load_all()):
        entity_alt_data.addSFSObject(await data.to_sfs_object())
    return SFSObject().putSFSArray('entity_alt_data', entity_alt_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_store_replacements')
async def send_store_replacements(client: SFSServerClient, request: SFSObject):
    store_replacement_data = SFSArray()
    for data in (await StoreReplacement.load_all()):
        store_replacement_data.addSFSObject(await data.to_sfs_object())
    return SFSObject().putSFSArray('store_replacement_data', store_replacement_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('db_titansoul_levels')
async def send_titansouls_levels(client: SFSServerClient, request: SFSObject):
    titansoul_level_data = SFSArray()
    for data in (await TitanSoulLevel.load_all()):
        titansoul_level_data.addSFSObject(await data.to_sfs_object())
    return SFSObject().putSFSArray('titansoul_level_data', titansoul_level_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('gs_quest')
async def send_quests(client: SFSServerClient, request: SFSObject):  # TODO: Add Quests
    return SFSObject().putSFSArray("result", SFSArray()).putLong("server_time", int(time.time() * 1000))


@router.on_request('gs_timed_events')
async def send_timed_events(client: SFSServerClient, request: SFSObject):
    timed_event_list = SFSArray()
    for event in (await TimedEvents.load_all()):
        timed_event_list.addSFSObject(await event.to_sfs_object())
    return SFSObject().putSFSArray('timed_event_list', timed_event_list).putLong('server_time', round(time.time() * 1000))


@router.on_request('gs_rare_monster_data')
async def send_rare_monster_data(client: SFSServerClient, request: SFSObject):
    rare_monster_data = SFSArray()
    for data in (await RareMonsterData.load_all()):
        rare_monster_data.addSFSObject(await data.to_sfs_object())
    return SFSObject().putSFSArray('rare_monster_data', rare_monster_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('gs_epic_monster_data')
async def send_epic_monster_data(client: SFSServerClient, request: SFSObject):
    epic_monster_data = SFSArray()
    for data in (await EpicMonsterData.load_all()):
        epic_monster_data.addSFSObject(await data.to_sfs_object())
    return SFSObject().putSFSArray('epic_monster_data', epic_monster_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('gs_monster_island_2_island_data')
async def send_epic_monster_data(client: SFSServerClient, request: SFSObject):
    monster_island_2_island_data = SFSArray()
    for data in (await MonsterHome.load_all()):
        monster_island_2_island_data.addSFSObject(await data.to_sfs_object())
    return SFSObject().putSFSArray('monster_island_2_island_data', monster_island_2_island_data).putLong('server_time', round(time.time() * 1000))


@router.on_request('gs_cant_breed')
async def send_epic_monster_data(client: SFSServerClient, request: SFSObject):
    async with await GameSettings.load_by_key('cant_breed_monsters') as obj:
        return SFSObject().putIntArray('monsterIds', json.loads(obj.value))


@router.on_request('gs_sticker')
async def send_sticker_data(client: SFSServerClient, request: SFSObject):
    return SFSObject()


# @router.on_request('gs_player')
async def experimental_send_player_data(client: SFSServerClient, request: SFSObject):
    player_object = SFSObject()

    player_object.putSFSArray('achievements', SFSArray())
    player_object.putLong('active_island', 1)
    player_object.putSFSArray('active_island_themes', SFSArray())

    avatar = SFSObject()
    avatar.putUtfString('pp_info', '0')
    avatar.putInt('pp_type', 0)
    avatar.putInt('user_id', 1)
    player_object.putSFSObject('avatar', avatar)

    battle_object = SFSObject()
    battle_object.putInt('level', 0)
    battle_object.putInt('xp', 0)
    battle_object.putInt('max_training_level', 0)
    battle_object.putInt('medals', 0)
    battle_object.putLong('user_id', 1)
    battle_object.putUtfString('loadout', '{}')
    battle_object.putUtfString('loadout_versus', '{}')
    player_object.putSFSObject('battle', battle_object)

    player_object.putLong('bbb_id', 1)
    player_object.putInt('cachedRewardDay', 0)
    # player_object.putUtfString('client_tutorial_setup', 'breedingAddOn')
    player_object.putLong('coins_actual', 123)

    costumes_object = SFSObject()
    costumes_object.putSFSArray('items', SFSArray())  # TODO: Add costumes
    costumes_object.putIntArray('unlocked', [])
    player_object.putSFSObject('costumes', costumes_object)

    player_object.putUtfString('country', 'us')
    player_object.putLong('currencyScratchTime', 0)
    player_object.putInt('daily_bonus_amount', 0)
    player_object.putUtfString('daily_bonus_type', '')

    daily_cumulative_login_object = SFSObject()
    daily_cumulative_login_object.putInt('calendar_id', 1)
    daily_cumulative_login_object.putLong('next_collect', 0)
    daily_cumulative_login_object.putInt('reward_idx', 0)
    daily_cumulative_login_object.putInt('total', 0)
    player_object.putSFSObject('daily_cumulative_login', daily_cumulative_login_object)

    player_object.putInt('daily_relic_purchase_count', 0)
    player_object.putLong('date_created', 0)
    player_object.putLong('diamonds_actual', 123)
    player_object.putInt('diamonds_spent', 123)
    player_object.putUtfString('display_name', 'Test')
    player_object.putLong('egg_wildcards', 1)
    player_object.putLong('egg_wildcards_actual', 123)
    player_object.putInt('email_invite_reward', 123)
    player_object.putLong('ethereal_currency_actual', 123)
    player_object.putUtfString('extra_ad_params', '')
    player_object.putInt('fb_invite_reward', 123)
    player_object.putLong('flip_game_time', 123)
    player_object.putLong('food_actual', 123)
    player_object.putLong('friend_gift', 123)
    player_object.putBool('has_free_ad_scratch', False)
    player_object.putBool('has_promo', False)
    player_object.putBool('has_scratch_off_m', False)
    player_object.putBool('has_scratch_off_s', False)
    player_object.putSFSObject('inventory', SFSObject().putSFSArray('items', SFSArray()))
    player_object.putInt('is_admin', 0)

    obj = SFSObject()
    obj.putSFSArray("baking", SFSArray())  # TODO: Add baking
    obj.putSFSArray("breeding", SFSArray())  # TODO: Add breeding
    obj.putSFSObject("costume_data", SFSObject().putSFSArray('costumes', SFSArray()))  # TODO: Add costumes

    obj.putSFSArray("eggs", SFSArray())
    obj.putSFSArray("fuzer", SFSArray())  # TODO: Add fuzer
    obj.putSFSArray("monsters", SFSArray())
    obj.putSFSArray("structures", SFSArray())
    obj.putSFSArray("torches", SFSArray())  # TODO: Add torches
    obj.putSFSArray("last_baked", SFSArray())
    obj.putUtfString("costumes_owned", '[]')
    obj.putInt("likes", 123)
    obj.putInt("dislikes", 1)
    obj.putInt("last_player_level", 10)
    obj.putBool("light_torch_flag", False)
    obj.putDouble("warp_speed", 1.0)
    obj.putLong("date_created", 0)
    obj.putLong("user_island_id", 1)
    obj.putLong("user", 123)
    obj.putInt("island", 1)
    obj.putInt("type", 1)
    obj.putInt('num_torches', 10)

    obj.putUtfString('monsters_sold', '[]')
    player_object.putSFSArray('islands', SFSArray().addSFSObject(obj))

    player_object.putLong('keys', 1)
    player_object.putLong('keys_actual', 123)
    player_object.putUtfString('last_client_version', '4.5.0')
    player_object.putLong('last_fb_post_reward', 123)
    player_object.putLong('last_login', 123)
    player_object.putInt('level', 80)
    player_object.putSFSArray('mailbox', SFSArray())
    player_object.putLong('monsterScratchTime', 123)
    player_object.putBool('new_mail', False)
    player_object.putLong('nextDailyLogin', 123)
    player_object.putLong('next_relic_reset', 123)
    player_object.putIntArray('owned_island_themes', [])
    player_object.putIntArray('player_groups', [])
    player_object.putInt('premium', 1)
    player_object.putLong('prev_rank', 0)
    player_object.putInt('prev_tier', 0)
    player_object.putInt('purchases_amount', 0)
    player_object.putInt('purchases_total', 0)

    pvp_season0 = SFSObject().putInt('campaign_id', 0).putLong('schedule_started_on', 0)
    player_object.putSFSObject('pvpSeason0', pvp_season0)  # TODO: Add PVP SEASON
    pvp_season1 = SFSObject().putInt('campaign_id', 0).putLong('schedule_started_on', 0)
    player_object.putSFSObject('pvpSeason1', pvp_season1)  # TODO: Add PVP SEASON

    player_object.putInt('relic_diamond_cost', 0)
    player_object.putLong('relics', 123)
    player_object.putLong('relics_actual', 123)
    player_object.putInt('reward_day', 1)
    player_object.putInt('rewards_total', 12)
    player_object.putSFSArray('scaled_daily_reward', SFSArray())
    player_object.putBool('show_welcomeback', False)
    player_object.putSFSArray('songs', SFSArray())  # TODO: Add songs
    player_object.putLong('speed_up_credit', 1)
    player_object.putLong('starpower_actual', 123)
    player_object.putBool('third_party_ads', False)
    player_object.putBool('third_party_video_ads', False)
    player_object.putSFSArray('timed_events', SFSArray())  # TODO: IDK WTF IS IT BUT IN NEED TO BE IMPLEMENTED IN FUTURE
    player_object.putLong('total_starpower_collected', 123123)
    player_object.putInt('twitter_invite_reward', 0)
    player_object.putSFSArray('tracks', SFSArray())  # TODO: Add tracks
    player_object.putInt('user_id', 123)
    player_object.putInt('xp',1231231231)

    print(player_object.tokenize())
    return SFSObject().putSFSObject('player_object', player_object)
