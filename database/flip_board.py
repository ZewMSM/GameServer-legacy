from ZewSFS.Types import SFSObject
from database import FlipBoardDB, FlipLevelDB
from database.base_adapter import BaseAdapter


class FlipBoard(BaseAdapter):
    _db_model = FlipBoardDB
    _game_id_key = 'id'

    name: str = ''
    definition: str = ''

    async def update_sfs(self, params: SFSObject):
        return params.putSFSObject("definition", SFSObject.from_json(self.definition))


class FlipLevel(BaseAdapter):
    _db_model = FlipLevelDB
    _game_id_key = 'id'

    num_dipsters: int = 0
    num_sigils: int = 0
    shape: str = ''
    level: int = 0
    columns: int = 0
    rows: int = 0
    num_epics: int = 0
    mismatches_allowed: int = 0
    num_rares: int = 0
    prize_pool: int = 0
    last_changed: int = 0
