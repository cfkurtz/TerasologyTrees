# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

import os, sys, random, math
import numpy as np

from trees_graphics import *
from trees_world import *
from trees_turtle import *

# -------------------------------------------------------------------------------------------
# TO DO
# -------------------------------------------------------------------------------------------

# DONE set up sequenced output dirs
# DONE make branches have non-perpendicular angles
# DONE make non-woody stems photosynthesize, a little
# DONE improve photosynthesis - use sun array
# DONE draw sun array on graph
# DONE add apical dominance
# DONE make absolute limit on how many internodes can be created - to prevent params blowing up
# DONE use s curve for photosynthesis
# DONE??? put random number on seed unique to tree
# FIXED problem: gaps
# DONE add internode width
# DONE add leafCluster petiole and leafCluster shape
# DONE add leafCluster angle with stem
# DONE put in root growth
# DONE do water and nutrient uptake - water and nutrient grids, like sun grid
# DONE add seeking behavior for internodes (stem and root)
# DONE put in flower and fruit clusters

# add limits on parameters (in comments)
# do several parameter sets
# make code more clear with many comments
# write comment on board
# upload to git repository?

# NOT DOING think about collision avoidance and growth around occupied blocks

# -------------------------------------------------------------------------------------------
class TreePart():
# the TreePart is the superclass for all parts of the tree. only a few methods are common to all tree parts.
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, matrix, biomass=0, water=0, minerals=0):
		self.tree = tree
		self.parent = parent
		self.age = 0
		self.alive = True
		
		self.biomass = biomass
		self.water = water
		self.minerals = minerals
		
		self.matrix = matrix.makeCopy() #cfk check if need this
		self.blocks = []
		
	def nextDay(self):
		self.releaseAllUsedBlocks()
		self.nextDay_Uptake()
		self.nextDay_Consumption()
		self.nextDay_Distribution()
		self.nextDay_Growth()
		self.nextDay_Drawing()
		self.nextDay_SignalPropagation()
		self.age += 1
		
	def die(self):
		self.alive = False
	
	def releaseAllUsedBlocks(self):
		for location in self.blocks:
			releaseLocation(location, self)
		self.blocks = []
		
	def claimStartBlock(self):
		self.blocks = [self.matrix.location]
		claimLocation(self.matrix.location, self)
		
	def claimSeriesOfBlocks(self, locations):
		for location in locations:
			if not location in self.blocks:
				self.blocks.append(location)
				claimLocation(location, self)
				
	def describe(self, outputFile, indentCounter):
		outputFile.write(INDENT * indentCounter + ' %s: \n' % self.__class__.__name__)
		fields = self.__dict__
		#fieldKeysSorted.sort()
		for key in fields:
			valueAsString = str(fields[key])
			if not valueAsString.find("instance") >= 0:
				outputFile.write(INDENT * (indentCounter+1) + key + ": " + valueAsString + "\n")
		outputFile.write("\n")

