# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

import os, math, random
import numpy as np

from trees_parameters import *
from trees_graphics import *

space = {}

print 'generating sun coverage...'

# generate patchy sun map
sun = {}
highestSun = 0
for i in range(SIZE_OF_SPACE_XY):
	for j in range(SIZE_OF_SPACE_XY):
		if PATCHY_SUN:
			sun[(i,j)] = abs(math.sin(1.0*i/10) + math.cos(1.0*j/10))
		else:
			sun[(i,j)] = 1.0
		if sun[(i,j)] > highestSun:
			highestSun = sun[(i,j)]
		
# normalize sun map
for i in range(SIZE_OF_SPACE_XY):
	for j in range(SIZE_OF_SPACE_XY):
		sun[(i,j)] = sun[(i,j)] / highestSun

print 'generating water distribution...'
		
# generate underground water
water = {}
if PATCHY_WATER:
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL+1):
				water[(i,j,k)] = 0.0
	for i in range(NUM_WATER_PATCHES):
		i = random.randrange(SIZE_OF_SPACE_XY)
		j = random.randrange(SIZE_OF_SPACE_XY)
		k = random.randrange(GROUND_LEVEL+1)
		for x in range(i-WATER_PATCH_RADIUS, i+WATER_PATCH_RADIUS):
			for y in range(j-WATER_PATCH_RADIUS, j+WATER_PATCH_RADIUS):
				for z in range(k-WATER_PATCH_RADIUS, k+WATER_PATCH_RADIUS):
					water[(x, y, z)] = random.random()
else:
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL):
				water[(i,j,k)] = 1.0

# generate underground minerals
minerals = {}
if PATCHY_MINERALS:
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL+1):
				minerals[(i,j,k)] = 0.0
	for i in range(NUM_MINERAL_PATCHES):
		i = random.randrange(SIZE_OF_SPACE_XY)
		j = random.randrange(SIZE_OF_SPACE_XY)
		k = random.randrange(GROUND_LEVEL+1)
		# CFK FIX - could go out of range
		for x in range(i-MINERAL_PATCH_RADIUS, i+MINERAL_PATCH_RADIUS):
			for y in range(j-MINERAL_PATCH_RADIUS, j+MINERAL_PATCH_RADIUS):
				for z in range(k-MINERAL_PATCH_RADIUS, k+MINERAL_PATCH_RADIUS):
					minerals[(x, y, z)] = random.random()
else:
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL+1):
				minerals[(i,j,k)] = 1.0

def locationIsInUse(location):
	return len(space[location]) > 0

def blocksOccupiedAboveLocation(location, plantPart):
	x = location[0]
	y = location[1]
	z = location[2]
	result = 0
	zAbove = min(SIZE_OF_SPACE_XY-1, z+1)
	while zAbove <= SIZE_OF_SPACE_XY-1:
		locationAbove = (x, y, zAbove)
		if space.has_key(locationAbove) and space[locationAbove] and not (space[locationAbove][0] is plantPart):
			result += 1
		zAbove += 1
	return result

def claimLocation(location, plantPart):
	# space use is competitive: any newcomers push others aside as the growth signal passes through the plant
	# keep a list rather than a pointer, because when one plant part releases the space
	# the next in line can have it
	# so the list is sort of a "waiting list" for the space
	if not space.has_key(location):
		space[location] = []
	space[location].insert(0, plantPart)
	
def seekBetterLocation(location, root, seekRadius):
	x = location[0]
	y = location[1]
	z = location[2]
	startX = max(0, min(SIZE_OF_SPACE_XY-1, x-seekRadius))
	stopX = max(0, min(SIZE_OF_SPACE_XY-1, x+seekRadius))
	startY = max(0, min(SIZE_OF_SPACE_XY-1, y-seekRadius))
	stopY = max(0, min(SIZE_OF_SPACE_XY-1, y+seekRadius))
	bestLocation = None
	if root:
		bestWaterAndMinerals = water[location] + minerals[location]
		startZ = max(0, min(GROUND_LEVEL, z-seekRadius))
		stopZ = max(0, min(GROUND_LEVEL, z+seekRadius))
		for i in range(startX, stopX):
			for j in range(startY, stopY):
				for k in range(startZ, stopZ):
					waterAndMinerals = water[(i,j,k)] + minerals[(i,j,k)]
					if waterAndMinerals > bestWaterAndMinerals:
						bestWaterAndMinerals = waterAndMinerals
						bestLocation = (i,j,k)
	else:
		bestSun = sun[(x,y)]
		for i in range(startX, stopX):
			for j in range(startY, stopY):
				sunHere = sun[(i,j)]
				if sunHere > bestSun:
					bestSun = sunHere
					bestLocation = (i,j, z)
	if bestLocation:
		return bestLocation
	else:
		return location
	
