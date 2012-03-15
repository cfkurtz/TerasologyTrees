# -----------------------------------------------------------------------------------------------------------------
# Terasology Trees: A proof-of-concept dynamic object oriented tree generator for the Terasology project.

# Copyright 2012 Cynthia Kurtz <cfkurtz@kurtz-fernhout.com>.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------------------------------------------

import os, sys, random, math
import numpy as np

from trees_graphics import *
from trees_world import *

INDENT = '---->'

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class TreePart():
# The TreePart is the superclass for all parts of the tree. Only a few methods are common to all tree parts.
# For modeling growth, all parts have biomass, water and minerals, which get passed around the tree.
# For occupying space, all parts have a 3D matrix which stores their location and orientation,
# as well as a list of occupied blocks. 
# The blocks are meant to be the interface with the block-identity system in general,
# so that if you broke a block the tree could find out which of its parts that block belonged to
# and do something to that part (kill it or reduce its biomass) in response.
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

	def __init__(self, tree, parent, matrix, biomass=0, water=0, minerals=0):
		self.tree = tree
		self.parent = parent
		self.age = 0
		self.alive = True
		
		self.biomass = biomass
		self.water = water
		self.minerals = minerals
		
		self.matrix = matrix # should be new copy, not pointer to one already in use
		self.blocks = []
		
	def nextDay(self, updateBlocks):
		#print 'start', self.__class__.__name__, 'next day'
		# The next-day "signal" moves up the tree, with each part performing its daily calculations.
		# Internodes, being the "pipes" of the system, handle making sure every part finds out
		# about the signal.
		# To start out, each part relinquishes all blocks in the world-space it had been occupying,
		# on its way to claiming new blocks. In many cases parts will not move, but sometimes they will.
		#print 'start', self.__class__.__name__, 'releaseAllUsedBlocks'
		self.releaseAllUsedBlocks()
		# Uptake is of photosynthate (for leaf clusters) or water and minerals (for root internodes).
		#print 'start', self.__class__.__name__, 'nextDay_Uptake'
		self.nextDay_Uptake()
		# All tree parts use up a little biomass each day in maintenance respiration.
		#print 'start', self.__class__.__name__, 'nextDay_Consumption'
		self.nextDay_Consumption()
		# Leaf clusters distribute new biomass to internodes; internode distribution biomass,
		# water and minerals to their parents, children and dependents.
		#print 'start', self.__class__.__name__, 'nextDay_Distribution'
		self.nextDay_Distribution()
		# In the growth method each part calculates its updated size.
		#print 'start', self.__class__.__name__, 'nextDay_Growth'
		self.nextDay_Growth()
		# In the occupation method each part reclaims blocks in the space it should be occupying.
		#print 'start', self.__class__.__name__, 'nextDay_BlockOccupation'
		if updateBlocks:
			self.nextDay_BlockOccupation()
		# Finally the internodes tell their children about the next day signal.
		#print 'start', self.__class__.__name__, 'nextDay_SignalPropagation'
		self.nextDay_SignalPropagation(updateBlocks)
		#print '     end', self.__class__.__name__, 'next day'
		self.age += 1
		
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		pass
	
	def nextDay_Distribution(self):
		pass
	
	def nextDay_BlockOccupation(self):
		pass
	
	def nextDay_SignalPropagation(self, updateBlocks):
		pass
		
	def die(self):
		# When tree parts die, they don't fall off; they just change color (block ID).
		# This prevents parts of the tree from disappearing and allows for interesting
		# materials to be collected.
		self.alive = False
	
	def releaseAllUsedBlocks(self):
		for location in self.blocks:
			roundedLocation = location.rounded()
			releaseLocation(roundedLocation, self)
		self.blocks = []
		
	def claimStartBlock(self):
		roundedLocation = self.matrix.location.rounded()
		self.blocks = [roundedLocation]
		claimLocation(roundedLocation, self)
		
	def claimSeriesOfBlocks(self, locations, aboveGround=True):
		for location in locations:
			roundedLocation = location.rounded()
			# Normally you should bound each block location to make sure it doesn't extend beyond the space "box"
			# created. However, don't bound the start of the tree, because it was placed at the start.
			# Also, if the roots were bounded below ground bounding the top root location
			# will create a gap between stem and root which looks strange.
			# In an infinite-xy world this bounding would go away, but at the top/bottom of the world it would still apply.
			if location != self.tree.trunkMatrix.location and location != self.tree.rootMatrix.location:
				roundedLocation = boundLocation(roundedLocation, aboveGround)
			self.blocks.append(roundedLocation)
			claimLocation(roundedLocation, self)
				
	def describe(self, outputFile, indentCounter):
		outputFile.write(INDENT * indentCounter + ' %s: \n' % self.__class__.__name__)
		fields = self.__dict__
		for key in fields:
			valueAsString = "%s" % fields[key]
			if not valueAsString.find("instance") >= 0:
				outputFile.write(INDENT * (indentCounter+1) + key + ": " + valueAsString + "\n")
		outputFile.write("\n")

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class Meristem(TreePart):
	
# Meristems are buds. They are the part-making factories of the tree.
# They should be visible and take up a whole block, because trimming (snipping) meristems
# would be a way to manipulate the growth of the tree.
# An important distinction in meristems is whether they are apical, or at the apex (end
# of the stem), or axillary, or in the angle between leaf and stem (the axil). 
# When apical meristems develop they produce a longer stem.
# When axillary meristems develop they produce branches.

