#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction, Position

# This library allows you to generate random numbers.
import random
import numpy as np
# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging
from collections import OrderedDict, defaultdict
import sys

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

class Registry:
    def __init__(self):
        self.ships = {}
        self.busy_turns = defaultdict(int)
    def __getitem__(self, ship):
        return self.ships.get(ship.id, None)
    def __setitem__(self, ship, item):
        self.ships[ship.id] = item
    def busy(self, ship):
        return self[ship] is not None and self[ship] != ship.position
    def done(self, ship):
        self[ship] = None
    def mark_busy(self, ship):
        self.busy_turns[ship.id] += 1
    def stuck(self, ship):
        return self.busy_turns[ship.id] > 4

reg = Registry()

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map
    ships = me.get_ships()

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []
    dropoffs = 0
    for ship in ships:
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.

        surrounding = ship.position.get_surrounding_cardinals()
        nearby_entities = [p for p in surrounding if game_map[p].is_occupied]

        if reg.stuck(ship):
            # reg.done(ship)
            pass

        # dangerously close to everyone
        if len(nearby_entities) > 2:
            if dropoffs == 0 and ship.halite_amount > constants.DROPOFF_COST:
                ship.make_dropoff()
                command_queue.append(ship.move(move))
            else:
                potential_moves = [p for p in surrounding if not game_map[p].is_occupied]
                choice = random.choice(potential_moves)
                game_map[choice].mark_unsafe(choice)
                move = game_map.get_unsafe_moves(ship.position, choice)[0]
                print("ship {} avoiding others => {} by going {} {}".format(ship.id, nearby_entities[0], move, choice), file=open("log1", "a"))
                command_queue.append(ship.move(move))
        elif ship.destination is not None and ship.destination == ship.position:
            print("ship {} arrived!!!: {} ({})".format(ship.id,reg[ship], ship.position), file=open("log1", "a"))
            reg.done(ship)
            command_queue.append(ship.stay_still())
        elif reg.busy(ship):
            reg.mark_busy(ship)
            print("ship {} busy => {} (at {})".format(ship.id, reg[ship], ship.position), file=open("log1", "a"))
            command_queue.append(ship.move(game_map.naive_navigate(ship, reg[ship])))
        elif ship.is_full:
            print("ship {} full, going to shipyard ({})".format(ship.id,me.shipyard.position), file=open("log1", "a"))
            reg[ship] = me.shipyard.position
            command_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))
        elif game_map[ship.position].halite_amount < constants.MAX_HALITE / 10:
            xr = range(ship.position.x-5, ship.position.x+5)
            yr = range(ship.position.y-5, ship.position.x+5)

            taken_positions = filter(lambda x: x is not None, reg.ships.values())
            nearby_positions = [Position(x,y) for x in xr for y in yr]
            available_positions = [p for p in nearby_positions if p not in taken_positions]
            halite_amounts = [game_map[pos].halite_amount for pos in available_positions]
            if len(halite_amounts):
                best_position = available_positions[np.argmax(halite_amounts)]
                # reset = Position(0,0)
                reg[ship] = best_position
                # choice = random.choice([reset, best_position])
                print("ship {} exploring to {}".format(ship.id,best_position), file=open("log1", "a"))
                command_queue.append(ship.move(game_map.naive_navigate(ship, best_position)))
            else:
                print("ship {} staying still because there's nowhere good to go".format(ship.id), file=open("log1", "a"))
                command_queue.append(ship.stay_still())    
        else:
            print("ship {} absorbing halite".format(ship.id), file=open("log1", "a"))
            command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

