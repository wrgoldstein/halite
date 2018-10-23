#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

# This library allows you to generate random numbers.
import random

# Logging allows you to save messages for yourself. This is required because the regular STDOUT

import logging
logging.basicConfig(filename='mybot2.log',level=logging.DEBUG)

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map
    logging.info("Turn number {}".format(game.turn_number))
    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    for ship in me.get_ships():
        # a better way to find good halite!
        # better avoiding collisions (maybe not possible efficiently)
        # 
        if game.turn_number > constants.MAX_TURNS - 20:
            
            if ship.position == me.shipyard.position:
              direction = 'o'
            else:
              direction = game_map.dangerous_navigate(ship, me.shipyard.position)
            command_queue.append(ship.move(direction))

        elif ship.position == me.shipyard.position:
            
            direction = game_map.evasive_maneuvers(ship)
            command_queue.append(ship.move(direction))
        
        elif ship.halite_amount < (1.00/constants.MOVE_COST_RATIO) * game_map[ship.position].halite_amount:
            
            command_queue.append(ship.stay_still())

        elif ship.halite_amount > .75*constants.MAX_HALITE:
            
            direction = game_map.less_naive_navigate(ship, me.shipyard.position)
            command_queue.append(ship.move(direction))
        
        elif sum([1 if game_map[c].is_occupied else 0 for c in ship.position.get_surrounding_cardinals()]) > 2:
            direction = game_map.evasive_maneuvers(ship)
            command_queue.append(ship.move(direction))
            
        elif game_map[ship.position].halite_amount < constants.MAX_HALITE * .05:
            surrounds = ship.position.get_n_surrounding_cardinals(5)
            safe_positions = [p for p in surrounds if not game_map[p].is_occupied]
            sorted_positions = sorted(safe_positions, key=lambda p: -game_map[p].halite_amount)
            direction = game_map.less_naive_navigate(ship, sorted_positions[0])
            
            command_queue.append(ship.move(direction))
        else:
            command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= .3*constants.MAX_TURNS and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

