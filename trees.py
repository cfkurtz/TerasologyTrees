# -----------------------------------------------------------------------------------------------------------------
# NarraCat: Tools for Narrative Catalysis
# -----------------------------------------------------------------------------------------------------------------
# License: Affero GPL 1.0 http://www.affero.org/oagpl.html
# Google Code Project: http://code.google.com/p/narracat/
# Copyright 2011 Cynthia Kurtz
# -----------------------------------------------------------------------------------------------------------------
# This file:
#
# Merging data - always custom
# this stuff is not often used, but is useful as a starting point when you need to merge two data files into one
# -----------------------------------------------------------------------------------------------------------------

import os, csv, sys, random, codecs, math

import colorsys

import matplotlib
matplotlib.use('TkAgg') # do this before importing pylab

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import axes3d
from matplotlib.patches import Circle, Rectangle
from matplotlib.collections import PatchCollection

import numpy as np

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
# DONE add leaf petiole and leaf shape
# DONE add leaf angle with stem

# clean up internode and leaf drawing code to make it more clear
# in general make everything more clear

# read parameters from file
# add limits on parameters

# put in inflorescences, flowers and fruits - not inflors???
# put in root growth
# do water and nutrient uptake - water and nutrient grids, like sun grid

# NOT DOING think about collision avoidance and growth around occupied blocks

# -------------------------------------------------------------------------------------------
# graphing
# -------------------------------------------------------------------------------------------

def cleanTextForFileName(fileName):
	result = fileName.replace("" + os.sep, " ").replace(":", " ").replace(".", " ").replace("\n", " ")
	result = result.replace("  ", " ")
	return result

def graphPNG3DScatter(xValues, yValues, zValues, colors, sizeOfSpace, xAxisName, yAxisName, zAxisName, graphName, pngFileName, pngFilePath):
	
	npArrayX = np.array(xValues)
	npArrayY = np.array(yValues)
	npArrayZ = np.array(zValues)
	
	plt.clf()
	figure = plt.figure(figsize=(6,6.5))
	axes = axes3d.Axes3D(figure)
	
	# set limits
	lowest = 0 #sizeOfSpace // 4
	highest = sizeOfSpace # 3 * sizeOfSpace // 4
	# for some reason you need both xlim and xlim3d, for x and y (not for z)
	axes.set_xlim(lowest, highest)
	axes.set_xlim3d(lowest, highest)
	axes.set_ylim(lowest, highest)
	axes.set_ylim3d(lowest, highest)
	axes.set_zlim3d(lowest, highest)
	axes.view_init(20, 30)
	
	try:
		axes.scatter(npArrayX, npArrayY, npArrayZ, c=colors, marker='s', s=10)
		axes.grid(False)
		axes.set_xlabel(xAxisName, fontsize=8)
		axes.set_ylabel(yAxisName, fontsize=8)
		plt.suptitle(graphName)
		plt.savefig(pngFilePath + cleanTextForFileName(pngFileName) + ".png", dpi=200)
		plt.close(figure)
	except Exception, e:
		print "could not save %s: %s" % (graphName, e)
		
def setUpOutputFolder(folder):
	folderList = os.listdir(folder)
	highestFolderNumber = 0
	for folderName in folderList:
		try:
			thisFolderNumber = int(folderName)
			if thisFolderNumber > highestFolderNumber:
				highestFolderNumber = thisFolderNumber
		except:
			pass # skip non-numerical folders
	newFolderNumber = highestFolderNumber + 1	
	folder = "%s%s/" % (folder, newFolderNumber)
	os.mkdir(folder)
	return folder

# -------------------------------------------------------------------------------------------
# space (block) management functions
# -------------------------------------------------------------------------------------------

# generate space
space = {}
sizeOfSpace = 100
for i in range(sizeOfSpace):
	for j in range(sizeOfSpace):
		for k in range (sizeOfSpace):
			space[(i,j,k)] = []
			
# generate patchy sun map
FULL_SUN = False
sun = {}
highestSun = 0
for i in range(sizeOfSpace):
	for j in range(sizeOfSpace):
		# to temporarily set all sun at max use this line
		if FULL_SUN:
			sun[(i,j)] = 1.0
		else:
			sun[(i,j)] = abs(math.sin(1.0*i/10) + math.cos(1.0*j/10))
		if sun[(i,j)] > highestSun:
			highestSun = sun[(i,j)]
		
# normalize sun map
for i in range(sizeOfSpace):
	for j in range(sizeOfSpace):
		sun[(i,j)] = sun[(i,j)] / highestSun
		
def locationIsInUse(location):
	return len(space[location]) > 0

