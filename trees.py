# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

import os, sys, random, math
import numpy as np

from trees_graphics import *
from trees_world import *

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
# DONE??? put random number on seed unique to plant
# FIXED problem: gaps
# DONE add internode width
# DONE add leafCluster petiole and leafCluster shape
# DONE add leafCluster angle with stem

# add limits on parameters (in comments)
# add seeking behavior for internodes (stem and root)

# put in flower and fruit clusters
# put in root growth
# do water and nutrient uptake - water and nutrient grids, like sun grid

# NOT DOING think about collision avoidance and growth around occupied blocks

# -------------------------------------------------------------------------------------------
class PlantPart():
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, location, forward, side, biomass=0, water=0, minerals=0):
		self.plant = plant
		self.parent = parent
		self.age = 0
		self.alive = True
		
		self.biomass = biomass
		self.water = water
		self.minerals = minerals
		
		self.forward = forward
		self.side = side
		self.location = location
		self.blocks = []
		
	def nextDay(self):
		self.releaseAllUsedBlocks()
		if self.alive:
			self.nextDay_Uptake()
			self.nextDay_Consumption()
			if self.alive:
				self.nextDay_Distribution()
				self.nextDay_Growth()
				self.nextDay_SignalPropagation()
		self.age += 1
		
	def die(self):
		self.alive = False
	
	def releaseAllUsedBlocks(self):
		for location in self.blocks:
			releaseLocation(location, self)
		self.blocks = []
		
	def claimStartBlock(self):
		self.blocks = [self.location]
		claimLocation(self.location, self)
		
	def claimSeriesOfBlocks(self, locations):
		for location in locations:
			if not location in self.blocks:
				self.blocks.append(location)
				claimLocation(location, self)
		
	def calculatePhotosynthesis(self, location, optimalAmount):
		# used by leafCluster and internode so to avoid duplication, keep here
		# 1. the more sun where you are, the more you can get at
		sunProportion = sun[(location[0], location[1])]
		# 2. the more things above you the less light you get
		numBlocksShadingMe = blocksOccupiedAboveLocation(location, self)
		if numBlocksShadingMe > 0:
			shadeProportion = max(0.0, min(1.0, 1.0 - 1.0 * numBlocksShadingMe / SHADE_TOLERANCE))
		else:
			shadeProportion = 1.0
		# 3. these effects multiply
		combinedEffectsProportion = sunProportion * shadeProportion
		# 5. photosynthesis depends on biomass accumulated (water and nutrients later)
		#print 'sunProportion', sunProportion, 'numBlocksShadingMe', numBlocksShadingMe, 'shadeProportion', shadeProportion, 'biomass', self.biomass 
		photosynthesisProportion = combinedEffectsProportion * (1.0 - math.exp(-0.65 * self.biomass))
		# 5. finally we end up with a proporton of the optimal
		newBiomass = max(0.0, photosynthesisProportion * optimalAmount) 
		return newBiomass
		