# Roots do not use separate classes, just a root flag in the meristem and internode.
# "numberOnParentInternode" remembers the order in which each element was placed.
# This is used to re-place it as the parent internode grows.
# "branchNestingLevel" keeps track of on which branch order (primary, secondary, tertiary, etc)
# the meristem/internode is found. This is used to select a branching angle, which is
# different off the main trunk or a subsidiary branch.
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

	def __init__(self, tree, parent, root, branchNestingLevel, numberOnParentInternode, matrix, apical=False, biomass=0, water=0, minerals=0):
		TreePart.__init__(self, tree, parent, matrix, biomass=START_MERISTEM_BIOMASS[root], water=0, minerals=0)
		self.apical = apical
		self.root = root
		self.numberOnParentInternode = numberOnParentInternode
		self.branchNestingLevel = branchNestingLevel
		self.active = False
		
		self.reproductive = False
		if self.tree.reproductivePhaseHasStarted:
			self.reproduce()
			
	# -------------------------------------------------------------------------------------------
	# creation of new parts
	# -------------------------------------------------------------------------------------------
		
	def buildInternode(self, firstOnTree=False):
		newMatrix = self.matrix.makeCopy()
		if self.apical:
			newBranchNestingLevel = self.branchNestingLevel
		else: 
			newBranchNestingLevel = self.branchNestingLevel + 1
		newInternode = Internode(self.tree, self.parent, self.root, newBranchNestingLevel, newMatrix, self.numberOnParentInternode,
								firstOnTree=firstOnTree, iAmABranchOffMyParent=not self.apical)
		if self.parent:
			if self.apical:
				self.parent.addChildInternode(newInternode)
			else:
				self.parent.addBranchInternode(newInternode)
		return newInternode
	
	def buildFlowerCluster(self):
		newMatrix = self.matrix.makeCopy()
		newFlowerCluster = FlowerCluster(self.tree, self.parent, self.numberOnParentInternode, self.apical, newMatrix)
		if self.parent:
			self.parent.addFlowerCluster(newFlowerCluster)
		
	# -------------------------------------------------------------------------------------------
	# next day methods
	# -------------------------------------------------------------------------------------------
		
	def nextDay_Uptake(self):
		if self.alive:
			if self.biomass - BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root] < MERISTEM_DIES_IF_BIOMASS_GOES_BELOW[self.root]:
				self.die()
			else:
				if self.apical:
					self.active = True
				else:
					self.calculateActivityLevel()
				if self.active:
					self.biomass -= BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root]
				
	def nextDay_Growth(self):
		if self.alive:
			if self.active:
				if self.reproductive:
					if self.biomass >= BIOMASS_TO_MAKE_ONE_FLOWER_CLUSTER:
						self.buildFlowerCluster()
						self.parent.removeMeristemThatMadeInternode(self)
				else:
					if self.biomass >= BIOMASS_TO_MAKE_ONE_PHYTOMER[self.root]:
						self.buildInternode()
						self.parent.removeMeristemThatMadeInternode(self)
						
	def nextDay_BlockOccupation(self):
		if self.apical:
			self.matrix = self.parent.matrixForApicalMeristemOrChildInternode(0)
		else:
			self.matrix = self.parent.matrixForAxillaryMeristemOrBranchInternode(self.numberOnParentInternode, 0)
		if DRAW_MERISTEMS:
			self.claimStartBlock()
		
	# -------------------------------------------------------------------------------------------
	# methods used by next day methods
	# -------------------------------------------------------------------------------------------
		
	def calculateActivityLevel(self):
		if self.alive and not self.active:
			if self.tree.numInternodesCreated <= MAX_NUM_INTERNODES_ON_TREE_EVER[self.root]:
				distance = self.distanceOfParentFromBranchApex()
				if distance > 0:
					if self.branchNestingLevel == 0:
						dominanceToConsider = APICAL_DOMINANCE_OFF_TRUNK[self.root] 
					else:
						dominanceToConsider = APICAL_DOMINANCE_NOT_OFF_TRUNK[self.root] 
					if dominanceToConsider > 0:
						distanceFactor = 1.0 * distance / dominanceToConsider
					else:
						distanceFactor = 1.0
					if self.branchNestingLevel == 0:
						probability = BRANCHING_PROBABILITY_OFF_TRUNK[self.root] * distanceFactor
					else:
						probability = BRANCHING_PROBABILITY_NOT_OFF_TRUNK[self.root] * distanceFactor
					probability = max(0.0, min(1.0, probability))
					randomNumber = random.random() 
					self.active = randomNumber < probability
					if self.active and not self.root and self.tree.reproductivePhaseHasStarted:
						self.reproduce()
		
	def distanceOfParentFromBranchApex(self):
		# this running up the branch is inefficient and may be able to be calculated less often and stored
		distance = 0
		internode = self.parent
		while internode:
			distance += 1
			internode = internode.child
		if internode and not internode.apicalMeristem: # apical meristem is missing, perhaps removed
			if self.branchNestingLevel == 0:
				distance = APICAL_DOMINANCE_OFF_TRUNK[self.root] + 1
			else:
				distance = APICAL_DOMINANCE_NOT_OFF_TRUNK[self.root] + 1 
		return distance
		
	def acceptBiomass(self, biomassOffered):
		if self.alive and self.active:
			biomassINeed = max(0, (BIOMASS_TO_MAKE_ONE_PHYTOMER[self.root] + BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root]) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
	
	def reproduce(self):
		if self.alive and not self.root:
			if self.apical:
				probabilityIWillTurnReproductive = PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE
			else:
				probabilityIWillTurnReproductive = PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE
			randomNumber = random.random()
			if randomNumber < probabilityIWillTurnReproductive:
				self.reproductive = True
			
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class Internode(TreePart):
	
# An internode is a section of stem between "nodes" where leaves and axillary meristems
# come off the stem. Together these make a phytomer or modular plant unit.
# Internodes are the plant's piping system: they transport water, minerals and plant sugars
# (here lumped in with plant tissues as "biomass") throughout the plant.
	