def releaseLocation(location, plantPart):
	if plantPart in space[location]:
		space[location].remove(plantPart)
	
def clearSpace():
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range (SIZE_OF_SPACE_XY):
				space[(i,j,k)] = []

def colorForLocation(location):
	if space.has_key(location):
		if space.has_key(location) and space[location]:
			plantPart = space[location][0]
			if plantPart:
				name = plantPart.__class__.__name__
				if name == "Meristem":
					if plantPart.alive:
						return COLOR_MERISTEM[plantPart.root]
					else:
						return COLOR_MERISTEM_DEAD[plantPart.root]
				elif name == "Internode":
					if plantPart.alive:
						if plantPart.woody:
							return COLOR_INTERNODE_WOODY
						else:
							return COLOR_INTERNODE_NONWOODY[plantPart.root]
					else:
						return COLOR_INTERNODE_DEAD[plantPart.root]
				elif name == "LeafCluster":
					if plantPart.alive:
						return COLOR_LEAF_CLUSTER
					else:
						return COLOR_LEAF_CLUSTER_DEAD
				# cfk add others later
	return None

def drawSpace(age, outputFolder, drawSun):
	xValues = []
	yValues = []
	zValues = []
	colors = []
	if drawSun:
		for i in range(SIZE_OF_SPACE_XY):
			for j in range(SIZE_OF_SPACE_XY):
				xValues.append(i)
				yValues.append(j)
				zValues.append(0)
				colors.append(str(sun[(i,j)]))
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range (SIZE_OF_SPACE_Z):
				color = colorForLocation((i,j,k))
				if color:
					xValues.append(i)
					yValues.append(j)
					zValues.append(k)
					colors.append(color)
	filename = "Test tree growth age %s" % age
	graphPNG3DScatter(xValues, yValues, zValues, colors, SIZE_OF_SPACE_XY, "x", "y", "z", "tree growth", filename, outputFolder)
	#print 'file %s written' % filename
	
def drawSunDistribution(outputFolder):
	xValues = []
	yValues = []
	zValues = []
	colors = []
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			xValues.append(i)
			yValues.append(j)
			zValues.append(SIZE_OF_SPACE_XY-1)
			colors.append(sun[(i,j)])
	filename = "Sun coverage"
	graphPNG3DScatter(xValues, yValues, zValues, colors, SIZE_OF_SPACE_XY, "x", "y", "z", "sun coverage", filename, outputFolder)
	print 'sun coverage graphed'
		
def drawWaterDistribution(outputFolder):
	xValues = []
	yValues = []
	zValues = []
	colors = []
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL):
				if water[(i,j,k)] > 0:
					xValues.append(i)
					yValues.append(j)
					zValues.append(k)
					colors.append(str(water[(i,j,k)]))
	filename = "Water distribution"
	graphPNG3DScatter(xValues, yValues, zValues, colors, SIZE_OF_SPACE_XY, "x", "y", "z", "water distribution", filename, outputFolder)
	print 'water distribution graphed'

def drawMineralsDistribution(outputFolder):
	xValues = []
	yValues = []
	zValues = []
	colors = []
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL):
				if minerals[(i,j,k)] > 0:
					xValues.append(i)
					yValues.append(j)
					zValues.append(k)
					colors.append(str(minerals[(i,j,k)]))
	filename = "Mineral deposits"
	graphPNG3DScatter(xValues, yValues, zValues, colors, SIZE_OF_SPACE_XY, "x", "y", "z", "mineral deposits", filename, outputFolder)
	print 'mineral deposits graphed'

