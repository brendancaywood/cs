#!/usr/bin/env python3
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import logging
import inspect

game = hlt.Game()
ship_locations = {}

# Saturation 2 is better though
OPTIMUM_HALITE_SATURATION = constants.MAX_HALITE / 2

# Sight distance
SIGHT_DISTANCE = 10


def check_position(ship_id, make_position=False):
    ref = ship_locations[ship_id]['next_move']
    if isinstance(ref, Position):
        if make_position:
            return
        else:
            ship_locations[ship_id]['next_move'] = (ref.x, ref.y)
            return
    else:
        ship_locations[ship_id]['next_move'] = Position(ref[0], ref[1])
        return


def check_perimeter(game_map):
    global OPTIMUM_HALITE_SATURATION
    spots = []
    for row in range(game_map.height):
        for col in range(game_map.width):
            pos = Position(row, col)
            if game_map[pos].halite_amount >= OPTIMUM_HALITE_SATURATION:
                spots.append(game_map[pos])
    if len(spots) == 0:
        logging.info('Lowering global threshold')
        OPTIMUM_HALITE_SATURATION = OPTIMUM_HALITE_SATURATION / 2

    return spots


def find_closest_halite(ship, issa_map, ya_boy, perimeter):
    if len(perimeter) == 0:
        return Direction.Still

    distance = 100000000000000
    optimum_location = Position(0, 0)

    for location in perimeter:
        calculated_distance = issa_map.calculate_distance(
                ship.position, location.position)
        if calculated_distance < distance:
            optimum_location = location
            distance = min(calculated_distance, distance)

    return optimum_location


def check_collision(ship, move, issa_map, ya_boy):
    move = Position(move[0], move[1])
    for ship_id in ship_locations:
        the_ship = ship_locations[ship_id]['ship']
        the_next_move = ship_locations[ship_id]['next_move']
        logging.info('NEXT MOVE: {} {}'.format(the_next_move, move))
        if the_next_move == move \
                and the_ship != ship:
            continue
        else:
            return False
    return True


def make_destination(ship, destination, issa_map, ya_boy):
    ''' Finds the destination'''

    # If we don't have a lot of halite
    if ship.halite_amount <= issa_map[ship.position].halite_amount * 0.1:
        return Direction.Still

    possible_moves = issa_map.get_unsafe_moves(
            ship.position, ship_locations[ship.id]['moving_to'])

    for move in possible_moves:
        if not check_collision(ship, move, issa_map, ya_boy):
            logging.info('Move: {}'.format(move))
            return Position(move[0], move[1])
        else:
            continue
    # No valid moves? Stand still and suck some halite
    return Direction.Still


def make_move(ship, ya_boy, issa_map):
    if ship.halite_amount > 900 and \
            ship_locations['ship_status'] == 'exploring':
        ship_locations[ship.id]['ship_status'] = 'returning'
        ship_locations[ship.id]['moving_to'] = ya_boy.shipyard.position

    if ship_locations[ship.id]['ship_status'] == 'returning':
        if issa_map[ship.position].has_structure:
            ship_locations[ship.id]['ship_status'] = 'exploring'
            ship_locations[ship.id]['moving_to'] = None
        else:
            ship_locations[ship.id]['next_move'] = make_destination(
                    ship, ya_boy.shipyard.position, issa_map, ya_boy)
    if ship_locations[ship.id]['ship_status'] == 'exploring':
        if issa_map[ship.position].halite_amount >= OPTIMUM_HALITE_SATURATION:
            ship_locations[ship.id]['next_move'] = Direction.Still
        else:
            spots = check_perimeter(issa_map)
            best_spot = find_closest_halite(ship, issa_map, ya_boy, spots)
            ship_locations[ship.id]['next_move'] = make_destination(
                    ship, best_spot, issa_map, ya_boy)


def check_ship_nearby(ship_id, ya_boy):
    check_position(ship_id, True)
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
    dead_ships = []
    for ship_id in ship_locations:
        if not ya_boy.has_ship(ship_id):
            dead_ships.append(ship_id)

    for dead_ship in dead_ships:
        del ship_locations[dead_ship]

    # Check ship position
    for ship in ya_boy.get_ships():
        if ship.id not in ship_locations:
            ship_locations[ship.id] = {
                'ship': ship,
                'moving_to': None,
                'next_move': ship.position,
                'ship_status': 'exploring'
            }
        make_move(ship, ya_boy, issa_map)

    for ship in ya_boy.get_ships():
        make_move(ship, ya_boy, issa_map)

    if game.turn_number <= 300 and \
        ya_boy.halite_amount >= constants.SHIP_COST \
            and not issa_map[ya_boy.shipyard].is_occupied:

        if len(ya_boy.get_ships()) != 0:
            # Make sure no ships are nearby
            for ship_id in ship_locations:
                if check_ship_nearby(ship_id, ya_boy):
                    logging.info('WE ARE HERE WOOO')
                    command_queue.append(ya_boy.shipyard.spawn())
                    break
        else:
            command_queue.append(ya_boy.shipyard.spawn())

    for ship_id in ship_locations:
        idx = ship_locations[ship_id]['next_move']
        logging.info(
            'SHIP INFO: {}'.format(ship_locations[ship_id]['next_move']))
        command_queue.append(
                ship_locations[ship_id]['ship'].move(idx))

    game.end_turn(command_queue)
