# This is a very simple Python 2.7 implementation of the Information Set Monte Carlo Tree Search algorithm.
# The function ISMCTS(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a 
# state.GetRandomMove() or state.DoRandomRollout() function.
# 
# An example GameState classes for Knockout Whist is included to give some idea of how you
# can write your own GameState to use ISMCTS in your hidden information game.
# 
# Written by Peter Cowling, Edward Powley, Daniel Whitehouse (University of York, UK) September 2012 - August 2013.
# 
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
# 
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai
# Also read the article accompanying this code at ***URL HERE***

from math import *
import random, sys
from copy import deepcopy
from api import State, util
import random
from argparse import ArgumentParser

class Node:
	""" A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
	"""
	def __init__(self, move = None, parent = None):
		self.move = move # the move that got us to this node - "None" for the root node
		self.parentNode = parent # "None" for the root node
		self.childNodes = []
		self.wins = 0
		self.winsRave = 0
		self.visits = 0
		self.visitsRave = 0
		self.avails = 1
	
	def GetUntriedMoves(self, legalMoves):
		""" Return the elements of legalMoves for which this node does not have children.
		"""
		
		# Find all moves for which this node *does* have children
		triedMoves = [child.move for child in self.childNodes]
		
		# Return all moves that are legal but have not been tried yet
		return [move for move in legalMoves if move not in triedMoves]
		
	def getBeta(self, n, nTilde, b = 2):
		return nTilde / (n + nTilde + 4 * (b * b * n * nTilde))

	def UCBSelectChild(self, legalMoves, ratio_points, exploration = 0.00000065, b = 2):
		""" Use the UCB1 formula to select a child node, filtered by the given list of legal moves.
			exploration is a constant balancing between exploitation and exploration, with default value 0.7 (approximately sqrt(2) / 2)
		"""
		# Filter the list of children by the list of legal moves
		legalChildren = [child for child in self.childNodes if child.move in legalMoves]
		
		# Get the child with the highest UCB score
		#s = max(legalChildren, key = lambda c: float(c.wins)/float(c.visits))
		#  s = max(legalChildren, key = lambda c: ((1 - self.getBeta(c.visits, getNodeStatistic(nodeStatistics, c).n)) * float(c.wins)/float(c.visits)) +
		#   										(self.getBeta() * float(c.wins)/float(c.visits)) +
		#   										exploration * sqrt(log(c.avails)/float(c.visits)))
		s = legalChildren[0] if len(legalChildren) > 0 else None
		UCB = float('-inf')
		for legalChild in legalChildren:
			nodeStatistic = getNodeStatistic(nodeStatistics, legalChild)
			beta = self.getBeta(legalChild.visits, nodeStatistic.visits, b)
			winVisitRatio = float(legalChild.wins) / float(legalChild.visits)
			winVisitRatioRave = float(nodeStatistic.wins) / float(nodeStatistic.visits)

			testUCB = ((1 - beta) * winVisitRatio) + (beta * winVisitRatioRave) + (exploration * sqrt(log(legalChild.avails) / float(legalChild.visits)))
			if testUCB > UCB:
				s = legalChild
				UCB = testUCB
		# s = max(legalChildren, key = lambda c: float(c.wins)/float(c.visits) + exploration * sqrt(log(c.avails)/float(c.visits)))
		#print(key(legalChildren))
		
		# Update availability counts -- it is easier to do this now than during backpropagation
		for child in legalChildren:
			child.avails += 1
		
		# Return the child selected above
		return s
	
	def AddChild(self, m, p):
		""" Add a new child node for the move m.
			Return the added child node
		"""
		n = None
		if self.parentNode == None or self.parentNode.move == None or self.parentNode.move != m:
			n = Node(move = m, parent = self)
			self.childNodes.append(n)
		return n

	def Update(self, player, winner, points):
		""" Update this node - increment the visit count by one, and increase the win count by the result of terminalState for self.playerJustMoved.
		"""
		self.visits += 1
		self.wins += points if player == winner else 0
		#self.wins += 1 if player == winner else 0

	def __repr__(self):
		return "[M:%s W/V/A: %4i/%4i/%4i]" % (self.move, self.wins, self.visits, self.avails)

	def TreeToString(self, indent):
		""" Represent the tree as a string, for debugging purposes.
		"""
		s = self.IndentString(indent) + str(self)
		for c in self.childNodes:
			s += c.TreeToString(indent+1)
		return s

	def IndentString(self,indent):
		s = "\n"
		for i in range (1,indent+1):
			s += "| "
		return s

	def ChildrenToString(self):
		s = ""
		for c in self.childNodes:
			s += str(c) + "\n"
		return s

