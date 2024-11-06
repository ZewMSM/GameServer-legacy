from ZewSFS.Types import Int, SFSObject, SFSArray
from database import StoreItemDB, StoreGroupDB, StoreCurrencyDB, StoreReplacementDB
from database.base_adapter import BaseAdapter


class StoreItem(BaseAdapter):
    _db_model = StoreItemDB
    _game_id_key = 'storeitem_id'
    _specific_sfs_datatypes = {'id': Int}

    amount: int = 0
    unlock_level: int = 0
    item_desc: str = '='
    max: int = -1
    ios_platform_id: str = ''
    item_name: str = ''
    enabled: bool = True
    most_popular_priority: int = 0
    contents: str = None
    group_id: int = 0
    sheet_id: str = 'currency.bin'
    android_platform_id: str = ''
    price: int = 0
    consumable: bool = True
    best_value_priority: int = 0
    currency: str = ''
    exclude: bool = False
    item_title: str = ''
    image_id: str = ''
    min_server_version: str = '0'
    currency_id: int = 1

    async def update_sfs(self, params: SFSObject):
        if self.contents is not None:
            params.putSFSArray('contents', SFSArray.from_json(self.contents))
        return params


class StoreGroup(BaseAdapter):
    _db_model = StoreGroupDB
    _game_id_key = 'storegroup_id'

    group_title: str = ''
    group_name: str = ''
    ad_name: str = ""
    currency: int = 0
    min_server_version: str = "0.0"
    store_ordering: int = 0


class StoreCurrency(BaseAdapter):
    _db_model = StoreCurrencyDB
    _game_id_key = 'storecur_id'

    currency_name: str = ""
    last_changed: int = 0


class StoreReplacement(BaseAdapter):
    _db_model = StoreReplacementDB
    _game_id_key = 'entityIdReplacement'

    numOwnedBeforeReplacement: int = 1
    entityIdSource: str = ''
    last_created: int = 0