# -------------------------------------------------------------------------------------------
class Meristem(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, root, numberOnInternode, location, forward, side, apical=False, biomass=0, water=0, minerals=0):
		PlantPart.__init__(self, plant, parent, location, forward, side, biomass=START_MERISTEM_BIOMASS[root], water=0, minerals=0)
		self.apical = apical
		self.root = root
		self.numberOnInternode = numberOnInternode
		self.active = False
		
	def buildInternode(self, firstOnPlant=False):
		if self.apical:
			newSide = rotateAround(self.forward, self.side, 1)
			if self.parent:
				parentBranchForward = self.parent.parentBranchForward
			else:
				if self.root:
					parentBranchForward = "down"
				else:
					parentBranchForward = "up"
		else:   
			if self.parent:
				newSide = self.side
				parentBranchForward = self.parent.forward
			else:
				if self.root:
					parentBranchForward = "down"
					newSide = self.plant.firstRootInternodeSideDirection
				else:
					parentBranchForward = "up"
					newSide = self.plant.firstInternodeSideDirection
		firstOnBranch = firstOnPlant or not self.apical
		
		newInternode = Internode(self.plant, self.parent, self.root, self.location, self.forward, newSide, 
								firstOnPlant=firstOnPlant, firstOnBranch=firstOnBranch, parentBranchForward=parentBranchForward,
								iAmABranchOffMyParent=not self.apical)
		if self.parent:
			if self.apical:
				self.parent.addChildInternode(newInternode)
			else:
				self.parent.addBranchInternode(newInternode)
		return newInternode
		
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
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
		if self.active:
			if self.biomass >= BIOMASS_TO_MAKE_ONE_PHYTOMER[self.root]:
				self.buildInternode()
				self.parent.removeMeristemThatMadeInternode(self)
		if self.apical:
			location = self.parent.locationForApicalMeristem()
		else:
			location, forward, side = self.parent.locationAndDirectionsForAxillaryMeristem(self.numberOnInternode)
		self.location = location
		self.claimStartBlock()
		
	def calculateActivityLevel(self):
		if not self.active:
			if self.plant.numInternodesCreated <= MAX_NUM_INTERNODES_ON_PLANT_EVER[self.root]:
				distance = self.distanceOfParentFromBranchApex()
				if distance > 0:
					probability = BRANCHING_PROBABILITY[self.root] * distance / APICAL_DOMINANCE_EXTENDS_FOR[self.root]
					probability = max(0.0, min(1.0, probability))
					randomNumber = random.random() 
					self.active = randomNumber < probability
					#print 'axillary meristem distance', distance, 'prob', probability, 'number', randomNumber, 'active', self.active
		
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
		biomassINeed = max(0, (BIOMASS_TO_MAKE_ONE_PHYTOMER[self.root] + BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root]) - self.biomass)
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		#print 'biomassINeed', biomassINeed, 'biomassIWillAccept', biomassIWillAccept, 'biomass', self.biomass
		#print 'meristem took %s biomass from internode' % biomassIWillAccept
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
	
	def display(self, indentCounter=0):
		if self.root:
			rootOrNot = 'root'
		else:
			rootOrNot = ''
		if self.apical:
			print INDENT * indentCounter, rootOrNot, 'apical meristem: biomass', self.biomass, "location", self.location, "active", self.active, "forward", self.forward, "side", self.side
		else:
			print INDENT * indentCounter, rootOrNot, 'axillary meristem: biomass', self.biomass, "location", self.location, "active", self.active,"forward", self.forward, "side", self.side
		
