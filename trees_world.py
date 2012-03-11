# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

import os, math, random
import numpy as np

from trees_parameters import *
from trees_graphics import *

import matplotlib.cm as cm
import matplotlib.colors as mpcolors

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
	for i in range(NUM_WATER_PATCHES):
		i = random.randrange(SIZE_OF_SPACE_XY)
		j = random.randrange(SIZE_OF_SPACE_XY)
		k = random.randrange(GROUND_LEVEL+1)
		# CFK FIX - could go out of range
		for x in range(i-WATER_PATCH_RADIUS, i+WATER_PATCH_RADIUS):
			for y in range(j-WATER_PATCH_RADIUS, j+WATER_PATCH_RADIUS):
				for z in range(k-WATER_PATCH_RADIUS, k+WATER_PATCH_RADIUS):
					water[(x, y, z)] = random.random()
else:
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL+1):
				water[(i,j,k)] = 1.0

print 'generating mineral deposits...'
		
# generate underground minerals
minerals = {}
if PATCHY_MINERALS:
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

def blocksOccupiedAboveLocation(location, treePart):
	x = location.x
	y = location.y
	z = location.z
	result = 0
	zAbove = min(SIZE_OF_SPACE_XY-1, z+1)
	while zAbove <= SIZE_OF_SPACE_XY-1:
		locationAbove = Point3D(x, y, zAbove)
		if space.has_key(locationAbove) and space[locationAbove] and not (space[locationAbove][0] is treePart):
			result += 1
		zAbove += 1
	return result

def claimLocation(location, treePart):
	# space use is competitive: any newcomers push others aside as the growth signal passes through the tree
	# keep a list rather than a pointer, because when one tree part releases the space
	# the next in line can have it
	# so the list is sort of a "waiting list" for the space
	if not space.has_key(location):
		space[location] = []
	space[location].insert(0, treePart)
	
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
		if water.has_key(location) and minerals.has_key(location):
			bestWaterAndMinerals = water[location] + minerals[location]
		else:
			bestWaterAndMinerals = 0
		startZ = max(0, min(GROUND_LEVEL, z-seekRadius))
		stopZ = max(0, min(GROUND_LEVEL, z+seekRadius))
		for i in range(startX, stopX):
			for j in range(startY, stopY):
				for k in range(startZ, stopZ):
					if water.has_key((i,j,k)) and minerals.has_key((i,j,k)):
						waterAndMinerals = water[(i,j,k)] + minerals[(i,j,k)]
					else:
						waterAndMinerals = 0
					if waterAndMinerals > bestWaterAndMinerals:
						bestWaterAndMinerals = waterAndMinerals
						bestLocation = Point3D(i,j,k)
	else:
		bestSun = sun[(x,y)]
		for i in range(startX, stopX):
			for j in range(startY, stopY):
				sunHere = sun[(i,j)]
				if sunHere > bestSun:
					bestSun = sunHere
					bestLocation = Point3D(i,j, z)
	if bestLocation:
		return bestLocation
	else:
		return location
	
def waterOrMineralsInRegion(waterOrMinerals, location, radius):
	x = int(round(location.x))
	y = int(round(location.y))
	z = int(round(location.z))
	startX = max(0, min(SIZE_OF_SPACE_XY-1, x-radius))
	stopX = max(0, min(SIZE_OF_SPACE_XY-1, x+radius))
	startY = max(0, min(SIZE_OF_SPACE_XY-1, y-radius))
	stopY = max(0, min(SIZE_OF_SPACE_XY-1, y+radius))
	startZ = max(0, min(GROUND_LEVEL, z-radius))
	stopZ = max(0, min(GROUND_LEVEL, z+radius))
	available = 0
	locationsConsidered = []
	if waterOrMinerals == "water":
		resource = water
	else:
		resource = minerals
	for i in range(startX, stopX):
		for j in range(startY, stopY):
			for k in range(startZ, stopZ):
				if resource.has_key((i,j,k)):
					available += resource[(i,j,k)]
				locationsConsidered.append((i,j,k))
	return available, locationsConsidered
	
def releaseLocation(location, treePart):
	if treePart in space[location]:
		space[location].remove(treePart)
	
def colorForLocation(location):
	if space.has_key(location):
		if space.has_key(location) and space[location]:
			treePart = space[location][0]
			if treePart:
				name = treePart.__class__.__name__
				if name == "Meristem":
					if treePart.alive:
						color = COLOR_MERISTEM[treePart.root]
					else:
						color = COLOR_MERISTEM_DEAD[treePart.root]
				elif name == "Internode":
					if treePart.alive:
						if treePart.woody:
							color = COLOR_INTERNODE_WOODY
						else:
							color = COLOR_INTERNODE_NONWOODY[treePart.root]
					else:
						color = COLOR_INTERNODE_DEAD[treePart.root]
				elif name == "LeafCluster":
					if treePart.alive:
						color = COLOR_LEAF_CLUSTER
					else:
						color = COLOR_LEAF_CLUSTER_DEAD
				elif name == "FlowerCluster":
					if treePart.alive:
						color = COLOR_FLOWER_CLUSTER
					else:
						color = COLOR_FLOWER_CLUSTER_DEAD
				elif name == "FruitCluster":
					if treePart.alive:
						color = COLOR_FRUIT_CLUSTER
					else:
						color = COLOR_FRUIT_CLUSTER_DEAD
				return mpcolors.colorConverter.to_rgba(color)
	return None