def blocksOccupiedAboveLocation(location, plantPart):
	x = location[0]
	y = location[1]
	z = location[2]
	result = 0
	zAbove = min(sizeOfSpace-1, z+1)
	while zAbove <= sizeOfSpace-1:
		locationAbove = (x, y, zAbove)
		if space[locationAbove] and not (space[locationAbove][0] is plantPart):
			result += 1
		zAbove += 1
	return result

def claimLocation(location, plantPart):
	# space use is competitive: any newcomers push others aside
	# keep a list rather than one because when one plant part releases the space
	# the next in line can have it
	# so this is sort of a "waiting list" for the space
	space[location].insert(0, plantPart)
	
def releaseLocation(location, plantPart):
	if plantPart in space[location]:
		space[location].remove(plantPart)
	
def clearSpace():
	for i in range(sizeOfSpace):
		for j in range(sizeOfSpace):
			for k in range (sizeOfSpace):
				space[(i,j,k)] = []

def colorForLocation(location):
	if space.has_key(location):
		if space[location]:
			plantPart = space[location][0]
			if plantPart:
				name = plantPart.__class__.__name__
				if name == "Meristem":
					if plantPart.alive:
						return COLOR_MERISTEM
					else:
						return COLOR_MERISTEM_DEAD
				elif name == "Internode":
					if plantPart.alive:
						if plantPart.woody:
							return COLOR_INTERNODE_WOODY
						else:
							return COLOR_INTERNODE_NONWOODY
					else:
						return COLOR_INTERNODE_DEAD
				elif name == "Leaf":
					if plantPart.alive:
						return COLOR_LEAF
					else:
						return COLOR_LEAF_DEAD
				# cfk add others later
	return None

# -------------------------------------------------------------------------------------------
# movement and rotation in space
# -------------------------------------------------------------------------------------------

def displacementInDirection(location, direction, amount):
	#print location, direction
	newX = location[0]
	newY = location[1]
	newZ = location[2]
	if direction == "up":
		newZ += amount
	elif direction == "down":
		newZ -= amount
	elif direction == "north":
		newX += amount
	elif direction == "south":
		newX -= amount
	elif direction == "east":
		newY += amount
	elif direction == "west":
		newY -= amount
	else:
		raise Exception("invalid direction - %s" % direction)
	newX = max(0, min(sizeOfSpace-1, newX))
	newY = max(0, min(sizeOfSpace-1, newY))
	newZ = max(0, min(sizeOfSpace-1, newZ))
	return (newX, newY, newZ)

def dimensionForDirection(direction):
	if direction == "up":
		return "z"
	elif direction == "down":
		return "-z"
	elif direction == "north":
		return "x"
	elif direction == "south":
		return "-x"
	elif direction == "east":
		return "y"
	elif direction == "west":
		return "-y"
	else:
		raise Exception("invalid direction - %s" % direction)
	
def xyzTupleIndexForDimensionName(dimension):
	# use find because it may have other things in it too, like + or -
	if dimension.find('x') >= 0:
		return 0
	elif dimension.find('y') >= 0:
		return 1
	elif dimension.find('z') >= 0:
		return 2

def rotateAround(forward, side, turns):
	if forward == "up":
		turnDirections = ["north", "east", "south", "west"]
	elif forward == "down":
		turnDirections = ["north", "west", "south", "east"]
	elif forward == "north":
		turnDirections = ["up", "east", "down", "west"]
	elif forward == "east":
		turnDirections = ["up", "south", "down", "north"]
	elif forward == "south":
		turnDirections = ["up", "west", "down", "east"]
	elif forward == "west":
		turnDirections = ["up", "north", "down", "south"]
	index = turnDirections.index(side)
	for i in range(turns):
		index += 1
		if index > len(turnDirections)-1:
			index = 0
	newSide = turnDirections[index]
	#print 'rotation: forward', forward, 'side', side, 'turns', turns, 'newside', newSide
	return newSide
			
def locationsBetweenTwoPoints(firstLocation, secondLocation, length):
	locations = []
	for i in range(length):
		proportion = 1.0 * i / length
		x = 1.0 * firstLocation[0] + proportion * (secondLocation[0] - firstLocation[0])
		y = 1.0 * firstLocation[1] + proportion * (secondLocation[1] - firstLocation[1])
		z = 1.0 * firstLocation[2] + proportion * (secondLocation[2] - firstLocation[2])
		locations.append((int(round(x)), int(round(y)), int(round(z))))
	locations.append(secondLocation) # no need to add first location, caller does that
	return locations

def circleAroundPoint(center, diameter, forward, side):
	# http://www.helixsoft.nl/articles/circle/sincos.htm
	firstDirection = side
	secondDirection = rotateAround(forward, side, 1)
	locations = []
	angle = 0.0
	angleStep = 0.2
	radius = diameter / 2.0
	while angle < math.pi * 2.0:
		distanceInFirstDirection = int(round(radius * math.cos(angle)))
		distanceInSecondDirection = int(round(radius * math.sin(angle)))
		locationConsideringFirstDisplacement = displacementInDirection(center, firstDirection, distanceInFirstDirection)
		locationConsideringBothDisplacements = displacementInDirection(locationConsideringFirstDisplacement, secondDirection, distanceInSecondDirection)
		if not locationConsideringBothDisplacements in locations:
			locations.append(locationConsideringBothDisplacements)
		angle += angleStep
	return locations
				