# -------------------------------------------------------------------------------------------
class Internode(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, root, location, forward, side, firstOnPlant, firstOnBranch, parentBranchForward, iAmABranchOffMyParent):
		PlantPart.__init__(self, plant, parent, location, forward, side, biomass=START_INTERNODE_BIOMASS[root], water=0, minerals=0)
		self.root = root
		self.child = None
		self.branches = []
		self.firstOnPlant = firstOnPlant
		self.firstOnBranch = firstOnBranch
		self.parentBranchForward = parentBranchForward
		self.iAmABranchOffMyParent = iAmABranchOffMyParent
		self.plant.numInternodesCreated += 1
		self.randomSway = random.randrange(RANDOM_INTERNODE_SWAY[self.root]) - RANDOM_INTERNODE_SWAY[self.root] // 2
		
		if not self.root:
			self.woody = (INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS == 0)
		else:
			self.woody = False
		self.length = INTERNODE_LENGTH_AT_CREATION[self.root]
		self.width = INTERNODE_WIDTH_AT_CREATION[self.root]
		self.recalculateBlockPlacementsForChangeInLength()
		
		if not self.root:
			self.buildLeafClusters()
		self.buildMeristems()
		
	def buildMeristems(self):
		location = self.locationForApicalMeristem()
		self.apicalMeristem = Meristem(self.plant, self, self.root, 0, location, self.forward, self.side, apical=True)
		self.axillaryMeristems = []
		for i in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			location, forward, side = self.locationAndDirectionsForAxillaryMeristem(i)
			newAxillaryMeristem = Meristem(self.plant, self, self.root, i, location, forward, side, apical=False)
			self.axillaryMeristems.append(newAxillaryMeristem)
		
	def buildLeafClusters(self):
		self.leafClusters = []
		for i in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			location, forward, side = self.locationAndDirectionsForLeafCluster(i)
			newLeafCluster = LeafCluster(self.plant, self, i, location, forward, side)
			self.leafClusters.append(newLeafCluster)
			
	def locationForApicalMeristem(self):
		locationOneFurther = displacementInDirection(self.endLocation, self.forward, 1)
		return locationOneFurther
	
	def locationAndDirectionsForAxillaryMeristem(self, meristemNumber):
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
		location = displacementInDirection(self.endLocation, meristemForward, self.width//2)
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
		locationOneFurther = displacementInDirection(self.endLocation, self.forward, 1)
		return locationOneFurther
		
	def addChildInternode(self, internode):
		self.child = internode
		
	def addBranchInternode(self, internode):
		self.branches.append(internode)
				
	def acceptBiomass(self, biomassOffered):
		# the internode, because it is a piping system, takes biomass it doesn't need
		# so it can pass it on
		#print self.age, 'biomass before accepting', self.biomass
		self.biomass += biomassOffered
		#print self.age, 'biomass after accepting', self.biomass
		return biomassOffered
	
	def removeMeristemThatMadeInternode(self, meristem):
		if meristem.apical:
			self.apicalMeristem = None
		else:
			self.axillaryMeristems.remove(meristem)
		
	def nextDay_Uptake(self):
		#print self.age, 'biomass before uptake', self.biomass
		if (not self.root) and (not self.woody):
			newBiomass = self.calculatePhotosynthesis(self.endLocation, BIOMASS_MADE_BY_FULL_SIZED_NON_WOODY_INTERNODE_PER_DAY_WITH_FULL_SUN)
			self.biomass += newBiomass
		if self.root:
			pass
			# figure out how much water and minerals you need first
			# need params for optimal and start water and minerals for all plant parts ??? i guess so
			#newWater = ROOT_TAKES_PROPORTION_OF_WATER_IN_SPOT * water[self.endLocation]
			#water[self.endLocation] -= newWater
			#self.water += newWater
			#newMinerals = ROOT_TAKES_PROPORTION_OF_MINERALS_IN_SPOT * minerals[self.endLocation]
			#minerals[self.endLocation] -= newMinerals
#		#print self.age, 'biomass after uptake', self.biomass
	
	def nextDay_Consumption(self):
		#print self.age, 'biomass before consumption', self.biomass
		if self.woody: #internodes don't use any biomass up once they have stopped photosynthesizing
			biomassINeedToUseToday = 0
		else:
			biomassINeedToUseToday = BIOMASS_USED_BY_INTERNODE_PER_DAY[self.root]
		if self.biomass - biomassINeedToUseToday < INTERNODE_DIES_IF_BIOMASS_GOES_BELOW[self.root]:
			self.die()
		else:
			self.biomass -= biomassINeedToUseToday
		#print self.age, 'biomass after consumption', self.biomass
	
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
		#print self.age, 'biomass before distribution', self.biomass
		supplicants = []
		for name in BIOMASS_DISTRIBUTION_ORDER[self.root]:
			if name == "leafClusters":
				if not self.root:
					supplicants.extend(self.leafClusters)
			elif name == "apical meristems":
				supplicants.extend([self.apicalMeristem])
			elif name == "axillary meristems":
				supplicants.extend(self.axillaryMeristems)
			elif name == "child":
				supplicants.extend([self.child])
			elif name == "branches":
				supplicants.extend(self.branches)
			elif name == "parent":
				supplicants.extend([self.parent])
			elif name == "root":
				if (not self.root) and self.firstOnPlant:
					supplicants.extend([self.plant.firstRootInternode])
			elif name == "above-ground plant":
				if self.root and self.firstOnPlant:
					supplicants.extend([self.plant.firstInternode])
		extraBiomass = max(0, self.biomass - OPTIMAL_INTERNODE_BIOMASS[self.root])
		toBeGivenAway = extraBiomass * BIOMASS_DISTRIBUTION_SPREAD_PERCENT[self.root] / 100.0
		for supplicant in supplicants:
			if supplicant and extraBiomass > 0:
				biomassTakenBySupplicant = supplicant.acceptBiomass(toBeGivenAway)
				#print '      biomass', self.biomass, 'extraBiomass', extraBiomass, 'toBeGivenAway', toBeGivenAway, 'taken', biomassTakenBySupplicant
				self.biomass -= biomassTakenBySupplicant
				extraBiomass = max(0, self.biomass - OPTIMAL_INTERNODE_BIOMASS[self.root])
				toBeGivenAway = extraBiomass * BIOMASS_DISTRIBUTION_SPREAD_PERCENT[self.root] / 100.0
		#print self.age, 'biomass after distribution', self.biomass
	
	def nextDay_Growth(self):
		if not self.root:
			self.woody = self.age > INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS
		else:
			self.woody = False
		proportion = self.biomass / OPTIMAL_INTERNODE_BIOMASS[self.root]
		self.length = max(1, min(INTERNODE_LENGTH_AT_FULL_SIZE[self.root], int(round(proportion * INTERNODE_LENGTH_AT_FULL_SIZE[self.root]))))
		self.width = max(1, min(INTERNODE_WIDTH_AT_FULL_SIZE[self.root], int(round(proportion * INTERNODE_WIDTH_AT_FULL_SIZE[self.root]))))
		self.recalculateBlockPlacementsForChangeInLength()
		
	def nextDay_SignalPropagation(self):
		sendNextDayTo = []
		if not self.root:
			sendNextDayTo.extend(self.leafClusters)
		sendNextDayTo.extend([self.apicalMeristem])
		sendNextDayTo.extend(self.axillaryMeristems)
		sendNextDayTo.extend([self.child])
		sendNextDayTo.extend(self.branches)
		for sendTo in sendNextDayTo:
			if sendTo:
				sendTo.nextDay()
		
	def recalculateBlockPlacementsForChangeInLength(self):
		aboveGround = not self.root
		if not self.iAmABranchOffMyParent:
			if self.parent:
				self.location = self.parent.locationForChildInternode()
		# testing the parent branch forward is a kludgy way of trying to find out if you have branched
		# off the main trunk without saving the information
		# NOT USING - CFK FIX
		angleInDegrees = ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK[self.root]
		self.endLocation = endPointOfAngledLine(self.location, self.length, 
					angleInDegrees, self.randomSway, self.forward, self.parentBranchForward, self.side, aboveGround)
		#print 'seeking from', self.endLocation
		self.endLocation = seekBetterLocation(self.endLocation, self.root, INTERNODES_SEEK_RADIUS[self.root])
		#print '..... found', self.endLocation
		# now interpolate between the start and end positions to produce a rough line
		locationsBetween = locationsBetweenTwoPoints(self.location, self.endLocation, self.length)
		# place yourself in the locations
		self.claimStartBlock()
		self.claimSeriesOfBlocks(locationsBetween)
		if self.width > 1:
			for location in locationsBetween:
				circleLocations = circleAroundPoint(location, self.width, self.forward, self.side, aboveGround)
				self.claimSeriesOfBlocks(circleLocations)
			
	def display(self, indentCounter=0):
		if self.root:
			rootOrNot = "root"
		else:
			rootOrNot = ""
		print INDENT * indentCounter, rootOrNot, 'internode: biomass', self.biomass, "location", self.location, "forward", self.forward, "side", self.side
		if not self.root:
			for leafCluster in self.leafClusters:
				leafCluster.display(indentCounter+1)
		if self.apicalMeristem:
			self.apicalMeristem.display(indentCounter+1)
		for meristem in self.axillaryMeristems:
			meristem.display(indentCounter+1)
		if self.child:
			self.child.display(indentCounter+1)
			
# -------------------------------------------------------------------------------------------
class LeafCluster(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, numberOnInternode, location, forward, side):
		PlantPart.__init__(self, plant, parent, location, forward, side, biomass=START_LEAF_CLUSTER_BIOMASS, water=0, minerals=0)
		self.numberOnInternode = numberOnInternode
		self.length = LEAF_CLUSTER_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_LEAF_CLUSTER_SWAY) - RANDOM_LEAF_CLUSTER_SWAY // 2
				
	def nextDay_Uptake(self):
		newBiomass = self.calculatePhotosynthesis(self.location, BIOMASS_MADE_BY_FULL_SIZED_LEAF_CLUSTER_PER_DAY_OF_PHOTOSYNTHESIS_WITH_FULL_SUN)
		self.biomass += newBiomass
	
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY < DEATH_BIOMASS_LEAF_CLUSTER:
			self.die()
		else:
			self.biomass -= BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY
	
	def nextDay_Distribution(self):
		extraBiomass = max(0, self.biomass - OPTIMAL_LEAF_CLUSTER_BIOMASS)
		biomassTakenByParent = self.parent.acceptBiomass(extraBiomass)
		self.biomass -= biomassTakenByParent
	
	def nextDay_Growth(self):
		location, direction, side = self.parent.locationAndDirectionsForLeafCluster(self.numberOnInternode)
		self.location = location
		proportion = self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS
		self.length = max(1, min(LEAF_CLUSTER_LENGTH_AT_FULL_SIZE, int(round(proportion * LEAF_CLUSTER_LENGTH_AT_FULL_SIZE))))
		self.recalculateBlockPlacementsForChangeInSize()
		
	def recalculateBlockPlacementsForChangeInSize(self):
		self.claimStartBlock()
		if self.length > 1:
			# draw "spine" of leaf cluster first
			endLocationForSpine = endPointOfAngledLine(self.location, self.length, 
						LEAF_CLUSTER_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward, self.side)
			leafClusterSpine = locationsBetweenTwoPoints(self.location, endLocationForSpine, self.length)
			self.claimSeriesOfBlocks(leafClusterSpine)
			# now draw two symmetrical "wings" to the sides
			leafClusterLengthIndex = 0
			leafClusterSides = []
			for location in leafClusterSpine:
				shapeLookupIndex = leafClusterLengthIndex % len(LEAF_CLUSTER_SHAPE_PATTERN)
				sideExtent = int(LEAF_CLUSTER_SHAPE_PATTERN[shapeLookupIndex])
				proportion = self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS
				sideExtentConsideringBiomass = max(0, min(sideExtent, int(round(proportion * sideExtent))))
				if sideExtentConsideringBiomass > 0:
					for sideMultiplier in [1, -1]:
						if sideMultiplier == -1:
							sideDirection = self.side
						else:
							sideDirection = rotateAround(self.forward, self.side, 2)
						# location, length, angleInDegrees, swayInDegrees, forward, parentForward, side
						endLocationForLeafClusterSide = endPointOfAngledLine(location, sideExtentConsideringBiomass, 
									LEAF_CLUSTER_SHAPE_ANGLE, self.randomSway, sideDirection, self.forward, self.forward)
						oneSidePiece = locationsBetweenTwoPoints(location, endLocationForLeafClusterSide, sideExtentConsideringBiomass)
						leafClusterSides.extend(oneSidePiece)
				leafClusterLengthIndex += 1
			self.claimSeriesOfBlocks(leafClusterSides)
		else:
			endLocationForLeafCluster = displacementInDirection(self.location, self.forward, 1)
			claimLocation(endLocationForLeafCluster, self)

	def nextDay_SignalPropagation(self):
		pass

	def acceptBiomass(self, biomassOffered):
		biomassINeed = max(0, (OPTIMAL_LEAF_CLUSTER_BIOMASS + BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY) - self.biomass)
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		#print 'leafCluster took %s biomass from internode' % biomassIWillAccept
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
	def display(self, indentCounter=0):
		print INDENT * indentCounter, 'leaf cluster: biomass', self.biomass, "location", self.location, "forward", self.forward, "side", self.side
		
		
