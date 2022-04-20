'''
    MyBot-Our tactic will be to firstly get rid of all cards not of trump-suit
    and then the lowest cards.
'''
# Import the API objects
from api import State
from api import Deck
import random


class Bot:

    def __init__(self):
        pass

    def get_lowest_card(self,moves):
        chosen_move = moves[0]
        for index, move in enumerate(moves):
			if move[0] is not None and move[0] % 5 >= chosen_move[0] % 5:
				chosen_move = move
        return chosen_move

    def get_move(self, state):
        moves = state.moves()
        chosen_move=moves[0]
        moves_not_trump_suit = []

        for index, move in enumerate(moves):
			if move[0] is not None and Deck.get_suit(move[0]) != state.get_trump_suit():
				moves_not_trump_suit.append(move)

        if len(moves_not_trump_suit) > 0:
			chosen_move = self.get_lowest_card(moves_not_trump_suit)
        
        else:
            chosen_move = self.get_lowest_card(moves)

        return chosen_move