def endPointOfAngledLine(location, length, angleInDegrees, swayInDegrees, forward, parentForward, side):
	# calculate which two dimensions to use the branching angle
	# it goes between your parent branch's forward dimension and your forward dimension
	# calculate the end position in those two dimensions only
	forwardDimension = dimensionForDirection(forward)
	parentForwardDimension = dimensionForDirection(parentForward)
	
	# calculate the angle to be applied to the two dimensions: the standard angle plus some random sway
	angleInRadians = 1.0 * angleInDegrees * math.pi / 180.0 
	swayInRadians = swayInDegrees * math.pi / 180.0
	angleInRadians += swayInRadians
	
	# calculate xy positions in whatever plane is being considered
	movementInForwardDimension = length * math.sin(angleInRadians)
	movementInParentForwardDimension = length * math.cos(angleInRadians)
	
	# based on that calculation, set two of the three end point values
	# note that newLocation has to be an array rather than a tuple because you can't set tuple values individually
	valueNotSet = -999999999
	endLocation = [valueNotSet, valueNotSet, valueNotSet]
	
	# set the value for the dimension corresponding to your forward direction
	forwardDimensionIndex = xyzTupleIndexForDimensionName(forwardDimension)
	# if they were heading in a negative dimension (down, south, west) prepare to subtract rather than add the movement
	if forwardDimension.find('-') >= 0:
		forwardMultiplier = -1
	else:
		forwardMultiplier = 1
	endLocation[forwardDimensionIndex] = location[forwardDimensionIndex] + forwardMultiplier * movementInForwardDimension
	
	# set the value for the dimension corresponding to the parent branch's forward direction
	parentForwardDimensionIndex = xyzTupleIndexForDimensionName(parentForwardDimension)
	if parentForwardDimension.find('-') >= 0:
		parentForwardMultiplier = -1
	else:
		parentForwardMultiplier = 1
	endLocation[parentForwardDimensionIndex] = location[parentForwardDimensionIndex] + parentForwardMultiplier * movementInParentForwardDimension
	
	# now set the one remaining value not set, keeping the value it had before
	# because the movement was in two dimensions but not in the third
	for index in range(len(endLocation)):
		if endLocation[index] == valueNotSet:
			endLocation[index] = location[index]
			
	newX = max(0, min(sizeOfSpace-1, int(round(endLocation[0]))))
	newY = max(0, min(sizeOfSpace-1, int(round(endLocation[1]))))
	newZ = max(0, min(sizeOfSpace-1, int(round(endLocation[2]))))
	endLocation = (newX, newY, newZ)
	#print 'length', length, 'start', location, 'end', endLocation
	#print '.... forwardDimension', forwardDimension, 'parentForwardDimension', parentForwardDimension
	#print '........ movementInForwardDimension', movementInForwardDimension, 'movementInParentForwardDimension', movementInParentForwardDimension
	return endLocation

# -------------------------------------------------------------------------------------------
# parameters
# -------------------------------------------------------------------------------------------

INDENT = '    '
DIRECTIONS = ["north", "east", "south", "west", "up", "down"]

# STRUCTURE
LEAVES_PER_INTERNODE = 2
BRANCHES_PER_ROOT_INTERNODE = 1
FIRST_INTERNODE_FORWARD_DIRECTION = "up"
FIRST_INTERNODE_SIDE_DIRECTION = "east"

INTERNODE_LENGTH_AT_FULL_SIZE = 12
INTERNODE_LENGTH_AT_CREATION = 3 # no less than 3, to have room for buds and leaves
INTERNODE_WIDTH_AT_FULL_SIZE = 3
INTERNODE_WIDTH_AT_CREATION = 1

LEAF_LENGTH_AT_FULL_SIZE = 4
LEAF_LENGTH_AT_CREATION = 1
LEAF_PETIOLE_LENGTH_AT_FULL_SIZE = 4
LEAF_PETIOLE_ANGLE_WITH_STEM = 20
LEAF_ANGLE_WITH_STEM = 40
LEAF_SHAPE_ANGLE = 30
RANDOM_LEAF_SWAY = 20
LEAF_SHAPE_PATTERN = "2222"

# BRANCHING
BRANCHING_PROBABILITY = 0.4
APICAL_DOMINANCE_EXTENDS_FOR = 5
ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK = 40
ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK = 20
RANDOM_INTERNODE_SWAY = 30
MAX_NUM_INTERNODES_ON_PLANT_EVER = 50 # this is a check on all the other parameters blowing up into a giant plant

