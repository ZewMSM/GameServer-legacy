from database.player import PlayerStructure, PlayerIsland
from database.structure import Structure


class PlayerIslandFactory:
    BASIC_SYNTHESIZER = 857
    BASIC_BREEDING = 2
    BASIC_ATTUNER = 856
    BASIC_CRUCIBLE = 711
    BASIC_NURSERY = 1
    BATTLE_NURSERY = 535
    BATTLE_GYM = 533
    BATTLE_HOTEL = 534
    BASIC_BAKERY = 32

    NOGGIN_ID = 3
    MAMOTT_ID = 5
    TOEJAMMER_ID = 4
    COMPOSER_MAMMOTT_ID = 204

    CASTLE_POS = (29, 9)
    DEFAULT_NURSERY_POS = (35, 17)
    DEFAULT_BREEDING_POS = (21, 3)
    DEFAULT_NOGGIN_POS = (23, 12)
    DEFAULT_MAMMOTT_POS = (27, 16)
    BATTLE_MONSTER_POS = (23, 12)
    BATTLE_GYM_POS = (21, 3)
    BATTLE_HOTEL_POS = (29, 9)
    COMPOSER_MAMMOTT_POS = (10, 28)

    DEFAULT_OBSTACLE_POSITIONS_X = [14, 5, 9, 22, 7, 6, 16, 5, 7, 11, 13, 10, 20, 15, 12, 16, 22, 11, 26, 24, 18, 23, 3, 16, 2, 8, 14, 28, 6, 16, 13, 2, 22, 19, 11, 13, 28, 29, 22, 19, 6, 14, 26, 11, 12, 17, 21, 10, 7,
                                    17, 1,
                                    15, 9, 19, 25, 14, 21, 19, 10, 9]
    DEFAULT_OBSTACLE_POSITIONS_Y = [12, 26, 21, 32, 17, 14, 27, 23, 27, 9, 21, 28, 35, 17, 31, 22, 26, 17, 31, 33, 29, 28, 20, 34, 23, 32, 33, 22, 31, 10, 23, 18, 23, 12, 13, 29, 20, 24, 9, 32, 21, 10, 22, 20, 34, 13,
                                    25, 24, 9,
                                    36, 20, 36, 9, 37, 21, 26, 29, 22, 14, 34]
    DEFAULT_OBSTACLE_OFFSET = [0, 5, 3, 4, 1, 2, 4, 3, 0, 5, 0, 2, 1, 3, 0, 1, 3, 4, 5, 0, 1, 2, 3, 0, 1, 3, 4, 0, 1, 2, 3, 5, 4, 0, 1, 1, 3, 1, 0, 1, 4, 0, 0, 2, 0, 3, 0, 0, 3, 4, 0, 3, 0, 0, 1, 3, 0, 0, 3, 1]
    ISLAND_13_OBSTACLE_POSITIONS_X = [14, 5, 9, 22, 7, 6, 16, 5, 7, 11, 13, 10, 20, 15, 12, 16, 22, 11, 26, 24, 18, 23, 3, 16, 2, 8, 14, 28, 13, 22, 19, 11, 13, 28, 29, 22, 19, 6, 14, 26, 11, 12, 17, 21, 10, 7, 17, 15,
                                      9, 19, 25,
                                      14, 19, 10]
    ISLAND_13_OBSTACLE_POSITIONS_Y = [12, 26, 21, 32, 17, 14, 27, 23, 27, 9, 21, 28, 35, 17, 31, 22, 26, 17, 31, 33, 29, 28, 20, 34, 23, 32, 33, 22, 23, 23, 12, 13, 29, 20, 24, 9, 32, 21, 10, 22, 20, 34, 13, 25, 24, 9,
                                      36, 36, 9,
                                      37, 21, 26, 29, 22, 14]
    ISLAND_13_OBSTACLE_OFFSET = [0, 5, 3, 4, 1, 2, 4, 3, 0, 5, 0, 2, 1, 3, 0, 1, 3, 4, 5, 0, 1, 2, 3, 0, 1, 3, 4, 0, 3, 4, 0, 1, 1, 3, 1, 0, 1, 4, 0, 0, 2, 0, 3, 0, 0, 3, 4, 3, 0, 0, 1, 3, 0, 0, 3]
    OBSTACLE_IDS_PER_ISLAND = [106, 112, 118, 125, 131, -1, 194, 208, -1, -1, -1, -1, 361, 399, 430, 471, 498, 590, 631, -1, 661, 699, 777, 875, -1]
    CASTLE_IDS_PER_ISLAND = []

    @staticmethod
    async def create_initial_structures(player_island: 'PlayerIsland'):
        if player_island.is_wublin_island() or player_island.is_celestial_island():
            return
        if player_island.is_battle_island():
            player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BATTLE_HOTEL, *PlayerIslandFactory.BATTLE_HOTEL_POS, completed=True))
            player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BATTLE_GYM, *PlayerIslandFactory.BATTLE_GYM_POS, completed=True))
            player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BATTLE_NURSERY, *PlayerIslandFactory.DEFAULT_NURSERY_POS, completed=True))
        else:
            await PlayerStructure.create_new_structure(player_island.id, 137, *PlayerIslandFactory.CASTLE_POS, completed=True)

            if not (player_island.is_composer_island() or player_island.is_gold_island() or player_island.is_tribal_island() or player_island.is_workshop_island()):
                struct = player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BASIC_NURSERY, *PlayerIslandFactory.DEFAULT_NURSERY_POS, completed=True))
                # if player_island.island.island_type in range(2, 5):
                #     await PlayerEgg.create_new_egg(struct, await Monster.load_from_db(1, session), hatch_now=True)

                if player_island.is_amber_island():
                    ...
                    # player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BASIC_CRUCIBLE, *PlayerIslandFactory.DEFAULT_BREEDING_POS, completed=True))
                else:
                    player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BASIC_BREEDING, *PlayerIslandFactory.DEFAULT_BREEDING_POS, completed=True))

            if player_island.is_workshop_island():
                player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BASIC_ATTUNER, *PlayerIslandFactory.DEFAULT_BREEDING_POS, completed=True))
                player_island.structures.append(await PlayerStructure.create_new_structure(player_island.id, PlayerIslandFactory.BASIC_SYNTHESIZER, *PlayerIslandFactory.DEFAULT_NURSERY_POS, completed=True))

            if player_island.is_composer_island():
                ...  # TODO: Add Monster to composer island

            if player_island.is_battle_island():
                ...  # TODO: Add Monster to battle island
