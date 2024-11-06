from ZewSFS.Types import SFSObject, SFSArray
from database import DailyCumulativeLoginDB
from database.base_adapter import BaseAdapter


class DailyCumulativeLogin(BaseAdapter):
    _db_model = DailyCumulativeLoginDB
    _game_id_key = 'id'

    name: str = ''
    layout: str = ''
    rewards: str = ''
    min_version: str = '0.0'
    island: int

    async def update_sfs(self, params: SFSObject):
        return params.putSFSArray('rewards', SFSArray.from_json(self.rewards))