# The internode, being the primary relationship manager of the tree, is related to:
#	0 to 1 parent - the internode (always an internode) it came from (if there is none, it is the first on the tree)
#	0 to 1 children - the internode (always an internode) that follows from it on the same stem
#	0 to n branches - internodes that developed out of axillary meristems (which go away afterward)
# 	0 to n axillary meristems - that have not yet developed into branches (none if all have created branches)
#	0 to 1 apical meristem - that has not yet developed a child internode
#	1 to n leaf clusters - can't have zero of these, the number of specified by parameter only
#	0 to n flower clusters - could be apical or axillary; created by meristems
#	0 to n fruit clusters - which were flower clusters but moved on past that stage
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

	def __init__(self, tree, parent, root, branchNestingLevel, matrix, numberOnParentInternode, firstOnTree, iAmABranchOffMyParent):
		TreePart.__init__(self, tree, parent, matrix, biomass=START_INTERNODE_BIOMASS[root], water=0, minerals=0)
		self.child = None
		self.branches = []
		self.flowerClusters = []
		self.fruitClusters = []
		
		self.root = root
		self.firstOnTree = firstOnTree
		self.branchNestingLevel = branchNestingLevel
		
		self.iAmABranchOffMyParent = iAmABranchOffMyParent
		self.numberOnParentInternode = numberOnParentInternode
		
		self.tree.numInternodesCreated += 1
		if RANDOM_INTERNODE_SWAY[self.root] > 0:
			self.randomSway = random.randrange(RANDOM_INTERNODE_SWAY[self.root]) - RANDOM_INTERNODE_SWAY[self.root] // 2
		else:
			self.randomSway = 0
		
		self.woody = (INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS[self.root] == 0)
		if self.firstOnTree:
			self.length = FIRST_INTERNODE_LENGTH_AT_CREATION[self.root]
		else:
			self.length = INTERNODE_LENGTH_AT_CREATION[self.root]
		self.width = INTERNODE_WIDTH_AT_CREATION[self.root]
		self.endLocation = self.matrix.location
		
		if not self.root:
			self.buildLeafClusters()
		self.buildMeristems()
		
	# -------------------------------------------------------------------------------------------
	# creation of new parts
	# -------------------------------------------------------------------------------------------
		
	def buildMeristems(self):
		newApicalMatrix = self.matrixForApicalMeristemOrChildInternode(0)
		self.apicalMeristem = Meristem(self.tree, self, self.root, self.branchNestingLevel, 0, newApicalMatrix, apical=True)
		self.axillaryMeristems = []
		for meristemNumber in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			newAxillaryMatrix = self.matrixForAxillaryMeristemOrBranchInternode(meristemNumber, 0)
			newAxillaryMeristem = Meristem(self.tree, self, self.root, self.branchNestingLevel, meristemNumber, newAxillaryMatrix, apical=False)
			self.axillaryMeristems.append(newAxillaryMeristem)
		
	def buildLeafClusters(self):
		self.leafClusters = []
		for leafClusterNumber in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			newLeafMatrix = self.matrixForLeafCluster(leafClusterNumber, 0)
			newLeafCluster = LeafCluster(self.tree, self, leafClusterNumber, newLeafMatrix)
			self.leafClusters.append(newLeafCluster)
			
	def matrixForApicalMeristemOrChildInternode(self, randomSway):
		# new matrices have to be created every day, because the internode itself may have changed
		# in length as it grew (and in end location if it is woody and is seeking sun/water/minerals)
		# this is horribly inefficient and can most surely be improved in optimization
		newMatrix = self.matrix.makeCopy()
		newMatrix.setLocation(self.endLocation.x, self.endLocation.y, self.endLocation.z)
		newMatrix.move(1.0)
		newMatrix.rotateX(90)
		newMatrix.rotateY(randomSway)
		return newMatrix
	
	def matrixForAxillaryMeristemOrBranchInternode(self, numberOnParentInternode, randomSway):
		if self.branchNestingLevel == 0:
			sideAngle = ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK[self.root]
		else:
			sideAngle = ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK[self.root]
		sideAngle += randomSway
		return self.matrixForPartAttachedToInternodeEnd(numberOnParentInternode, -1.0, sideAngle)
	
	def matrixForLeafCluster(self, numberOnParentInternode, randomSway):
		sideAngle = LEAF_CLUSTER_ANGLE_WITH_STEM
		sideAngle += randomSway
		return self.matrixForPartAttachedToInternodeEnd(numberOnParentInternode, -2.0, sideAngle)
	
	def matrixForFlowerCluster(self, numberOnParentInternode, randomSway):
		sideAngle = FLOWER_CLUSTER_ANGLE_WITH_STEM
		sideAngle += randomSway
		return self.matrixForPartAttachedToInternodeEnd(numberOnParentInternode, -2.0, sideAngle)
	
	def matrixForFruitCluster(self, numberOnParentInternode, randomSway):
		sideAngle = FRUIT_CLUSTER_ANGLE_WITH_STEM
		sideAngle += randomSway
		return self.matrixForPartAttachedToInternodeEnd(numberOnParentInternode, -2.0, sideAngle)
	
	def matrixForPartAttachedToInternodeEnd(self, numberOnParentInternode, pullBack, sideAngle):
		newMatrix = self.matrix.makeCopy()
		newMatrix.setLocation(self.endLocation.x, self.endLocation.y, self.endLocation.z)
		newMatrix.move(pullBack)
		if AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 1:
			xRotation = 0
		elif AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 2:
			if numberOnParentInternode == 1:
				xRotation = 0
			else:
				xRotation = 180
		else:
			if numberOnParentInternode == 1:
				xRotation = 0
			else:
				xRotation = 90 * numberOnParentInternode
		if xRotation > 0:
			newMatrix.rotateX(xRotation)
		newMatrix.rotateY(sideAngle)
		if self.width == 1:
			newMatrix.move(1.0)
		else:
			newMatrix.move(self.width / 2)
		return newMatrix
		
	def addChildInternode(self, internode):
		self.child = internode
		
	def addBranchInternode(self, internode):
		self.branches.append(internode)
		
	def addFlowerCluster(self, flowerCluster):
		self.flowerClusters.append(flowerCluster)
				
	def addFruitCluster(self, fruitCluster):
		self.fruitClusters.append(fruitCluster)
				
	def removeMeristemThatMadeInternode(self, meristem):
		# after a meristem makes a new internode, it goes away
		# because it becomes the internode
		if meristem.apical:
			self.apicalMeristem = None
		else:
			self.axillaryMeristems.remove(meristem)
			
	def removeFlowerClusterThatMadeFruitCluster(self, flowerCluster):
		self.flowerClusters.remove(flowerCluster)
		
	# -------------------------------------------------------------------------------------------
	# next day methods
	# -------------------------------------------------------------------------------------------
		
	def nextDay_Uptake(self):
		if self.root and self.alive:
			x = int(round(self.endLocation.x))
			y = int(round(self.endLocation.y))
			z = int(round(self.endLocation.z))
			availableWater, locationsConsidered = waterOrMineralsInRegion("water", self.endLocation, ROOT_WATER_EXTRACTION_RADIUS)
			if availableWater > 0:
				for locationTuple in locationsConsidered:
					if water.has_key(locationTuple):
						waterAtLocation = water[locationTuple]
					else:
						waterAtLocation = 0
					if waterAtLocation > 0:
						waterExtractedFromLocation = ROOT_WATER_EXTRACTION_EFFICIENCY * waterAtLocation
						self.water += waterExtractedFromLocation
						water[locationTuple] -= waterExtractedFromLocation
			availableMinerals, locationsConsidered = waterOrMineralsInRegion("minerals", self.endLocation, ROOT_MINERAL_EXTRACTION_RADIUS)
			if availableMinerals > 0:
				for locationTuple in locationsConsidered:
					if minerals.has_key(locationTuple):
						mineralsAtLocation = minerals[locationTuple]
						if mineralsAtLocation > 0:
							mineralsExtractedFromLocation = ROOT_MINERAL_EXTRACTION_EFFICIENCY * mineralsAtLocation
							self.minerals += mineralsExtractedFromLocation
							minerals[locationTuple] -= mineralsExtractedFromLocation
	
	def nextDay_Consumption(self):
		if self.alive:
			if self.woody:
				biomassINeedToUseToday = 0
			else:
				biomassINeedToUseToday = BIOMASS_USED_BY_INTERNODE_PER_DAY[self.root]
			if self.biomass - biomassINeedToUseToday < INTERNODE_DIES_IF_BIOMASS_GOES_BELOW[self.root]:
				self.die()
			else:
				self.biomass -= biomassINeedToUseToday
	
	def nextDay_Distribution(self):
		if self.tree.prevailingStressCondition == "no stress":
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["no stress"][self.root]
			biomassSpread = BIOMASS_DISTRIBUTION_SPREAD["no stress"][self.root]
		elif self.tree.prevailingStressCondition == "low sun and shade":
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["low sun and shade"][self.root]
			biomassSpread = BIOMASS_DISTRIBUTION_SPREAD["low sun and shade"][self.root]
		elif self.tree.prevailingStressCondition in ["water", "minerals"]:
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["water or mineral stress"][self.root]
			biomassSpread = BIOMASS_DISTRIBUTION_SPREAD["water or mineral stress"][self.root]
		elif self.tree.prevailingStressCondition == "reproduction":
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["reproduction"][self.root]
			biomassSpread = BIOMASS_DISTRIBUTION_SPREAD["reproduction"][self.root]
		parts = self.gatherDistributees(biomassDistributionOrder)
		for part in parts:
			if part:
				extra = max(0, self.biomass - OPTIMAL_INTERNODE_BIOMASS[self.root] - BIOMASS_USED_BY_INTERNODE_PER_DAY[self.root])
				if extra > 0:
					toBeGivenAway = extra * biomassSpread
					taken = part.acceptBiomass(toBeGivenAway)
					self.biomass -= taken
		parts = self.gatherDistributees(WATER_DISTRIBUTION_ORDER[self.root])
		for part in parts:
			if part:
				extra = self.water
				if extra > 0:
					toBeGivenAway = extra * WATER_DISTRIBUTION_SPREAD_PERCENT[self.root] 
					taken = part.acceptWater(toBeGivenAway)
					self.water -= taken
		parts = self.gatherDistributees(MINERALS_DISTRIBUTION_ORDER[self.root])
		for part in parts:
			if part:
				extra = self.minerals
				if extra > 0:
					toBeGivenAway = extra * MINERALS_DISTRIBUTION_SPREAD_PERCENT[self.root] 
					taken = part.acceptMinerals(toBeGivenAway)
					self.minerals -= taken
				
	def nextDay_Growth(self):
		if self.alive:
			self.woody = self.age > INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS
			proportion = self.biomass / OPTIMAL_INTERNODE_BIOMASS[self.root]
			if self.firstOnTree:
				lengthICanGrow = FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE[self.root] - FIRST_INTERNODE_LENGTH_AT_CREATION[self.root]
				self.length = FIRST_INTERNODE_LENGTH_AT_CREATION[self.root] + proportion * lengthICanGrow
				self.length = max(FIRST_INTERNODE_LENGTH_AT_CREATION[self.root], min(FIRST_INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE[self.root], self.length))
			else:
				if self.branchNestingLevel == 0:
					maxLength = INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_TRUNK[self.root]
				else:
					maxLength = INTERNODE_GROWTH_IN_LENGTH_AT_FULL_SIZE_BRANCH[self.root]
				lengthICanGrow = maxLength - INTERNODE_LENGTH_AT_CREATION[self.root]
				self.length = INTERNODE_LENGTH_AT_CREATION[self.root] + proportion * lengthICanGrow
				self.length = max(INTERNODE_LENGTH_AT_CREATION[self.root], min(maxLength, self.length))
			widthICanGrow = INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE[self.root] - INTERNODE_WIDTH_AT_CREATION[self.root]
			self.width = INTERNODE_WIDTH_AT_CREATION[self.root] + proportion * widthICanGrow
			self.width = max(INTERNODE_WIDTH_AT_CREATION[self.root], min(INTERNODE_GROWTH_IN_WIDTH_AT_FULL_SIZE[self.root], self.width))

	def nextDay_BlockOccupation(self):
		aboveGround = not self.root
		if self.iAmABranchOffMyParent:
			self.matrix = self.parent.matrixForAxillaryMeristemOrBranchInternode(self.numberOnParentInternode, self.randomSway)
		else:
			if self.parent:
				self.matrix = self.parent.matrixForApicalMeristemOrChildInternode(self.randomSway)
		self.endLocation = self.matrix.calculateMove(self.length)
		self.endLocation = boundLocation(self.endLocation, aboveGround)
		if self.alive and not self.woody and NON_WOODY_INTERNODES_SEEK_RESOURCES_IN_RADIUS[self.root] > 0:
			self.endLocation = seekBetterLocation(self.endLocation, self.root, NON_WOODY_INTERNODES_SEEK_RESOURCES_IN_RADIUS[self.root])
		if (self.root and DRAW_ROOTS) or (not self.root and DRAW_STEMS):
			self.claimStartBlock()
			pointsBetween = self.length * INTERNODE_LINE_DRAWING_DETAIL_MULTIPLIER
			locationsBetween = locationsBetweenTwoPoints(self.matrix.location, self.endLocation, pointsBetween, INTERNODE_LINE_DRAWING_METHOD)
			self.claimSeriesOfBlocks(locationsBetween, aboveGround)
			if self.width > 1:
				for location in locationsBetween:
					turns = 4 + self.width//2
					diameterPattern = str(int(round(self.width/2)))
					circleLocations = locationsForShapeAroundSpine(locationsBetween, diameterPattern, turns, 1.0, INTERNODES_ARE_HOLLOW[self.root], self.matrix)
					self.claimSeriesOfBlocks(circleLocations, aboveGround)
								
	def nextDay_SignalPropagation(self, updateBlocks):
		sendSignalTo = []
		if not self.root:
			sendSignalTo.extend(self.leafClusters)
			sendSignalTo.extend(self.flowerClusters)
			sendSignalTo.extend(self.fruitClusters)
		sendSignalTo.extend([self.apicalMeristem])
		sendSignalTo.extend(self.axillaryMeristems)
		sendSignalTo.extend([self.child])
		sendSignalTo.extend(self.branches)
		for sendTo in sendSignalTo:
			if sendTo:
				sendTo.nextDay(updateBlocks)
		
	# -------------------------------------------------------------------------------------------
	# methods used by next day methods
	# the internode has several methods that propagate signals to other parts
	# -------------------------------------------------------------------------------------------
		
	def acceptBiomass(self, biomassOffered):
		# the internode, because it is a piping system, takes biomass it doesn't need so it can pass it on
		self.biomass += biomassOffered
		return biomassOffered
	
	def acceptWater(self, waterOffered):
		self.water += waterOffered
		return waterOffered
	
	def acceptMinerals(self, mineralsOffered):
		self.minerals += mineralsOffered
		return mineralsOffered
	
	def reproduce(self):
		if not self.root:
			sendSignalTo = []
			sendSignalTo.extend([self.apicalMeristem])
			sendSignalTo.extend(self.axillaryMeristems)
			sendSignalTo.extend([self.child])
			sendSignalTo.extend(self.branches)
			for sendTo in sendSignalTo:
				if sendTo:
					sendTo.reproduce()
					
	def die(self):
		# when an internode dies, everything that depends on it dies too (only makes sense)
		sendSignalTo = []
		if not self.root:
			sendSignalTo.extend(self.leafClusters)
			sendSignalTo.extend(self.flowerClusters)
			sendSignalTo.extend(self.fruitClusters)
		sendSignalTo.extend([self.apicalMeristem])
		sendSignalTo.extend(self.axillaryMeristems)
		sendSignalTo.extend([self.child])
		sendSignalTo.extend(self.branches)
		for sendTo in sendSignalTo:
			if sendTo:
				sendTo.die()
	
	def gatherDistributees(self, order):
		distributees = []
		for name in order:
			if name == "leaves":
				if not self.root:
					distributees.extend(self.leafClusters)
			elif name == "flowers":
				if not self.root:
					distributees.extend(self.flowerClusters)
			elif name == "fruits":
				if not self.root:
					distributees.extend(self.fruitClusters)
			elif name == "apical meristems":
				distributees.extend([self.apicalMeristem])
			elif name == "axillary meristems":
				distributees.extend(self.axillaryMeristems)
			elif name == "child":
				distributees.extend([self.child])
			elif name == "branches":
				distributees.extend(self.branches)
			elif name == "parent":
				distributees.extend([self.parent])
			elif name == "root":
				if (not self.root) and self.firstOnTree:
					distributees.extend([self.tree.firstRootInternode])
			elif name == "above-ground tree":
				if self.root and self.firstOnTree:
					distributees.extend([self.tree.firstInternode])
		return distributees
				
	def sumUpStresses(self):
		totalCount = 0
		totalLowSunAndShadeStress = 0
		totalLowWaterStress = 0
		totalLowMineralStress = 0
		sendSignalTo = []
		if not self.root:
			sendSignalTo.extend(self.leafClusters)
		sendSignalTo.extend([self.child])
		sendSignalTo.extend(self.branches)
		for sendTo in sendSignalTo:
			if sendTo:
				count, lowSunAndShadeStress, lowWaterStress, lowMineralStress = sendTo.sumUpStresses()
				totalCount += count
				totalLowSunAndShadeStress += lowSunAndShadeStress
				totalLowWaterStress += lowWaterStress
				totalLowMineralStress += lowMineralStress
		return totalCount, totalLowSunAndShadeStress, totalLowWaterStress, totalLowMineralStress
		
	def describe(self, outputFile, indentCounter=0):
		TreePart.describe(self, outputFile, indentCounter)
		sendSignalTo = []
		sendSignalTo.extend(self.branches)
		if not self.root:
			sendSignalTo.extend(self.leafClusters)
			sendSignalTo.extend(self.flowerClusters)
			sendSignalTo.extend(self.fruitClusters)
		sendSignalTo.extend([self.apicalMeristem])
		sendSignalTo.extend(self.axillaryMeristems)
		sendSignalTo.extend([self.child])
		for sendTo in sendSignalTo:
			if sendTo:
				sendTo.describe(outputFile, indentCounter+1)
			
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class LeafCluster(TreePart):
	