# -------------------------------------------------------------------------------------------
class Meristem(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, root, branchNestingLevel, numberOnInternode, location, forward, side, apical=False, biomass=0, water=0, minerals=0):
		TreePart.__init__(self, tree, parent, location, forward, side, biomass=START_MERISTEM_BIOMASS[root], water=0, minerals=0)
		self.apical = apical
		self.root = root
		self.numberOnInternode = numberOnInternode
		self.branchNestingLevel = branchNestingLevel
		self.active = False
		
		self.reproductive = False
		if self.tree.reproductivePhaseHasStarted:
			self.reproduce()
		
	def buildInternode(self, firstOnTree=False):
		if self.apical:
			newSide = rotateAround(self.forward, self.side, 1)
			if self.parent:
				parentBranchForward = self.parent.parentBranchForward
			else: # parent may be first on plant
				if self.root:
					parentBranchForward = "down"
				else:
					parentBranchForward = "up"
			newBranchNestingLevel = self.branchNestingLevel
		else: 
			newSide = self.side
			parentBranchForward = self.parent.forward
			newBranchNestingLevel = self.branchNestingLevel + 1
			#print self.branchNestingLevel, newBranchNestingLevel
		firstOnBranch = firstOnTree or not self.apical
		newInternode = Internode(self.tree, self.parent, self.root, newBranchNestingLevel, self.matrix.location, self.forward, newSide, 
								firstOnTree=firstOnTree, firstOnBranch=firstOnBranch, parentBranchForward=parentBranchForward,
								iAmABranchOffMyParent=not self.apical)
		if self.parent:
			if self.apical:
				self.parent.addChildInternode(newInternode)
			else:
				self.parent.addBranchInternode(newInternode)
		return newInternode
	
	def buildFlowerCluster(self):
		if self.apical:
			newSide = rotateAround(self.forward, self.side, 1)
		else:   
			if self.parent:
				newSide = self.side
			else:
				newSide = self.tree.firstInternodeSideDirection
		newFlowerCluster = FlowerCluster(self.tree, self.parent, self.numberOnInternode, self.apical, self.matrix.location, self.forward, newSide)
		if self.parent:
			self.parent.addFlowerCluster(newFlowerCluster)
		
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
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
				
	def nextDay_Distribution(self):
		pass
	
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
						
	def nextDay_Drawing(self):
		if self.apical:
			location = self.parent.locationForApicalMeristem()
		else:
			location, forward, side = self.parent.locationAndDirectionsForAxillaryMeristem(self.numberOnInternode)
		self.matrix.location = location
		if DRAW_MERISTEMS:
			self.claimStartBlock()
		
	def calculateActivityLevel(self):
		if self.alive and not self.active:
			if self.tree.numInternodesCreated <= MAX_NUM_INTERNODES_ON_TREE_EVER[self.root]:
				distance = self.distanceOfParentFromBranchApex()
				if distance > 0:
					if APICAL_DOMINANCE_EXTENDS_FOR[self.root] > 0:
						distanceFactor = 1.0 * distance / APICAL_DOMINANCE_EXTENDS_FOR[self.root]
					else:
						distanceFactor = 1.0
					probability = BRANCHING_PROBABILITY[self.root] * distanceFactor
					probability = max(0.0, min(1.0, probability))
					randomNumber = random.random() 
					self.active = randomNumber < probability
					if self.active and not self.root and self.tree.reproductivePhaseHasStarted:
						self.reproduce()
		
	def distanceOfParentFromBranchApex(self):
		distance = 0
		internode = self.parent
		while internode:
			distance += 1
			internode = internode.child
		if internode and not internode.apicalMeristem: # apical meristem is missing, perhaps removed
			distance = APICAL_DOMINANCE_EXTENDS_FOR[self.root] + 1 # you can develop if the apex was removed
		return distance
		
	def nextDay_SignalPropagation(self):
		pass
	
	def acceptBiomass(self, biomassOffered):
		if self.alive and self.active:
			biomassINeed = max(0, (BIOMASS_TO_MAKE_ONE_PHYTOMER[self.root] + BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root]) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
	
	def reproduce(self):
		#print 'in meristem reproduce', self.alive, self.root
		if self.alive and not self.root:
			if self.apical:
				probabilityIWillTurnReproductive = PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE
			else:
				probabilityIWillTurnReproductive = PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE
			randomNumber = random.random()
			#print probabilityIWillTurnReproductive, randomNumber
			if randomNumber < probabilityIWillTurnReproductive:
				self.reproductive = True
			