class NodeStatistic:
	def __init__(self, node):
		self.node 		= node
		self.visits 	= self.wins = 0

def getNodeStatistic(NodeStatisticList, node):
	for nodeStatistic in NodeStatisticList:
		if node.move == nodeStatistic.node.move:
			return nodeStatistic
	return None

nodeStatistics 	= []
class Bot:
	def __init__(self, exploration = None, b = None):
		self.exploration = 1.3137354769499265 if exploration == None else exploration
		self.b = 2 if b == None else b
		# print(self.exploration)
		# print(self.b)

	def ISMCTS(self, rootstate, itermax, player, exploration, b, verbose = False):
		""" Conduct an ISMCTS search for itermax iterations starting from rootstate.
			Return the best move from the rootstate.
		"""
		rootnode 		= Node()
		for _ in range(itermax):
			node = rootnode
			
			# Determinize
			state_clone = rootstate.make_assumption() if rootstate.get_phase() == 1 else rootstate.clone()
			
			# Select
			moves = state_clone.moves()
			while moves != [] and node.GetUntriedMoves(moves) == []: # node is fully expanded and non-terminal
				node = node.UCBSelectChild(moves, util.ratio_points(state_clone, player), exploration = exploration, b = b)
				if not state_clone.finished():
					state_clone = state_clone.next(node.move)
				moves = state_clone.moves()
					
			# Expand
			untriedMoves = node.GetUntriedMoves(moves)
			if untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
				m = random.choice(untriedMoves)
				if not state_clone.finished():
					state_clone = state_clone.next(m)
				prevNode = node
				tempNode = node.AddChild(m, player)
				node = tempNode if tempNode != None else prevNode # add child and descend tree

			# Simulate
			moves = state_clone.moves()
			while moves != [] and not state_clone.finished(): # while state is non-terminal
				state_clone = state_clone.next(random.choice(moves))
				moves = state_clone.moves()

			# Backpropagate
			while node != None: # backpropagate from the expanded node and work back to the root node
				winner, points = state_clone.winner()

				node.Update(player, winner, points)
				nodeStatistic = getNodeStatistic(nodeStatistics, node)
				if nodeStatistic != None:
					nodeStatistic.visits += 1
					nodeStatistic.wins += points if winner == player else 0
				else:
					newNodeStatistic = NodeStatistic(node)
					newNodeStatistic.visits += 1
					newNodeStatistic.wins += points if winner == player else 0
					nodeStatistics.append(newNodeStatistic)
					nodeStatistic = getNodeStatistic(nodeStatistics, node)
				#print("Node move: {}, wins: {}, winsRave: {}, visits: {}, visitsRave: {}".format(node.move, node.wins, nodeStatistic.wins, node.visits, nodeStatistic.visits))
				node = node.parentNode

			# Output some information about the tree - can be omitted
			# if (verbose): print(rootnode.TreeToString(0))
			# else: print(rootnode.ChildrenToString())
		#print("NodeStatisticLen: {}".format(len(nodeStatistics)))
		return max(rootnode.childNodes, key = lambda c: c.visits).move # return the move that was most visited

	def get_move(self, state):
		""" Play a sample game between two ISMCTS players.
		"""	
		# Use different numbers of iterations (simulations, tree nodes) for different players
		player = state.whose_turn()
		if state.get_points(player) == 0 and state.get_points(util.other(player)) == 0: # First round of the game
			nodeStatistics = []
		res = self.ISMCTS(state, 200, player, self.exploration, self.b, verbose = False)
		return res