# BIOMASS
OPTIMAL_LEAF_BIOMASS = 8
OPTIMAL_INTERNODE_BIOMASS = 6
START_LEAF_BIOMASS = 1
START_INTERNODE_BIOMASS = 1
START_MERISTEM_BIOMASS = 3

# UPTAKE
BIOMASS_MADE_BY_FULL_SIZED_LEAF_PER_DAY_OF_PHOTOSYNTHESIS_WITH_FULL_SUN = 10
BIOMASS_MADE_BY_FULL_SIZED_NON_WOODY_INTERNODE_PER_DAY_WITH_FULL_SUN = 2
INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS = 8
SHADE_TOLERANCE = 10

# CONSUMPTION
BIOMASS_USED_BY_LEAF_PER_DAY = 0.5
BIOMASS_USED_BY_INTERNODE_PER_DAY = 0.2
BIOMASS_USED_BY_MERISTEM_PER_DAY = 0.1

# DISTRIBUTION
BIOMASS_DISTRIBUTION_SPREAD_PERCENT = 75
BIOMASS_DISTRIBUTION_ORDER = ["leaves",'branches', 'axillary meristems', "apical meristems", "child"]

# GROWTH
BIOMASS_TO_MAKE_ONE_PHYTOMER = 10

# SIGNAL PROPAGATION

# DEATH
DEATH_BIOMASS_LEAF = 0.1
DEATH_BIOMASS_INTERNODE = 0.01
DEATH_BIOMASS_MERISTEM = 0.5

# DRAWING
COLOR_MERISTEM = "#7CFC00"
COLOR_MERISTEM_DEAD = "#8B8B83"
COLOR_INTERNODE_WOODY = "#CC7F32"
COLOR_INTERNODE_NONWOODY = "#8FBC8F"
COLOR_INTERNODE_DEAD = "#292421"
COLOR_LEAF = "#488214"
COLOR_LEAF_DEAD = "#5E2605"

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
		# used by leaf and internode so to avoid duplication, keep here
		# 1. the more sun where you are, the more you can get at
		sunProportion = sun[(location[0], location[1])]
		# 2. the higher you are the more sun you get (but this is a smaller factor)
		heightProportion = 0.8 + 0.2 * (1.0 * location[2] / sizeOfSpace)
		# 3. the more things above you the less light you get
		numBlocksShadingMe = blocksOccupiedAboveLocation(location, self)
		if numBlocksShadingMe > 0:
			shadeProportion = max(0.0, min(1.0, 1.0 - 1.0 * numBlocksShadingMe / SHADE_TOLERANCE))
		else:
			shadeProportion = 1.0
		# 4. all of these effects multiply
		combinedEffectsProportion = sunProportion * heightProportion * shadeProportion
		# 5. photosynthesis depends on biomass accumulated (water and nutrients later)
		photosynthesisProportion = combinedEffectsProportion * (1.0 - math.exp(-0.65 * self.biomass))
		# 5. finally we end up with a proporton of the optimal
		newBiomass = max(0.0, photosynthesisProportion * optimalAmount) 
		return newBiomass
		