# -------------------------------------------------------------------------------------------
class Internode(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, root, branchNestingLevel, location, forward, side, firstOnTree, firstOnBranch, parentBranchForward, iAmABranchOffMyParent):
		TreePart.__init__(self, tree, parent, location, forward, side, biomass=START_INTERNODE_BIOMASS[root], water=0, minerals=0)
		self.child = None
		self.branches = []
		self.flowerClusters = []
		self.fruitClusters = []
		
		self.root = root
		self.firstOnTree = firstOnTree
		self.firstOnBranch = firstOnBranch
		self.branchNestingLevel = branchNestingLevel
		
		self.parentBranchForward = parentBranchForward
		self.iAmABranchOffMyParent = iAmABranchOffMyParent
		
		self.tree.numInternodesCreated += 1
		self.randomSway = random.randrange(RANDOM_INTERNODE_SWAY[self.root]) - RANDOM_INTERNODE_SWAY[self.root] // 2
		
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
		
	def buildMeristems(self):
		location = self.matrix.locationForApicalMeristem()
		self.apicalMeristem = Meristem(self.tree, self, self.root, self.branchNestingLevel, 0, location, self.forward, self.side, apical=True)
		self.axillaryMeristems = []
		for i in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			location, forward, side = self.matrix.locationAndDirectionsForAxillaryMeristem(i)
			newAxillaryMeristem = Meristem(self.tree, self, self.root, self.branchNestingLevel, i, location, forward, side, apical=False)
			self.axillaryMeristems.append(newAxillaryMeristem)
		
	def buildLeafClusters(self):
		self.leafClusters = []
		for i in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			location, forward, side = self.matrix.locationAndDirectionsForLeafCluster(i)
			newLeafCluster = LeafCluster(self.tree, self, i, location, forward, side)
			self.leafClusters.append(newLeafCluster)
			
	def locationForApicalMeristem(self):
		aboveGround = not self.root
		locationOneFurther = displacementInDirection(self.endLocation, self.forward, 1, aboveGround)
		return locationOneFurther
	
	def locationAndDirectionsForAxillaryMeristem(self, meristemNumber):
		aboveGround = not self.root
		if AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 1:
			meristemForward = self.side
		elif AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 2:
			if meristemNumber == 1:
				meristemForward = self.side
			else:
				meristemForward = rotateAround(self.forward, self.side, 2)
		else:
			if meristemNumber == 1:
				meristemForward = self.side
			else:
				meristemForward = rotateAround(self.forward, self.side, meristemNumber)
		location = displacementInDirection(self.endLocation, meristemForward, self.width//2, aboveGround)
		meristemSide = self.forward
		return location, meristemForward, meristemSide
		
	def locationAndDirectionsForLeafCluster(self, leafClusterNumber):
		locationOneDownFromEnd = displacementInDirection(self.endLocation, self.forward, -1)
		if AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 1:
			leafClusterForward = self.side
		elif AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 2:
			if leafClusterNumber == 1:
				leafClusterForward = self.side
			else:
				leafClusterForward = rotateAround(self.forward, self.side, 2)
		else:
			if leafClusterNumber == 1:
				leafClusterForward = self.side
			else:
				leafClusterForward = rotateAround(self.forward, self.side, leafClusterNumber)
		location = displacementInDirection(locationOneDownFromEnd, leafClusterForward, self.width//2)
		leafClusterSide = self.forward
		# looks strange if leafClusters don't point to the side
		# cfk keep this?
		if leafClusterSide in ["up", "down"]:
			leafClusterSide = rotateAround(leafClusterForward, leafClusterSide, 1)
		return location, leafClusterForward, leafClusterSide
	
	def locationForChildInternode(self):
		aboveGround = not self.root
		locationOneFurther = displacementInDirection(self.endLocation, self.forward, 1, aboveGround)
		return locationOneFurther
		
	def addChildInternode(self, internode):
		self.child = internode
		
	def addBranchInternode(self, internode):
		self.branches.append(internode)
		
	def addFlowerCluster(self, flowerCluster):
		self.flowerClusters.append(flowerCluster)
				
	def addFruitCluster(self, fruitCluster):
		self.fruitClusters.append(fruitCluster)
				
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
	
	def removeMeristemThatMadeInternode(self, meristem):
		if meristem.apical:
			self.apicalMeristem = None
		else:
			self.axillaryMeristems.remove(meristem)
			
	def removeFlowerClusterThatMadeFruitCluster(self, flowerCluster):
		self.flowerClusters.remove(flowerCluster)
		
	def nextDay_Uptake(self):
		if self.alive:
			if self.root:
				availableWater, locationsConsidered = waterOrMineralsInRegion("water", self.endLocation, ROOT_WATER_EXTRACTION_RADIUS)
				if availableWater > 0:
					for location in locationsConsidered:
						if water.has_key(location):
							waterAtLocation = water[location]
						else:
							waterAtLocation = 0
						if waterAtLocation > 0:
							waterExtractedFromLocation = ROOT_WATER_EXTRACTION_EFFICIENCY * waterAtLocation
							self.water += waterExtractedFromLocation
							water[location] -= waterExtractedFromLocation
				availableMinerals, locationsConsidered = waterOrMineralsInRegion("minerals", self.endLocation, ROOT_MINERAL_EXTRACTION_RADIUS)
				if availableMinerals > 0:
					for location in locationsConsidered:
						if minerals.has_key(location):
							mineralsAtLocation = minerals[location]
							if mineralsAtLocation > 0:
								mineralsExtractedFromLocation = ROOT_MINERAL_EXTRACTION_EFFICIENCY * mineralsAtLocation
								self.minerals += mineralsExtractedFromLocation
								minerals[location] -= mineralsExtractedFromLocation
	
	def nextDay_Consumption(self):
		if self.alive:
			if self.woody:
				biomassINeedToUseToday = 0
			else:
				biomassINeedToUseToday = BIOMASS_USED_BY_INTERNODE_PER_DAY[self.root]
			if self.biomass - biomassINeedToUseToday < INTERNODE_DIES_IF_BIOMASS_GOES_BELOW[self.root]:
				self.die()
				#print 'internode died', self.biomass, self.water, self.minerals, self.root
			else:
				self.biomass -= biomassINeedToUseToday
	
	def die(self):
		sendDieSignalTo = []
		if not self.root:
			sendDieSignalTo.extend(self.leafClusters)
		sendDieSignalTo.extend([self.apicalMeristem])
		sendDieSignalTo.extend(self.axillaryMeristems)
		sendDieSignalTo.extend([self.child])
		sendDieSignalTo.extend(self.branches)
		for sendTo in sendDieSignalTo:
			if sendTo:
				sendTo.die()
	
	def nextDay_Distribution(self):
		if self.tree.prevailingStressCondition == "no stress":
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["no stress"][self.root]
			spread = BIOMASS_DISTRIBUTION_SPREAD["no stress"][self.root]
		elif self.tree.prevailingStressCondition in ["low sun", "shade"]:
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["low sun or shade"][self.root]
			spread = BIOMASS_DISTRIBUTION_SPREAD["low sun or shade"][self.root]
		elif self.tree.prevailingStressCondition in ["water", "minerals"]:
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["water or mineral stress"][self.root]
			spread = BIOMASS_DISTRIBUTION_SPREAD["water or mineral stress"][self.root]
		elif self.tree.prevailingStressCondition == "reproduction":
			biomassDistributionOrder = BIOMASS_DISTRIBUTION_ORDER["reproduction"][self.root]
			spread = BIOMASS_DISTRIBUTION_SPREAD["reproduction"][self.root]
		parts = self.gatherDistributees(biomassDistributionOrder)
		for part in parts:
			if part:
				extra = max(0, self.biomass - OPTIMAL_INTERNODE_BIOMASS[self.root] - BIOMASS_USED_BY_INTERNODE_PER_DAY[self.root])
				if extra > 0:
					toBeGivenAway = extra * spread
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
				
	def nextDay_Growth(self):
		self.woody = self.age > INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS
		if self.alive:
			proportion = self.biomass / OPTIMAL_INTERNODE_BIOMASS[self.root]
			if self.firstOnTree:
				self.length = int(round(proportion * FIRST_INTERNODE_LENGTH_AT_FULL_SIZE[self.root]))
				self.length = max(FIRST_INTERNODE_LENGTH_AT_CREATION[self.root], min(FIRST_INTERNODE_LENGTH_AT_FULL_SIZE[self.root], self.length))
			else:
				self.length = int(round(proportion * INTERNODE_LENGTH_AT_FULL_SIZE[self.root]))
				self.length = max(INTERNODE_LENGTH_AT_CREATION[self.root], min(INTERNODE_LENGTH_AT_FULL_SIZE[self.root], self.length))
			self.width = int(round(proportion * INTERNODE_WIDTH_AT_FULL_SIZE[self.root]))
			self.width = max(INTERNODE_WIDTH_AT_CREATION[self.root], min(INTERNODE_WIDTH_AT_FULL_SIZE[self.root], self.width))
		
	def nextDay_Drawing(self):
		aboveGround = not self.root
		if not self.iAmABranchOffMyParent:
			if self.parent:
				self.matrix.location = self.parent.locationForChildInternode()
		directionOfParentBranch = self.findDirectionOfParentBranch()
		if self.branchNestingLevel <= 1:
			angleInDegrees = ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK[self.root]
		else:
			angleInDegrees = ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK[self.root]
			
		# location, length, angleInDegrees, swayInDegrees, forward, parentForward, side, aboveGround=True
		self.endLocation = endPointOfAngledLine(self.matrix.location, self.length, 
					angleInDegrees, self.randomSway, self.forward, directionOfParentBranch, aboveGround)
		#if aboveGround and self.branchNestingLevel >= 2:
		#	print self.branchNestingLevel, self.matrix.location, self.endLocation, self.length, angleInDegrees, self.randomSway, self.forward, self.parentBranchForward, aboveGround
		if not self.woody and INTERNODES_SEEK_SUN_OR_WATER_AND_MINERALS_IN_RADIUS[self.root] > 0:
			self.endLocation = seekBetterLocation(self.endLocation, self.root, INTERNODES_SEEK_SUN_OR_WATER_AND_MINERALS_IN_RADIUS[self.root])
		if (self.root and DRAW_ROOTS) or (not self.root and DRAW_STEMS):
			locationsBetween = locationsBetweenTwoPoints(self.matrix.location, self.endLocation, self.length)
			self.claimStartBlock()
			self.claimSeriesOfBlocks(locationsBetween)
			if self.width > 1:
				for location in locationsBetween:
					circleLocations = circleAroundPoint(location, self.width, self.forward, self.side, aboveGround)
					self.claimSeriesOfBlocks(circleLocations)
					
	def findDirectionOfParentBranch(self):
		internode = self.parent
		if not internode:
			if self.root:
				return "down"
			else:
				return "up"
		while internode:
			if internode.firstOnBranch:
				if internode.parent:
					return internode.parent.forward
				else:
					if self.root:
						return "down"
					else:
						return "up"
			else:
				internode = internode.parent
			
	def nextDay_SignalPropagation(self):
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
				sendTo.nextDay()
		
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
					
	def sumUpStresses(self):
		totalCount = 0
		totalLowSunStress = 0
		totalShadeStress = 0
		totalLowWaterStress = 0
		totalLowMineralStress = 0
		sendSignalTo = []
		if not self.root:
			sendSignalTo.extend(self.leafClusters)
		sendSignalTo.extend([self.child])
		sendSignalTo.extend(self.branches)
		for sendTo in sendSignalTo:
			if sendTo:
				count, lowSunStress, shadeStress, lowWaterStress, lowMineralStress = sendTo.sumUpStresses()
				totalCount += count
				totalLowSunStress += lowSunStress
				totalShadeStress += shadeStress
				totalLowWaterStress += lowWaterStress
				totalLowMineralStress += lowMineralStress
		return totalCount, totalLowSunStress, totalShadeStress, totalLowWaterStress, totalLowMineralStress
		
	def describe(self, outputFile, indentCounter=0):
		TreePart.describe(self, outputFile, indentCounter)
		if not self.root:
			for leafCluster in self.leafClusters:
				leafCluster.describe(outputFile, indentCounter+1)
		if not self.root:
			for flowerCluster in self.flowerClusters:
				flowerCluster.describe(outputFile, indentCounter+1)
		if not self.root:
			for fruitCluster in self.fruitClusters:
				fruitCluster.describe(outputFile, indentCounter+1)
		if self.apicalMeristem:
			self.apicalMeristem.describe(outputFile, indentCounter+1)
		for meristem in self.axillaryMeristems:
			if meristem:
				meristem.describe(outputFile, indentCounter+1)
		if self.child:
			self.child.describe(outputFile, indentCounter+1)
			
# -------------------------------------------------------------------------------------------
class LeafCluster(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, numberOnInternode, location, forward, side):
		TreePart.__init__(self, tree, parent, location, forward, side, biomass=START_LEAF_CLUSTER_BIOMASS, water=0, minerals=0)
		self.numberOnInternode = numberOnInternode
		self.length = LEAF_CLUSTER_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_LEAF_CLUSTER_SWAY) - RANDOM_LEAF_CLUSTER_SWAY // 2
		self.newBiomass = 0
		self.lowSunStress = 0
		self.shadeStress = 0
		self.lowWaterStress = 0
		self.lowMineralStress = 0
				
	def nextDay_Uptake(self):
		if self.alive:
			self.lowSunStress = 1.0 - sun[(self.matrix.location[0], self.matrix.location[1])]
			numBlocksShadingMe = blocksOccupiedAboveLocation(self.matrix.location, self)
			self.shadeStress = max(0.0, min(1.0, 1.0 * numBlocksShadingMe / NUM_BLOCKS_ABOVE_FOR_MAX_SHADE_STRESS))
			self.lowWaterStress = 1.0 - self.water / WATER_FOR_OPTIMAL_PHOTOSYNTHESIS
			self.lowMineralStress = 1.0 - self.minerals / MINERALS_FOR_OPTIMAL_PHOTOSYNTHESIS
			lowBiomassStress = 1.0 - self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS
			
			lowSunStressFactor = self.lowSunStress * 0.2 * (1.0 - LOW_SUN_TOLERANCE)
			shadeStressFactor = self.shadeStress * 0.2 * (1.0 - SHADE_TOLERANCE)
			lowWaterStressFactor = self.lowWaterStress * 0.2 * (1.0 - WATER_STRESS_TOLERANCE)
			lowMineralStressFactor = self.lowMineralStress * 0.2 * (1.0 - MINERAL_STRESS_TOLERANCE)
			lowBiomassStressFactor = lowBiomassStress * 0.2 # no tolerance for this; small leaves make less food!
			
			combinedEffects = 1.0 - (lowSunStressFactor + shadeStressFactor + lowWaterStressFactor + lowMineralStressFactor + lowBiomassStressFactor)
			combinedEffects = max(0.0, min(1.0, combinedEffects))
			
			sCurve = 1.0 - math.exp(-0.65 * combinedEffects)
			self.newBiomass =  sCurve * OPTIMAL_LEAF_PHOTOSYNTHATE
			#print sunProportion, numBlocksShadingMe, shadeProportion, waterProportion, mineralsProportion, biomassProportion
			#print '.....', combinedEffectsProportion, sCurve, self.newBiomass
			#self.newBiomass =  max(0.0, combinedEffectsProportion * (1.0 - math.exp(-0.65 * OPTIMAL_LEAF_PHOTOSYNTHATE)))
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
		location, direction, side = self.parent.locationAndDirectionsForLeafCluster(self.numberOnInternode)
		self.matrix.location = location
		if self.alive:
			proportion = self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS
			self.length = int(round(proportion * LEAF_CLUSTER_LENGTH_AT_FULL_SIZE))
			self.length = max(LEAF_CLUSTER_LENGTH_AT_CREATION, min(LEAF_CLUSTER_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_Drawing(self):
		if DRAW_LEAF_CLUSTERS:
			if self.length > 1:
				spineEndLocation = endPointOfAngledLine(self.matrix.location, self.length, 
							LEAF_CLUSTER_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward)
				spine = locationsBetweenTwoPoints(self.matrix.location, spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / LEAF_CLUSTER_LENGTH_AT_FULL_SIZE
				# spine, pattern, angle, sides, sizeProportion, forward, side
				wings = locationsForShapeAroundSpine(spine, LEAF_CLUSTER_SHAPE_PATTERN, LEAF_CLUSTER_SHAPE_ANGLE, LEAF_CLUSTER_SIDES, 
							sizeProportion, self.forward, self.side)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	def nextDay_SignalPropagation(self):
		pass

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
		return 1, self.lowSunStress, self.shadeStress, self.lowWaterStress, self.lowMineralStress
				
# -------------------------------------------------------------------------------------------
class FlowerCluster(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, numberOnInternode, apical, location, forward, side):
		TreePart.__init__(self, tree, parent, location, forward, side, biomass=START_FLOWER_CLUSTER_BIOMASS, water=0, minerals=0)
		self.numberOnInternode = numberOnInternode
		self.apical = apical
		self.length = FLOWER_CLUSTER_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_FLOWER_CLUSTER_SWAY) - RANDOM_FLOWER_CLUSTER_SWAY // 2
		
	def buildFruit(self):
		newFruitCluster = FruitCluster(self.tree, self.parent, self.numberOnInternode, self.matrix.location, self.forward, self.side)
		self.parent.removeFlowerClusterThatMadeFruitCluster(self)
		self.parent.addFruitCluster(newFruitCluster)
				
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY < FLOWER_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW:
			self.die()
			#print 'leaf died', self.biomass, self.water, self.minerals
		else:
			self.biomass -= BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY

	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		if self.age >= MINIMUM_DAYS_FLOWER_APPEARS_EVEN_WITH_OPTIMAL_BIOMASS and self.biomass >= OPTIMAL_FLOWER_CLUSTER_BIOMASS:
			self.buildFruit()
		else:
			location, direction, side = self.parent.locationAndDirectionsForAxillaryMeristem(self.numberOnInternode)
			self.matrix.location = location
			proportion = self.biomass / OPTIMAL_FLOWER_CLUSTER_BIOMASS
			self.length = int(round(proportion * FLOWER_CLUSTER_LENGTH_AT_FULL_SIZE))
			self.length = max(FLOWER_CLUSTER_LENGTH_AT_CREATION, min(FLOWER_CLUSTER_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_Drawing(self):
		if DRAW_FLOWER_CLUSTERS:
			if self.length > 1:
				spineEndLocation = endPointOfAngledLine(self.matrix.location, self.length, 
							FLOWER_CLUSTER_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward)
				spine = locationsBetweenTwoPoints(self.matrix.location, spineEndLocation, self.length)
				sizeProportion = self.biomass / OPTIMAL_FLOWER_CLUSTER_BIOMASS
				# # spine, pattern, angle, sides, sizeProportion, forward, side
				wings = locationsForShapeAroundSpine(spine, FLOWER_CLUSTER_SHAPE_PATTERN, FLOWER_CLUSTER_SHAPE_ANGLE, FLOWER_CLUSTER_SIDES, 
							sizeProportion, self.forward, self.side)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	def nextDay_SignalPropagation(self):
		pass

	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_FLOWER_CLUSTER_BIOMASS + BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
# -------------------------------------------------------------------------------------------
class FruitCluster(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, numberOnInternode, location, forward, side):
		TreePart.__init__(self, tree, parent, location, forward, side, biomass=START_FRUIT_CLUSTER_BIOMASS, water=0, minerals=0)
		self.numberOnInternode = numberOnInternode
		self.length = FRUIT_CLUSTER_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_FRUIT_CLUSTER_SWAY) - RANDOM_FRUIT_CLUSTER_SWAY // 2
		
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY < FRUIT_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW:
			self.die()
		else:
			self.biomass -= BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY

	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		location, direction, side = self.parent.locationAndDirectionsForAxillaryMeristem(self.numberOnInternode)
		self.matrix.location = location
		proportion = self.biomass / OPTIMAL_FRUIT_CLUSTER_BIOMASS
		self.length = int(round(proportion * FRUIT_CLUSTER_LENGTH_AT_FULL_SIZE))
		self.length = max(FRUIT_CLUSTER_LENGTH_AT_CREATION, min(FRUIT_CLUSTER_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_Drawing(self):
		if DRAW_FRUIT_CLUSTERS:
			if self.length > 1:
				spineEndLocation = endPointOfAngledLine(self.matrix.location, self.length, 
							FRUIT_CLUSTER_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward)
				spine = locationsBetweenTwoPoints(self.matrix.location, spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / FRUIT_CLUSTER_LENGTH_AT_FULL_SIZE
				# # spine, pattern, angle, sides, sizeProportion, forward, side
				wings = locationsForShapeAroundSpine(spine, FRUIT_CLUSTER_SHAPE_PATTERN, FRUIT_CLUSTER_SHAPE_ANGLE, FRUIT_CLUSTER_SIDES, 
							sizeProportion, self.forward, self.side)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	def nextDay_SignalPropagation(self):
		pass

	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_FRUIT_CLUSTER_BIOMASS + BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
				
# -------------------------------------------------------------------------------------------
class Tree():
# -------------------------------------------------------------------------------------------
	def __init__(self, x, y, z):
		self.age = 0
		self.matrix = Matrix3D(0.0, 0.0, 0.0)
		self.matrix.initializeAsUnitMatrix()
		#self.matrix.setXYZ(x, y, z)
		self.matrix.rotateY(90)
		self.matrix.move(1.0)
		print self.matrix.location
		
		self.numInternodesCreated = 0
		self.numRootInternodesCreated = 0
		self.reproductivePhaseHasStarted = False
		self.prevailingStressCondition = "no stress"
		
		self.seed = random.random()
		random.seed(self.seed)
		
		rootMatrix = self.matrix.makeCopy()
		rootMatrix.rotateY(180)
		print rootMatrix.location
		rootMatrix.move(1.0)
		print rootMatrix.location

		#self.firstInternodeSideDirection = DIRECTIONS[random.randrange(4)] # only choose from NESW, not up or down - first 4 in list
		#self.firstRootInternodeSideDirection = DIRECTIONS[random.randrange(4)]
		
		firstMeristem = Meristem(self, None, False, 0, 0, self.matrix, apical=True)
		self.firstInternode = firstMeristem.buildInternode(firstOnTree=True)
		
		
		firstRootMeristem = Meristem(self, None, True, 0, 0, rootMatrix, apical=True)
		self.firstRootInternode = firstRootMeristem.buildInternode(firstOnTree=True)
		
	def nextDay(self):
		if self.age == REPRODUCTIVE_MODE_STARTS_ON_DAY:
			self.reproductivePhaseHasStarted = True
			self.firstInternode.reproduce()
		self.firstInternode.nextDay()
		self.firstRootInternode.nextDay()
		self.calculateStresses()
		self.age += 1
		
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
		
	def calculateStresses(self):
		self.leafClusterCount, self.totalLowSunStress, self.totalShadeStress, self.totalLowWaterStress, \
			self.totalLowMineralStress = self.firstInternode.sumUpStresses()
		highestStress = max(self.totalLowSunStress, self.totalShadeStress, self.totalLowWaterStress, self.totalLowMineralStress)
		if highestStress / self.leafClusterCount < MIN_STRESS_TO_TRIGGER_BIOMASS_REDISTRIBUTION:
			if self.reproductivePhaseHasStarted:
				self.prevailingStressCondition = "reproduction"
			else:
				self.prevailingStressCondition = "no stress"
		elif highestStress == self.totalLowSunStress:
			self.prevailingStressCondition = "low sun"
		elif highestStress == self.totalShadeStress:
			self.prevailingStressCondition = "shade"
		elif highestStress == self.totalLowWaterStress:
			self.prevailingStressCondition = "water"
		elif highestStress == self.totalLowMineralStress:
			self.prevailingStressCondition = "minerals"
		
# -------------------------------------------------------------------------------------------
def growTree(outputFolder):
# -------------------------------------------------------------------------------------------
	
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
		daysPerPulse = 3
		numPulses = 10
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
				if describeTrees:
					outputFile.write("Day %s\n\n" % day)
				for tree in trees:
					tree.nextDay()
					if describeTrees:
						tree.describe(outputFile)
			drawSpace(day, outputFolder, drawTrees=True)#, drawSun=True, drawWater=True, drawMinerals=True, drawSurface=True)
			day += daysPerPulse
	
	finally:
		if describeTrees:
			outputFile.close()

	print 'done'
	
def main():
	iterations = 1
	for i in range(iterations):
		outputFolder = setUpOutputFolder("/Users/cfkurtz/Documents/personal/terasology/generated images/")
		print 'writing files to:', outputFolder
		growTree(outputFolder)
	
if __name__ == "__main__":
	main()
	
