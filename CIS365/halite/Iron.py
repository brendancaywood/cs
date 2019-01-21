#!/usr/bin/env python3
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import logging

game = hlt.Game()
ship_locations = {}

# Saturation 2 is better though
OPTIMUM_HALITE_SATURATION = constants.MAX_HALITE / 2
COUNTER = 0

def check_perimeter(game_map):
    spots = []
    # search all cells for halite
    # Possibly optimize by robot spot
    # for better performance
    for row in range(game_map.height):
        for col in range(game_map.width):
            pos = Position(row, col)
            if game_map[pos].halite_amount >= OPTIMUM_HALITE_SATURATION:
                spots.append(game_map[pos])

    # Get top 5 to keep things clean
    if len(spots) > 5:
        return sorted(
                range(len(spots)), key=lambda i: spots[i].halite_amount)[-2:]
    else:
        return spots

def check_collision(ship, move, issa_map, ya_boy):
    global COUNTER
    move = Position(move[0], move[1])
    for ship_id in ship_locations:
        the_ship = ship_locations[ship_id]['ship']
        logging.info("ship locs:{}".format(ship_locations))
        the_next_move = ship_locations[ship_id]['next_move']
        if COUNTER == 0:
            the_next_move1 = the_next_move.x
            the_next_move2 = the_next_move.y
            COUNTER = COUNTER + 1
        else:
            the_next_move1 = the_next_move[0]
            the_next_move2 = the_next_move[1]
        next_move = (the_next_move1, the_next_move2)
        logging.info('NEXT MOVE: {} {}'.format(next_move, move))
        if Position(the_next_move1, the_next_move2) == move \
                and the_ship != ship:
            continue
        else:
            return False
    return True


def make_destination(ship, issa_map, ya_boy):
    ''' Finds the destination'''

    # If we don't have a lot of halite
    if ship.halite_amount >= OPTIMUM_HALITE_SATURATION * .2:
        ship_locations[ship.id]['moving_to'] = Direction.Still

    possible_moves = issa_map.get_unsafe_moves(
            ship.position, ship_locations[ship.id]['moving_to'])

    for move in possible_moves:
        if not check_collision(ship, move, issa_map, ya_boy):
            ship_locations[ship.id]['next_move'] = Position(move[0], move[1])
            break
        else:
            continue
    # No valid moves? Stand still and suck some halite
    ship_locations[ship.id]['next_move'] = Direction.Still


def make_move(ship, ya_boy, issa_map):
    if ship.halite_amount >= constants.MAX_HALITE * 0.7:
        ship_locations[ship.id]['ship_status'] = 'returning'
        logging.info('Ship: {} going home'.format(ship.id))
        ship_locations[ship.id]['moving_to'] = ya_boy.shipyard.positon

    if ship_locations[ship.id]['ship_status'] == 'exploring':
        # dont leave if halite high
        if issa_map[ship.position].halite_amount >= OPTIMUM_HALITE_SATURATION:
            ship_locations[ship.id]['next_move'] = Direction.Still
        else:
            logging.info("shits going haywire")
            ship_locations[ship.id]['next_move'] = Position(max(
                    check_perimeter(issa_map)))


def check_ship_nearby(ship_id, ya_boy):
    logging.info("whoop")
    return ship_locations[ship_id]['next_move'] != ya_boy.shipyard.position


game.ready('IRON')
logging.info('Iron has arrived... {}'.format(game.my_id))

while True:
    game.update_frame()
    ya_boy = game.me
    issa_map = game.game_map
    command_queue = []

    # Get the top 5 most halite spots
    most_halite = check_perimeter(issa_map)

    # check dead boy
    for ship_id in ship_locations:
        if not ya_boy.has_ship(ship_id):
            del ship_locations[ship_id]

    # Check ship position
    for ship in ya_boy.get_ships():
        if ship.id not in ship_locations:
            ship_locations[ship.id] = {
                'ship': ship,
                'moving_to': Position(0, 0),
                'next_move': ship.position,
                'ship_status': 'exploring'
            }

    for ship in ya_boy.get_ships():
        make_destination(ship, issa_map, ya_boy)

    if game.turn_number <= 300 and \
        ya_boy.halite_amount >= constants.SHIP_COST \
            and not issa_map[ya_boy.shipyard].is_occupied:

        if len(ya_boy.get_ships()) != 0:
            # Make sure no ships are nearby
            for ship_id in ship_locations:
                if check_ship_nearby(ship_id, ya_boy):
                    logging.info('WE ARE HERE WOOO')
                    command_queue.append(ya_boy.shipyard.spawn())
        else:
            command_queue.append(ya_boy.shipyard.spawn())

    for ship_id in ship_locations:
        logging.info(
                'SHIP INFO3: {}'.format(ship_locations[ship_id]['next_move']))
        command_queue.append(
                ship_locations[ship_id]['ship'].move(
                    ship_locations[ship_id]['next_move']))

    game.end_turn(command_queue)
    