# -------------------------------------------------------------------------------------------
class Meristem(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, numberOnInternode, location, forward, side, apical=False, biomass=0, water=0, minerals=0):
		PlantPart.__init__(self, plant, parent, location, forward, side, biomass=START_MERISTEM_BIOMASS, water=0, minerals=0)
		self.apical = apical
		self.numberOnInternode = numberOnInternode
		self.active = False
		
	def buildInternode(self, firstOnPlant=False):
		if self.apical:
			newSide = rotateAround(self.forward, self.side, 1)
			if self.parent:
				parentBranchForward = self.parent.parentBranchForward
			else:
				parentBranchForward = FIRST_INTERNODE_FORWARD_DIRECTION
		else:   
			if self.parent:
				newSide = self.side
				parentBranchForward = self.parent.forward
			else:
				newSide = FIRST_INTERNODE_SIDE_DIRECTION
				parentBranchForward = FIRST_INTERNODE_FORWARD_DIRECTION
		firstOnBranch = firstOnPlant or not self.apical
		
		newInternode = Internode(self.plant, self.parent, self.location, self.forward, newSide, 
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
		if self.biomass - BIOMASS_USED_BY_MERISTEM_PER_DAY < DEATH_BIOMASS_MERISTEM:
			self.die()
		else:
			if self.apical:
				self.active = True
			else:
				self.calculateActivityLevel()
			if self.active:
				self.biomass -= BIOMASS_USED_BY_MERISTEM_PER_DAY
				
	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		if self.active:
			if self.biomass >= BIOMASS_TO_MAKE_ONE_PHYTOMER:
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
			if self.plant.numInternodesCreated <= MAX_NUM_INTERNODES_ON_PLANT_EVER:
				distance = self.distanceOfParentFromBranchApex()
				if distance > 0:
					probability = BRANCHING_PROBABILITY * distance / APICAL_DOMINANCE_EXTENDS_FOR
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
			distance = APICAL_DOMINANCE_EXTENDS_FOR + 1 # you can develop if the apex was removed
		return distance
		
	def nextDay_SignalPropagation(self):
		pass
	
	def acceptBiomass(self, biomassOffered):
		biomassINeed = max(0, (BIOMASS_TO_MAKE_ONE_PHYTOMER + BIOMASS_USED_BY_MERISTEM_PER_DAY) - self.biomass)
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		#print 'biomassINeed', biomassINeed, 'biomassIWillAccept', biomassIWillAccept, 'biomass', self.biomass
		#print 'meristem took %s biomass from internode' % biomassIWillAccept
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
	
	def display(self, indentCounter=0):
		if self.apical:
			print INDENT * indentCounter, 'apical meristem: biomass', self.biomass, "active", self.active, "forward", self.forward, "side", self.side
		else:
			print INDENT * indentCounter, 'axillary meristem: biomass', self.biomass, "active", self.active,"forward", self.forward, "side", self.side
		
# -------------------------------------------------------------------------------------------
class Internode(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, location, forward, side, firstOnPlant, firstOnBranch, parentBranchForward, iAmABranchOffMyParent):
		PlantPart.__init__(self, plant, parent, location, forward, side, biomass=START_INTERNODE_BIOMASS, water=0, minerals=0)
		self.child = None
		self.branches = []
		self.firstOnPlant = firstOnPlant
		self.firstOnBranch = firstOnBranch
		self.parentBranchForward = parentBranchForward
		self.iAmABranchOffMyParent = iAmABranchOffMyParent
		self.plant.numInternodesCreated += 1
		self.randomSway = random.randrange(RANDOM_INTERNODE_SWAY) - RANDOM_INTERNODE_SWAY // 2
		
		self.woody = (INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS == 0)
		self.length = INTERNODE_LENGTH_AT_CREATION
		self.width = INTERNODE_WIDTH_AT_CREATION
		self.recalculateBlockPlacementsForChangeInLength()
		
		self.buildLeaves()
		self.buildMeristems()
		
	def buildMeristems(self):
		location = self.locationForApicalMeristem()
		self.apicalMeristem = Meristem(self.plant, self, 0, location, self.forward, self.side, apical=True)
		self.axillaryMeristems = []
		for i in range(LEAVES_PER_INTERNODE):
			location, forward, side = self.locationAndDirectionsForAxillaryMeristem(i)
			newAxillaryMeristem = Meristem(self.plant, self, i, location, forward, side, apical=False)
			self.axillaryMeristems.append(newAxillaryMeristem)
		
	def buildLeaves(self):
		self.leaves = []
		for i in range(LEAVES_PER_INTERNODE):
			location, forward, side = self.locationAndDirectionsForLeaf(i)
			newLeaf = Leaf(self.plant, self, i, location, forward, side)
			self.leaves.append(newLeaf)
			
	def locationForApicalMeristem(self):
		locationOneFurther = displacementInDirection(self.endLocation, self.forward, 1)
		return locationOneFurther
	
	def locationAndDirectionsForAxillaryMeristem(self, meristemNumber):
		if LEAVES_PER_INTERNODE == 1:
			meristemForward = self.side
		elif LEAVES_PER_INTERNODE == 2:
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
		
	def locationAndDirectionsForLeaf(self, leafNumber):
		locationOneDownFromEnd = displacementInDirection(self.endLocation, self.forward, -1)
		if LEAVES_PER_INTERNODE == 1:
			leafForward = self.side
		elif LEAVES_PER_INTERNODE == 2:
			if leafNumber == 1:
				leafForward = self.side
			else:
				leafForward = rotateAround(self.forward, self.side, 2)
		else:
			if leafNumber == 1:
				leafForward = self.side
			else:
				leafForward = rotateAround(self.forward, self.side, leafNumber)
		location = displacementInDirection(locationOneDownFromEnd, leafForward, self.width//2)
		leafSide = self.forward
		# looks strange if leaves don't point to the side
		if leafSide in ["up", "down"]:
			leafSide = rotateAround(leafForward, leafSide, 1)
		return location, leafForward, leafSide
	
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
		if not self.woody:
			newBiomass = self.calculatePhotosynthesis(self.endLocation, BIOMASS_MADE_BY_FULL_SIZED_NON_WOODY_INTERNODE_PER_DAY_WITH_FULL_SUN)
			self.biomass += newBiomass
		#print self.age, 'biomass after uptake', self.biomass
	
	def nextDay_Consumption(self):
		#print self.age, 'biomass before consumption', self.biomass
		if self.woody: #internodes don't use any biomass up once they have stopped photosynthesizing
			biomassINeedToUseToday = 0
		else:
			biomassINeedToUseToday = BIOMASS_USED_BY_INTERNODE_PER_DAY
		if self.biomass - biomassINeedToUseToday < DEATH_BIOMASS_INTERNODE:
			self.die()
		else:
			self.biomass -= biomassINeedToUseToday
		#print self.age, 'biomass after consumption', self.biomass
	
	def die(self):
		sendDieSignalTo = []
		sendDieSignalTo.extend(self.leaves)
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
		for name in BIOMASS_DISTRIBUTION_ORDER:
			if name == "leaves":
				supplicants.extend(self.leaves)
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
		extraBiomass = max(0, self.biomass - OPTIMAL_INTERNODE_BIOMASS)
		toBeGivenAway = extraBiomass * BIOMASS_DISTRIBUTION_SPREAD_PERCENT / 100.0
		for supplicant in supplicants:
			if supplicant and extraBiomass > 0:
				biomassTakenBySupplicant = supplicant.acceptBiomass(toBeGivenAway)
				#print '      biomass', self.biomass, 'extraBiomass', extraBiomass, 'toBeGivenAway', toBeGivenAway, 'taken', biomassTakenBySupplicant
				self.biomass -= biomassTakenBySupplicant
				extraBiomass = max(0, self.biomass - OPTIMAL_INTERNODE_BIOMASS)
				toBeGivenAway = extraBiomass * BIOMASS_DISTRIBUTION_SPREAD_PERCENT / 100.0
		#print self.age, 'biomass after distribution', self.biomass
	
	def nextDay_Growth(self):
		self.woody = self.age > INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS
		proportion = self.biomass / OPTIMAL_INTERNODE_BIOMASS
		self.length = max(1, min(INTERNODE_LENGTH_AT_FULL_SIZE, int(round(proportion * INTERNODE_LENGTH_AT_FULL_SIZE))))
		self.width = max(1, min(INTERNODE_WIDTH_AT_FULL_SIZE, int(round(proportion * INTERNODE_WIDTH_AT_FULL_SIZE))))
		self.recalculateBlockPlacementsForChangeInLength()
		
	def nextDay_SignalPropagation(self):
		sendNextDayTo = []
		sendNextDayTo.extend(self.leaves)
		sendNextDayTo.extend([self.apicalMeristem])
		sendNextDayTo.extend(self.axillaryMeristems)
		sendNextDayTo.extend([self.child])
		sendNextDayTo.extend(self.branches)
		for sendTo in sendNextDayTo:
			if sendTo:
				sendTo.nextDay()
		
	def recalculateBlockPlacementsForChangeInLength(self):
		if not self.iAmABranchOffMyParent:
			if self.parent:
				self.location = self.parent.locationForChildInternode()
		# testing the parent branch forward is a kludgy way of trying to find out if you have branched
		# off the main trunk without saving the information
		# CFK BETTER WAY!!!
		if self.parentBranchForward == FIRST_INTERNODE_FORWARD_DIRECTION:
			angleInDegrees = ANGLE_BETWEEN_STEM_AND_BRANCH_OFF_TRUNK
		else:
			angleInDegrees = ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK
		self.endLocation = endPointOfAngledLine(self.location, self.length, 
					angleInDegrees, self.randomSway, self.forward, self.parentBranchForward, self.side)
		# now interpolate between the start and end positions to produce a rough line
		locationsBetween = locationsBetweenTwoPoints(self.location, self.endLocation, self.length)
		
		# place yourself in the locations
		self.claimStartBlock()
		self.claimSeriesOfBlocks(locationsBetween)
		if self.width > 1:
			for location in locationsBetween:
				circleLocations = circleAroundPoint(location, self.width, self.forward, self.side)
				self.claimSeriesOfBlocks(circleLocations)
			
	def display(self, indentCounter=0):
		print INDENT * indentCounter, 'internode: biomass', self.biomass, ", forward", self.forward, ", side", self.side
		for leaf in self.leaves:
			leaf.display(indentCounter+1)
		if self.apicalMeristem:
			self.apicalMeristem.display(indentCounter+1)
		for meristem in self.axillaryMeristems:
			meristem.display(indentCounter+1)
		if self.child:
			self.child.display(indentCounter+1)
			
# -------------------------------------------------------------------------------------------
class Leaf(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, numberOnInternode, location, forward, side):
		PlantPart.__init__(self, plant, parent, location, forward, side, biomass=START_LEAF_BIOMASS, water=0, minerals=0)
		self.numberOnInternode = numberOnInternode
		self.length = LEAF_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_LEAF_SWAY) - RANDOM_LEAF_SWAY // 2
				
	def nextDay_Uptake(self):
		newBiomass = self.calculatePhotosynthesis(self.location, BIOMASS_MADE_BY_FULL_SIZED_LEAF_PER_DAY_OF_PHOTOSYNTHESIS_WITH_FULL_SUN)
		self.biomass += newBiomass
	
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_LEAF_PER_DAY < DEATH_BIOMASS_LEAF:
			self.die()
		else:
			self.biomass -= BIOMASS_USED_BY_LEAF_PER_DAY
	
	def nextDay_Distribution(self):
		extraBiomass = max(0, self.biomass - OPTIMAL_LEAF_BIOMASS)
		biomassTakenByParent = self.parent.acceptBiomass(extraBiomass)
		self.biomass -= biomassTakenByParent
	
	def nextDay_Growth(self):
		location, direction, side = self.parent.locationAndDirectionsForLeaf(self.numberOnInternode)
		self.location = location

		proportion = self.biomass / OPTIMAL_LEAF_BIOMASS
		self.length = max(1, min(LEAF_LENGTH_AT_FULL_SIZE, int(round(proportion * LEAF_LENGTH_AT_FULL_SIZE))))
		self.petioleLength = max(1, min(LEAF_PETIOLE_LENGTH_AT_FULL_SIZE, int(round(proportion * LEAF_PETIOLE_LENGTH_AT_FULL_SIZE))))
		self.recalculateBlockPlacementsForChangeInSize()
		
	def recalculateBlockPlacementsForChangeInSize(self):
		self.claimStartBlock()
		if self.petioleLength > 1:
			endLocationForPetiole = endPointOfAngledLine(self.location, self.petioleLength, 
						LEAF_PETIOLE_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward, self.side)
			petioleLine = locationsBetweenTwoPoints(self.location, endLocationForPetiole, self.petioleLength)
			self.claimSeriesOfBlocks(petioleLine)
		else:
			endLocationForPetiole = displacementInDirection(self.location, self.forward, 1)
			claimLocation(endLocationForPetiole, self)

		if self.length > 1:
			endLocationForLeaf = endPointOfAngledLine(endLocationForPetiole, self.length, 
						LEAF_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward, self.side)
			leafSpine = locationsBetweenTwoPoints(endLocationForPetiole, endLocationForLeaf, self.length)
			self.claimSeriesOfBlocks(leafSpine)
			
			drawLines = True
		
			leafLengthIndex = 0
			leafSides = []
			for location in leafSpine:
				shapeLookupIndex = leafLengthIndex % len(LEAF_SHAPE_PATTERN)
				sideExtent = int(LEAF_SHAPE_PATTERN[shapeLookupIndex])
				proportion = self.biomass / OPTIMAL_LEAF_BIOMASS
				sideExtentConsideringBiomass = max(0, min(sideExtent, int(round(proportion * sideExtent))))
				if sideExtentConsideringBiomass > 0:
					for sideMultiplier in [1, -1]:
						if drawLines:
							if sideMultiplier == -1:
								sideDirection = self.side
							else:
								sideDirection = rotateAround(self.forward, self.side, 2)
							# location, length, angleInDegrees, swayInDegrees, forward, parentForward, side
							endLocationForLeafSide = endPointOfAngledLine(location, sideExtentConsideringBiomass, 
										LEAF_SHAPE_ANGLE, self.randomSway, sideDirection, "down", self.forward)
							oneSidePiece = locationsBetweenTwoPoints(location, endLocationForLeafSide, sideExtentConsideringBiomass)
							leafSides.extend(oneSidePiece)
						else:
							for degree in range(sideExtentConsideringBiomass):
								newLocation = displacementInDirection(location, self.side, sideMultiplier * degree)
								leafSides.append(newLocation)
				leafLengthIndex += 1
			self.claimSeriesOfBlocks(leafSides)
		else:
			endLocationForLeaf = displacementInDirection(endLocationForPetiole, self.forward, 1)
			claimLocation(endLocationForLeaf, self)

	def nextDay_SignalPropagation(self):
		pass

	def acceptBiomass(self, biomassOffered):
		biomassINeed = max(0, (OPTIMAL_LEAF_BIOMASS + BIOMASS_USED_BY_LEAF_PER_DAY) - self.biomass)
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		#print 'leaf took %s biomass from internode' % biomassIWillAccept
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
	def display(self, indentCounter=0):
		print INDENT * indentCounter, 'leaf: biomass', self.biomass, ", forward", self.forward, ", side", self.side
		
# -------------------------------------------------------------------------------------------
class RootMeristem(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent, apical):
		PlantPart.__init__(self, plant)
		self.apical = apical
		self.parent = parent
	
	def buildRootPhytomer(self):
		rootInternode = RootInternode(self.plant, [self.parent], first=False)
		for i in range(BRANCHES_PER_ROOT_INTERNODE):
			rootInternode.addRootMeristem(RootMeristem(self.plant, rootInternode, apical=False))
		if self.parent:
			self.parent.addChildInternode(rootInternode)
		return rootInternode
	
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
		print INDENT * indentCounter, 'root meristem', self.biomass
		
# -------------------------------------------------------------------------------------------
class RootInternode(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parents, first):
		PlantPart.__init__(self, plant)
		self.parents = parents
		self.children = []
		self.meristems = []
		self.first = first
	
	def addRootMeristem(self, meristem):
		self.meristems.append(meristem)
		
	def addChildInternode(self, internode):
		self.children.append(internode)
	
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
		print INDENT * indentCounter, 'root internode', self.biomass
		for meristem in self.meristems:
			meristem.display(indentCounter+1)
		for child in self.children:
			child.display(indentCounter+1)
		
# -------------------------------------------------------------------------------------------
class Inflorescence(PlantPart):
# -------------------------------------------------------------------------------------------
	def __init__(self, plant, parent):
		PlantPart.__init__(self, plant)
		self.parent = parent 
		self.flowers = []
		self.fruits = []
	
	def display(self, indentCounter=0):
		print INDENT * indentCounter, 'inflorescence', self.biomass
		for flower in self.flowers():
			flower.display(indentCounter+1)
		for fruit in self.fruits():
			fruit.display(indentCounter+1)
		
# -------------------------------------------------------------------------------------------
class Flower(PlantPart):
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
class Fruit(PlantPart):
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
		self.seed = random.random()
		random.seed(self.seed)
		firstMeristem = Meristem(self, None, 0, self.location, FIRST_INTERNODE_FORWARD_DIRECTION, FIRST_INTERNODE_SIDE_DIRECTION, apical=True)
		self.firstInternode = firstMeristem.buildInternode(firstOnPlant=True)
		#firstRootMeristem = RootMeristem(self, None, apical=True)
		#self.firstRootInternode = firstRootMeristem.buildRootPhytomer()
		
	def nextDay(self):
		self.firstInternode.nextDay()
		#self.firstRootInternode.nextDay()
		self.age += 1
		
	def display(self):
		print 'plant'
		self.firstInternode.display()
		#self.firstRootInternode.display()
		
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
def growPlant(outputFolder):
	print 'starting...'
	#drawSunDistribution(outputFolder)
	daysPerPulse = 2
	numPulses = 15
	plants = []
	numPlants = 3
	for i in range(numPlants):
		if numPlants == 1:
			xLocation = 50
			yLocation = 50
		else:
			xLocation = 10 + random.randrange(80)
			yLocation = 10 + random.randrange(80)
		plants.append(Plant(xLocation, yLocation, 1))
	#for plant in plants:
	#	plant.display()
	
	day = 1
	for i in range(numPulses):
		for j in range(daysPerPulse):
			#clearSpace()
			for plant in plants:
				plant.nextDay()
				#plant.display()
		drawSpace(day, outputFolder, drawSun=True)
		day += daysPerPulse
	
	print 'done'
	
def drawSpace(age, outputFolder, drawSun):
	xValues = []
	yValues = []
	zValues = []
	colors = []
	if drawSun:
		for i in range(sizeOfSpace):
			for j in range(sizeOfSpace):
				xValues.append(i)
				yValues.append(j)
				zValues.append(0)
				colors.append(str(sun[(i,j)]))
	for i in range(sizeOfSpace):
		for j in range(sizeOfSpace):
			for k in range (sizeOfSpace):
				color = colorForLocation((i,j,k))
				if color:
					xValues.append(i)
					yValues.append(j)
					zValues.append(k)
					colors.append(color)
	filename = "Test tree growth age %s" % age
	graphPNG3DScatter(xValues, yValues, zValues, colors, sizeOfSpace, "x", "y", "z", "tree growth", filename, outputFolder)
	#print 'file %s written' % filename
	
def drawSunDistribution(outputFolder):
	xValues = []
	yValues = []
	zValues = []
	colors = []
	for i in range(sizeOfSpace):
		for j in range(sizeOfSpace):
			xValues.append(i)
			yValues.append(j)
			zValues.append(sizeOfSpace-1)
			colors.append(sun[(i,j)])
	filename = "Sun coverage"
	graphPNG3DScatter(xValues, yValues, zValues, colors, sizeOfSpace, "x", "y", "z", "sun coverage", filename, outputFolder)
		
def main():
	iterations = 1
	for i in range(iterations):
		outputFolder = setUpOutputFolder("/Users/cfkurtz/Documents/personal/terasology/generated images/")
		print 'writing files to:', outputFolder
		growPlant(outputFolder)
	
if __name__ == "__main__":
	main()
	