def drawSpace(age, outputFolder, drawTrees=True, drawSun=False, drawWater=False, drawMinerals=False, drawSurface=False):
	allXValues = []
	allYValues = []
	allZValues = []
	allColors = []
	if drawSun:
		xValues, yValues, zValues, colors = sunBlocksToGraph()
		allXValues.extend(xValues)
		allYValues.extend(yValues)
		allZValues.extend(zValues)
		allColors.extend(colors)
	if drawWater:
		xValues, yValues, zValues, colors = waterBlocksToGraph()
		allXValues.extend(xValues)
		allYValues.extend(yValues)
		allZValues.extend(zValues)
		allColors.extend(colors)
	if drawMinerals:
		xValues, yValues, zValues, colors = mineralBlocksToGraph()
		allXValues.extend(xValues)
		allYValues.extend(yValues)
		allZValues.extend(zValues)
		allColors.extend(colors)
	if drawSurface:
		spacing = 5
		whiteColor = mpcolors.colorConverter.to_rgba('white')
		for i in range(SIZE_OF_SPACE_XY):
			for j in range(SIZE_OF_SPACE_XY):
				if (i % spacing == 0) and (j % spacing == 0):
					allXValues.append(i)
					allYValues.append(j)
					allZValues.append(GROUND_LEVEL+1)
					allColors.append(whiteColor)
	if drawTrees:
		xValues = []
		yValues = []
		zValues = []
		colors = []
		for k in range (SIZE_OF_SPACE_Z): # order by height
			for i in range(SIZE_OF_SPACE_XY):
				for j in range(SIZE_OF_SPACE_XY):
					color = colorForLocation(Point3D(i,j,k))
					if color:
						xValues.append(i)
						yValues.append(j)
						zValues.append(k)
						colors.append(color)
		allXValues.extend(xValues)
		allYValues.extend(yValues)
		allZValues.extend(zValues)
		allColors.extend(colors)
	#print allColors
	filename = "Tree growth age %s" % age
	graphPNG3DScatter(allXValues, allYValues, allZValues, allColors, SIZE_OF_SPACE_XY, "x", "y", "z", "tree growth", filename, outputFolder)
	
def drawSunDistribution(outputFolder):
	xValues, yValues, zValues, colors = sunBlocksToGraph()
	graphPNG3DScatter(xValues, yValues, zValues, colors, SIZE_OF_SPACE_XY, "x", "y", "z", "sun coverage", "Sun coverage", outputFolder)
	print 'sun coverage graphed'
	
def sunBlocksToGraph():
	xValues = []
	yValues = []
	zValues = []
	colors = []
	autumn = cm.get_cmap("autumn")
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			if sun[(i,j)] > 0:
				xValues.append(i)
				yValues.append(j)
				zValues.append(0)
				color = autumn(sun[(i,j)])
				colors.append(color)
	return xValues, yValues, zValues, colors
		
def drawWaterDistribution(outputFolder):
	xValues, yValues, zValues, colors = waterBlocksToGraph()
	graphPNG3DScatter(xValues, yValues, zValues, colors, 
					SIZE_OF_SPACE_XY, "x", "y", "z", "water distribution", "Water distribution", outputFolder, drawLines=False)
	print 'water distribution graphed'
	
def waterBlocksToGraph():
	xValues = []
	yValues = []
	zValues = []
	colors = []
	blues = cm.get_cmap("Blues")
	for k in range(GROUND_LEVEL):
		for i in range(SIZE_OF_SPACE_XY):
			for j in range(SIZE_OF_SPACE_XY):
				if water.has_key((i,j,k)) and water[(i,j,k)] > 0:
					xValues.append(i)
					yValues.append(j)
					zValues.append(k)
					color = blues(water[(i,j,k)])
					colors.append(color)
	return xValues, yValues, zValues, colors

def drawMineralsDistribution(outputFolder):
	xValues, yValues, zValues, colors = mineralBlocksToGraph()
	graphPNG3DScatter(xValues, yValues, zValues, colors, 
					SIZE_OF_SPACE_XY, "x", "y", "z", "mineral deposits", "Mineral deposits", outputFolder, drawLines=False)
	print 'mineral deposits graphed'
	
def mineralBlocksToGraph():
	xValues = []
	yValues = []
	zValues = []
	colors = []
	copper = cm.get_cmap("copper")
	for k in range(GROUND_LEVEL):
		for i in range(SIZE_OF_SPACE_XY):
			for j in range(SIZE_OF_SPACE_XY):
				if minerals.has_key((i,j,k)) and minerals[(i,j,k)] > 0:
					xValues.append(i)
					yValues.append(j)
					zValues.append(k)
					color = copper(minerals[(i,j,k)])
					colors.append(color)
	return xValues, yValues, zValues, colors