# -------------------------------------------------------------------------------------------
class FlowerCluster(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent):
		PlantPart.__init__(self, plant)
		self.parent = parent 
	
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		pass
	
	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		pass
	
	def nextDay_SignalPropagation(self):
		pass

	def display(self, indentCounter=0):
		print INDENT * indentCounter, 'flower', self.biomass
		
# -------------------------------------------------------------------------------------------
class FruitCluster(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent):
		PlantPart.__init__(self, plant)
		self.parent = parent 
			
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		pass
	
	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		pass
	
	def nextDay_SignalPropagation(self):
		pass

	def display(self, indentCounter=0):
		print INDENT * indentCounter, 'fruit', self.biomass
# -------------------------------------------------------------------------------------------
class Plant():
# -------------------------------------------------------------------------------------------
	def __init__(self, x, y, z):
		self.age = 0
		self.location = (x, y, z)
		self.numInternodesCreated = 0
		self.numRootInternodesCreated = 0
		self.seed = random.random()
		random.seed(self.seed)
		self.firstInternodeSideDirection = DIRECTIONS[random.randrange(4)] # only choose from NESW, not up or down - first 4 in list
		self.firstRootInternodeSideDirection = DIRECTIONS[random.randrange(4)]
		
		firstMeristem = Meristem(self, None, False, 0, self.location, "up", self.firstInternodeSideDirection, apical=True)
		self.firstInternode = firstMeristem.buildInternode(firstOnPlant=True)
		
		firstRootMeristem = Meristem(self, None, True, 0, self.location, "down", self.firstRootInternodeSideDirection, apical=True)
		self.firstRootInternode = firstRootMeristem.buildInternode(firstOnPlant=True)
		
	def nextDay(self):
		self.firstInternode.nextDay()
		self.firstRootInternode.nextDay()
		self.age += 1
		
	def display(self):
		print 'plant'
		self.firstInternode.display()
		self.firstRootInternode.display()
		