# Leaf clusters are what would be on an herbaceous (non-tree) plant simply leaves.
# Here, since one leaf block represents "lots and lots" of leaves, what is simulated
# is a cluster of leaves, or really the end of a branch with lots of little twigs
# and leaves.

# All photosynthesis happens in the leaf clusters, which require sunlight, water
# and minerals to carry this out. Parameters that control photosynthesis, and the
# tolerance of the plant to conditions of low light, drought and poor soils,
# are specified in reference to the leaves, since they impact tree growth mainly through photosynthesis.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

	def __init__(self, tree, parent, numberOnParentInternode, matrix):
		TreePart.__init__(self, tree, parent, matrix, biomass=START_LEAF_CLUSTER_BIOMASS, water=0, minerals=0)
		self.numberOnParentInternode = numberOnParentInternode
		self.length = LEAF_CLUSTER_LENGTH_AT_CREATION
		self.newBiomass = 0
		self.lowSunAndShadeStress = 0
		self.lowWaterStress = 0
		self.lowMineralStress = 0

		if RANDOM_LEAF_CLUSTER_SWAY > 0:
			self.randomSway = random.randrange(RANDOM_LEAF_CLUSTER_SWAY) - RANDOM_LEAF_CLUSTER_SWAY // 2
		else:
			self.randomSway = 0
		self.spineEndLocation = self.matrix.location
		
	# -------------------------------------------------------------------------------------------
	# next day methods
	# -------------------------------------------------------------------------------------------
		
	def nextDay_Uptake(self):
		if self.alive:
			if self.age >= LEAF_SENESCENCE_BEGINS_AT_AGE:
				ageOverSenescenceStart = self.age - LEAF_SENESCENCE_BEGINS_AT_AGE
				if ageOverSenescenceStart < LEAF_SENESCENCE_LASTS:
					self.senescenceFactor = 1.0 * ageOverSenescenceStart / LEAF_SENESCENCE_LASTS
				else:
					self.senescenceFactor = 0.0
			else:
				self.senescenceFactor = 1.0
			if self.senescenceFactor > 0:
				x = int(round(self.spineEndLocation.x))
				y = int(round(self.spineEndLocation.y))
				# there should not be a location outside of the sun space, but ...
				if sun.has_key((x,y)):
					sunAtEndOfLeafCluster = sun[(x,y)]
				else:
					sunAtEndOfLeafCluster = 0.0
					
				self.lowSunStress = math.exp(-math.pi * sunAtEndOfLeafCluster)
				self.numBlocksShadingMe = 1.0 - blocksOccupiedAboveLocation(self.matrix.location, self)
				if NUM_BLOCKS_ABOVE_FOR_MAX_SHADE_STRESS > 0:
					proportionOfMaxShade = max(0.0, min(1.0, 1.0 * self.numBlocksShadingMe / NUM_BLOCKS_ABOVE_FOR_MAX_SHADE_STRESS))
				else:
					proportionOfMaxShade = 0.0
				self.shadeStress = 1.0 - math.exp(-math.pi * proportionOfMaxShade)
				self.lowSunAndShadeStress = max(0.0, min(1.0, self.lowSunStress + self.shadeStress))
				
				proportionOfOptimalWater = max(0.0, min(1.0, self.water / WATER_FOR_OPTIMAL_PHOTOSYNTHESIS))
				self.lowWaterStress = math.exp(-math.pi * proportionOfOptimalWater)
				
				proportionOfOptimalMinerals = max(0.0, min(1.0, self.minerals / MINERALS_FOR_OPTIMAL_PHOTOSYNTHESIS))
				self.lowMineralStress = math.exp(-math.pi * proportionOfOptimalMinerals)
				
				proportionOfOptimalBiomass = max(0.0, min(1.0, self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS))
				lowBiomassFactor = math.exp(-math.pi * proportionOfOptimalBiomass)
				
				# the reason to make so many of these fields of the object is so you can look at them (using the describe method)
				# if anything is going wrong to see what is causing the tree not to grow
				# they do cause extra overhead however and could be stripped out of the object later
				self.lowSunAndShadeStressFactor = self.lowSunAndShadeStress * 0.25 * (1.0 - LOW_SUN_AND_SHADE_TOLERANCE)
				self.lowWaterStressFactor = self.lowWaterStress * 0.25 * (1.0 - WATER_STRESS_TOLERANCE)
				self.lowMineralStressFactor = self.lowMineralStress * 0.25 * (1.0 - MINERAL_STRESS_TOLERANCE)
				self.lowBiomassStressFactor = lowBiomassFactor * 0.25 # no tolerance; small leaves make less food!
				
				self.combinedEffects = 1.0 - (self.lowSunAndShadeStressFactor + self.lowWaterStressFactor + \
										self.lowMineralStressFactor + self.lowBiomassStressFactor)
				self.combinedEffects = self.combinedEffects * self.senescenceFactor
				self.combinedEffects = max(0.0, min(1.0, self.combinedEffects))
				
				self.newBiomass =  self.combinedEffects * OPTIMAL_DAILY_PHOTOSYNTHATE
				self.biomass += self.newBiomass
		else:
			self.newBiomass = 0
	
	def nextDay_Consumption(self):
		if self.alive:
			if self.biomass - BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY < LEAF_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW:
				self.die()
			else:
				self.biomass -= BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY

	def nextDay_Distribution(self):
		if self.alive:
			extraBiomass = max(0, self.biomass - OPTIMAL_LEAF_CLUSTER_BIOMASS)
			biomassTakenByParent = self.parent.acceptBiomass(extraBiomass)
			self.biomass -= biomassTakenByParent
	
	def nextDay_Growth(self):
		if self.alive:
			proportion = self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS
			self.length = LEAF_CLUSTER_LENGTH_AT_CREATION + proportion * (LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE - LEAF_CLUSTER_LENGTH_AT_CREATION)
			self.length = max(LEAF_CLUSTER_LENGTH_AT_CREATION, min(LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_BlockOccupation(self):
		if DRAW_LEAF_CLUSTERS:
			self.matrix = self.parent.matrixForLeafCluster(self.numberOnParentInternode, self.randomSway)
			if self.length > 1:
				self.spineEndLocation = self.matrix.calculateMove(self.length)
				spine = locationsBetweenTwoPoints(self.matrix.location, self.spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / LEAF_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE
				wings = locationsForShapeAroundSpine(spine, LEAF_CLUSTER_SHAPE_PATTERN, LEAF_CLUSTER_SIDES, sizeProportion, 
													LEAF_CLUSTERS_ARE_HOLLOW, self.matrix)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	# -------------------------------------------------------------------------------------------
	# methods used by next day methods
	# -------------------------------------------------------------------------------------------
		
	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_LEAF_CLUSTER_BIOMASS + BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
	def acceptWater(self, waterOffered):
		if self.alive:
			waterINeed = max(0, WATER_FOR_OPTIMAL_PHOTOSYNTHESIS - self.water)
		else:
			waterINeed = 0
		waterIWillAccept = min(waterOffered, waterINeed)
		self.water += waterIWillAccept
		return waterIWillAccept
	
	def acceptMinerals(self, mineralsOffered):
		if self.alive:
			mineralsINeed = max(0, MINERALS_FOR_OPTIMAL_PHOTOSYNTHESIS - self.minerals)
		else:
			mineralsINeed = 0
		mineralsIWillAccept = min(mineralsOffered, mineralsINeed)
		self.minerals += mineralsIWillAccept
		return mineralsIWillAccept
	
	def sumUpStresses(self):
		return 1, self.lowSunAndShadeStress, self.lowWaterStress, self.lowMineralStress
				
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class FlowerCluster(TreePart):
	
# A flower cluster is a lot like a leaf cluster: it represents lots of flowers. 
# Flower clusters, like fruit clusters, don't do anything on the tree except
# suck up biomass and present interesting things to harvest.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

	def __init__(self, tree, parent, numberOnParentInternode, apical, matrix):
		TreePart.__init__(self, tree, parent, matrix, biomass=START_FLOWER_CLUSTER_BIOMASS, water=0, minerals=0)
		self.numberOnParentInternode = numberOnParentInternode
		self.apical = apical
		self.length = FLOWER_CLUSTER_LENGTH_AT_CREATION
		if RANDOM_FLOWER_CLUSTER_SWAY > 0:
			self.randomSway = random.randrange(RANDOM_FLOWER_CLUSTER_SWAY) - RANDOM_FLOWER_CLUSTER_SWAY // 2
		else:
			self.randomSway = 0
		
	# -------------------------------------------------------------------------------------------
	# creation of new objects
	# -------------------------------------------------------------------------------------------
		
	def buildFruit(self):
		newFruitCluster = FruitCluster(self.tree, self.parent, self.numberOnParentInternode, self.matrix)
		self.parent.removeFlowerClusterThatMadeFruitCluster(self)
		self.parent.addFruitCluster(newFruitCluster)
				
	# -------------------------------------------------------------------------------------------
	# next day methods
	# -------------------------------------------------------------------------------------------
		
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY < FLOWER_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW:
			self.die()
		else:
			self.biomass -= BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY

	def nextDay_Growth(self):
		if self.age >= MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS and self.biomass >= OPTIMAL_FLOWER_CLUSTER_BIOMASS:
			self.buildFruit()
		else:
			proportion = self.biomass / OPTIMAL_FLOWER_CLUSTER_BIOMASS
			self.length = FLOWER_CLUSTER_LENGTH_AT_CREATION + proportion * (FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE - FLOWER_CLUSTER_LENGTH_AT_CREATION)
			self.length = max(FLOWER_CLUSTER_LENGTH_AT_CREATION, min(FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_BlockOccupation(self):
		if DRAW_FLOWER_CLUSTERS:
			self.matrix = self.parent.matrixForFlowerCluster(self.numberOnParentInternode, self.randomSway)
			if self.length > 1:
				spineEndLocation = self.matrix.calculateMove(self.length)
				spine = locationsBetweenTwoPoints(self.matrix.location, spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / FLOWER_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE
				wings = locationsForShapeAroundSpine(spine, FLOWER_CLUSTER_SHAPE_PATTERN, FLOWER_CLUSTER_SIDES, sizeProportion, 
													FLOWER_CLUSTERS_ARE_HOLLOW, self.matrix)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	# -------------------------------------------------------------------------------------------
	# methods used by next day methods
	# -------------------------------------------------------------------------------------------
		
	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_FLOWER_CLUSTER_BIOMASS + BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class FruitCluster(TreePart):
	
# Like flower clusters, these do nothing but look good and perhaps present something
# worth harvesting. They take up biomass but do nothing else.

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

	def __init__(self, tree, parent, numberOnParentInternode, matrix):
		TreePart.__init__(self, tree, parent, matrix, biomass=START_FRUIT_CLUSTER_BIOMASS, water=0, minerals=0)
		self.numberOnParentInternode = numberOnParentInternode
		self.length = FRUIT_CLUSTER_LENGTH_AT_CREATION
		if RANDOM_FRUIT_CLUSTER_SWAY > 0:
			self.randomSway = random.randrange(RANDOM_FRUIT_CLUSTER_SWAY) - RANDOM_FRUIT_CLUSTER_SWAY // 2
		else:
			self.randomSway = 0
		
	# -------------------------------------------------------------------------------------------
	# next day methods
	# -------------------------------------------------------------------------------------------
		
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY < FRUIT_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW:
			self.die()
		else:
			self.biomass -= BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY

	def nextDay_Growth(self):
		if self.alive:
			proportion = self.biomass / OPTIMAL_FRUIT_CLUSTER_BIOMASS
			self.length = FRUIT_CLUSTER_LENGTH_AT_CREATION + proportion * (FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE - FRUIT_CLUSTER_LENGTH_AT_CREATION)
			self.length = max(FRUIT_CLUSTER_LENGTH_AT_CREATION, min(FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_BlockOccupation(self):
		if DRAW_FRUIT_CLUSTERS:
			self.matrix = self.parent.matrixForFruitCluster(self.numberOnParentInternode, self.randomSway)
			if self.length > 1:
				spineEndLocation = self.matrix.calculateMove(self.length)
				spine = locationsBetweenTwoPoints(self.matrix.location, spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / FRUIT_CLUSTER_GROWTH_IN_LENGTH_AT_FULL_SIZE
				wings = locationsForShapeAroundSpine(spine, FRUIT_CLUSTER_SHAPE_PATTERN, FRUIT_CLUSTER_SIDES, sizeProportion, 
													FRUIT_CLUSTERS_ARE_HOLLOW, self.matrix)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	# -------------------------------------------------------------------------------------------
	# methods used by next day methods
	# -------------------------------------------------------------------------------------------
		
	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_FRUIT_CLUSTER_BIOMASS + BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
				
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
class Tree():
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

	def __init__(self, x, y, z):
		self.age = 0
		
		self.trunkMatrix = Matrix3D(0.0, 0.0, 0.0)
		self.trunkMatrix.initializeAsUnitMatrix()
		self.trunkMatrix.setLocation(x, y, z)
		self.trunkMatrix.rotateY(90)
		
		self.numInternodesCreated = 0
		self.numRootInternodesCreated = 0
		self.reproductivePhaseHasStarted = False
		self.prevailingStressCondition = "no stress"
		
		self.seed = random.random()
		random.seed(self.seed)
		
		self.rootMatrix = self.trunkMatrix.makeCopy()
		self.rootMatrix.rotateY(180)
		self.rootMatrix.move(1.0)

		firstMeristem = Meristem(self, None, False, 0, 0, self.trunkMatrix, apical=True)
		self.firstInternode = firstMeristem.buildInternode(firstOnTree=True)
		
		firstRootMeristem = Meristem(self, None, True, 0, 0, self.rootMatrix, apical=True)
		self.firstRootInternode = firstRootMeristem.buildInternode(firstOnTree=True)
		
	def nextDay(self, updateBlocks):
		if self.age == REPRODUCTIVE_MODE_STARTS_ON_DAY:
			self.reproductivePhaseHasStarted = True
			self.firstInternode.reproduce()
		self.firstInternode.nextDay(updateBlocks)
		self.firstRootInternode.nextDay(updateBlocks)
		self.calculateStresses()
		self.age += 1
		
	def calculateStresses(self):
		self.leafClusterCount, self.totalLowSunAndShadeStress, self.totalLowWaterStress, \
			self.totalLowMineralStress = self.firstInternode.sumUpStresses()
		highestStress = max(self.totalLowSunAndShadeStress, self.totalLowWaterStress, self.totalLowMineralStress)
		self.averageHighestStressPerLeaf = highestStress / self.leafClusterCount
		if self.averageHighestStressPerLeaf < MIN_STRESS_TO_TRIGGER_BIOMASS_REDISTRIBUTION:
			if self.reproductivePhaseHasStarted:
				self.prevailingStressCondition = "reproduction"
			else:
				self.prevailingStressCondition = "no stress"
		elif highestStress == self.totalLowSunAndShadeStress:
			self.prevailingStressCondition = "low sun and shade"
		elif highestStress == self.totalLowWaterStress:
			self.prevailingStressCondition = "water"
		elif highestStress == self.totalLowMineralStress:
			self.prevailingStressCondition = "minerals"
		
	def describe(self, outputFile):
		outputFile.write('%s: \n' % self.__class__.__name__)
		fields = self.__dict__
		fieldKeysSorted = []
		fieldKeysSorted.extend(fields.keys())
		fieldKeysSorted.sort()
		for key in fieldKeysSorted:
			valueAsString = str(fields[key])
			if not valueAsString.find("instance") >= 0:
				outputFile.write('    ' + key + ": " + valueAsString + "\n")
		outputFile.write("\n")
		self.firstInternode.describe(outputFile)
		self.firstRootInternode.describe(outputFile)
		
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
def growTree(outputFolder):
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	drawGraphs = False
	if drawGraphs:
		print 'writing distribution graphs...'
		drawSunDistribution(outputFolder)
		if PATCHY_WATER:
			drawWaterDistribution(outputFolder)
		if PATCHY_MINERALS:
			drawMineralsDistribution(outputFolder)
	describeTrees = True
	if describeTrees:
		outputFileName = outputFolder + 'Tree growth recording.txt'
		outputFile = open(outputFileName, 'w')
	try:
		numTrees = 1
		print 'starting simulated growth with %s tree(s)...' % numTrees
		daysPerPulse = 1
		numPulses = 40
		trees = []
		for i in range(numTrees):
			if numTrees == 1:
				xLocation = 50
				yLocation = 50
			else:
				xLocation = 10 + random.randrange(80)
				yLocation = 10 + random.randrange(80)
			zLocation = GROUND_LEVEL+1
			newTree = Tree(xLocation, yLocation, zLocation)
			trees.append(newTree)
		if describeTrees:
			outputFile.write("Day zero\n\n")
			for tree in trees:
				tree.describe(outputFile)
		day = 1
		for i in range(numPulses):
			for j in range(daysPerPulse):
				print 'simulating day', day
				if describeTrees:
					outputFile.write("Day %s\n\n" % day)
				for tree in trees:
					dayToDraw = j == daysPerPulse-1
					tree.nextDay(updateBlocks=True)
					if describeTrees:
						tree.describe(outputFile)
					day += 1
			print '  drawing space on day %s...' % (day-1)
 			drawSpace(day-1, outputFolder, drawTrees=True)#, drawSun=True, drawWater=True, drawMinerals=True, drawSurface=True)
	finally:
		if describeTrees:
			outputFile.close()
	print 'done'
	
def main():
	global SPECIES
	loopThroughSpecies = True
	specimensPerSpecies = 5
	if loopThroughSpecies:
		for aSpecies in ALL_SPECIES:
			SPECIES = aSpecies
			for i in range(specimensPerSpecies):
				outputFolder = setUpOutputFolder("/Users/cfkurtz/Documents/personal/terasology/generated images/")
				print 'writing files to:', outputFolder
				space.clear()
				growTree(outputFolder)
	else:
		outputFolder = setUpOutputFolder("/Users/cfkurtz/Documents/personal/terasology/generated images/")
		print 'writing files to:', outputFolder
		space.clear()
		growTree(outputFolder)
	
if __name__ == "__main__":
	#import profile
	#profile.run('main()', 'profiletest')
	main()
	
