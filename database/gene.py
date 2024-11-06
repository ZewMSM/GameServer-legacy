from ZewSFS.Types import Int, SFSObject
from database import GeneDB, AttunerGeneDB
from database.base_adapter import BaseAdapter


class Gene(BaseAdapter):
    _db_model = GeneDB
    _game_id_key = 'gene_id'
    _specific_sfs_datatypes = {'id': Int}

    gene_graphic: str
    gene_string: str
    gene_letter: str
    sort_order: int
    min_server_version: str


class AttunerGene(BaseAdapter):
    _db_model = AttunerGeneDB
    _game_id_key = 'id'
    _specific_sfs_datatypes = {'id': Int}

    schedule: str = ''
    critter_graphic: str = ''
    gene: str = ''
    attuner_graphic: str = ''
    instability: int = 0
    island_id: int = 0

    async def update_sfs(self, params: SFSObject):
        return params.putSFSObject('schedule', SFSObject.from_json(self.schedule))