def growPlant(outputFolder):
	
	drawGraphs = False
	if drawGraphs:
		print 'writing distribution graphs...'
		drawSunDistribution(outputFolder)
		drawWaterDistribution(outputFolder)
		drawMineralsDistribution(outputFolder)
	
	numPlants = 1
	print 'starting simulated growth with %s plant(s)...' % numPlants
	daysPerPulse = 2
	numPulses = 15
	plants = []
	for i in range(numPlants):
		if numPlants == 1:
			xLocation = 50
			yLocation = 50
		else:
			xLocation = 10 + random.randrange(80)
			yLocation = 10 + random.randrange(80)
		zLocation = GROUND_LEVEL+1
		newPlant = Plant(xLocation, yLocation, zLocation)
		plants.append(newPlant)
	#for plant in plants:
	#	plant.display()
	
	day = 1
	for i in range(numPulses):
		for j in range(daysPerPulse):
			for plant in plants:
				plant.nextDay()
				#plant.display()
		drawSpace(day, outputFolder, drawSun=False)
		day += daysPerPulse
	
	print 'done'
	
def main():
	iterations = 1
	for i in range(iterations):
		outputFolder = setUpOutputFolder("/Users/cfkurtz/Documents/personal/terasology/generated images/")
		print 'writing files to:', outputFolder
		growPlant(outputFolder)
	
if __name__ == "__main__":
	main()
	
