from sqlalchemy import select

from database import ScratchOfferDB
from database.base_adapter import BaseAdapter


class ScratchOffer(BaseAdapter):
    _db_model = ScratchOfferDB
    _game_id_key = 'id'

    amount: int = 0
    sheetName: str = ''
    probability: int = 0
    is_top_prize: bool = False
    spriteName: str = ''
    revealSfx: str = ''
    type: str = ''
    prize: str = ''
    min_server_version: str = ''