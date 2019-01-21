#!/usr/bin/env python3
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import logging

game = hlt.Game()
ship_locations = {}

# Saturation 2 is better though
OPTIMUM_HALITE_SATURATION = constants.MAX_HALITE / 2


def check_position(ship_id, make_position=False):
    '''
    Checks if a particular position is of type
    Position() and converts if needed
    '''
    ref = ship_locations[ship_id]['next_move']
    if isinstance(ref, Position):
        if make_position:
            return
        else:
            ship_locations[ship_id]['next_move'] = (ref.x, ref.y)
            return
    else:
        ship_locations[ship_id]['next_move'] = Position(ref)
        return


def check_perimeter(game_map):
    '''
    Checks the bot perimeter and determines
    where the most halite is
    '''
    spots = []
    # search all cells for halite
    # Possibly optimize by robot spot
    # for better performance
    for row in range(game_map.height):
        for col in range(game_map.width):
            pos = Position(row, col)
            if game_map[pos].halite_amount >= OPTIMUM_HALITE_SATURATION:
                spots.append(game_map[pos])

    # Get only the data we need from the list
    spots = [(x.halite_amount, x.position) for x in spots]

    # Get top 5 to keep things clean
    if len(spots) > 5:
        return sorted(spots, key=lambda i: i[0], reverse=True)[:5]
    else:
        return sorted(spots, key=lambda i: i[0], reverse=True)


def check_collision(ship, move, issa_map, ya_boy):
    '''
    Checks if a collision is immenent
    '''
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


def make_destination(ship, issa_map, ya_boy):
    ''' Finds the destination'''

    # If we don't have a lot of halite
    if ship.halite_amount >= OPTIMUM_HALITE_SATURATION * .2:
        ship_locations[ship.id]['moving_to'] = Direction.Still

    # Generate list of possible moves to go there
    # This needs to be implemented
    possible_moves = issa_map.get_unsafe_moves(
            ship.position, ship_locations[ship.id]['moving_to'])
    logging.info('Possible moves: {}'.format(possible_moves))

    for move in possible_moves:
        if not check_collision(ship, move, issa_map, ya_boy):
            ship_locations[ship.id]['next_move'] = Position(move[0], move[1])
            break
        else:
            continue
    # No valid moves? Stand still and suck some halite
    ship_locations[ship.id]['next_move'] = Direction.Still


def make_move(ship, ya_boy, issa_map):
    '''
    Generates the next move to the desired position
    '''
    if ship.halite_amount >= constants.MAX_HALITE * 0.7:
        ship_locations[ship.id]['ship_status'] = 'returning'
        logging.info('Ship: {} going home'.format(ship.id))
        ship_locations[ship.id]['moving_to'] = ya_boy.shipyard.positon

    if ship_locations[ship.id]['ship_status'] == 'exploring':
        # dont leave if halite high
        if issa_map[ship.position].halite_amount >= OPTIMUM_HALITE_SATURATION:
            ship_locations[ship.id]['next_move'] = Direction.Still
        else:
            max_halite = check_perimeter(issa_map)[1]
            logging.info('MAKE_MOVE: {}'.format(max_halite[1]))
            ship_locations[ship.id]['next_move'] = max_halite[1]


def check_ship_nearby(ship_id, ya_boy):
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
                'moving_to': Position(0, 0),
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
        check_position(ship_id, True)
        logging.info(
            'SHIP INFO: {}'.format(ship_locations[ship_id]['next_move']))
        command_queue.append(
                ship_locations[ship_id]['ship'].move(
                    issa_map.naive_navigate(
                        ship_locations[ship_id]['ship'], 
                        ship_locations[ship_id]['next_move'])))

    game.end_turn(command_queue)
