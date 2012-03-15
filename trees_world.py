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

import os, math, random
import numpy as np

from trees_parameters import *
from trees_graphics import *

import matplotlib
matplotlib.use('TkAgg') # do this before importing pylab

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d

import matplotlib.cm as cm
import matplotlib.colors as mpcolors

blues = cm.get_cmap("Blues")
copper = cm.get_cmap("copper")
autumn = cm.get_cmap("autumn")
heatmap = cm.get_cmap("jet")
greens = cm.get_cmap("YlGn")

# -------------------------------------------------------------------------------------------
# Generating world definitions: space, sunlight, water, minerals.

# All of this is a stand-in for a blocky world and can be discarded on integration.
# For sun, there should be a degree of light falling on each vertical space
# which is (optimally) not binary but continuously varying, as effected by clouds and biome.

# For water/minerals, what is needed is to find some water and minerals in existing blocks.
# Species definitions should define what consitutes water and minerals.
# Water need not be found only in water blocks but could be partially present
# in many blocks, as defined by the species. Some might be better at extracting water,
# so what "contains" water for some species might not for others.
# The same is true for minerals.
# -------------------------------------------------------------------------------------------

SIZE_OF_SPACE_XY = 100
SIZE_OF_SPACE_Z = 300
GROUND_LEVEL = 100

PATCHY_SUN = True

PATCHY_WATER = True
NUM_WATER_PATCHES = 50
WATER_PATCH_RADIUS = 4

PATCHY_MINERALS = True
NUM_MINERAL_PATCHES = 50
MINERAL_PATCH_RADIUS = 4

DRAW_ROOTS = True
DRAW_STEMS = True
DRAW_LEAF_CLUSTERS = True
DRAW_MERISTEMS = True
DRAW_FLOWER_CLUSTERS = True
DRAW_FRUIT_CLUSTERS = True

# "biomass", "water", "minerals", "photosynthate", "parts"
COLOR_MAP = "parts"

space = {}

print 'generating sun coverage...'

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
					water[(x, y, z)] = random.random() * 2.0
else:
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL+1):
				water[(i,j,k)] = 1.0
				
print 'generating mineral deposits...'
		
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
					minerals[(x, y, z)] = random.random() * 2.0
else:
	for i in range(SIZE_OF_SPACE_XY):
		for j in range(SIZE_OF_SPACE_XY):
			for k in range(GROUND_LEVEL+1):
				minerals[(i,j,k)] = 1.0
				
# -------------------------------------------------------------------------------------------
# Managing blocks in 3D space.

# This is a stand-in for block assignments. In this model there is no collision avoidance
# mechanism. Instead space use is competitive: any newcomers to a block space push others aside.
# This is partly because it's how plants grow, and partly because I didn't have time to do better.
# Because each part finds its place as the next-day growth signal passes up the tree, this means
# parts higher up in the branches displace parts lower down. Of course this could be reversed
# by having parts go to the end of the stack in the claimLocation() method instead of to the front.
# By keeping a stack of parts waiting to use any space, instead of allowing only one block to have it,
# this means that if the block first in the list recalculates and moves, the one waiting below
# can have the space if they still want it.

# In this proof-of-concept model there is nothing in the space but empty air to start with. 
# When there are other things in the space, a species parameter could determine whether 
# growing plant parts replace existing blocks or avoid them. If they do replace existing blocks, 
# it would make sense to keep a similar "stack" of replaced blocks so that they can be put back 
# if the plant stem moves pr is removed
# -------------------------------------------------------------------------------------------

def claimLocation(location, treePart):
	# location should always be rounded
	if not space.has_key(location):
		space[location] = []
	if treePart in space[location]:
		space[location].remove(treePart)
	space[location].insert(0, treePart)
	
def releaseLocation(location, treePart):
	# location should always be rounded
	if treePart in space[location]:
		space[location].remove(treePart)
	
def boundXYZ(x, y, z, aboveGround=True):
	newX = max(0, min(SIZE_OF_SPACE_XY-1, x))
	newY = max(0, min(SIZE_OF_SPACE_XY-1, y))
	if aboveGround:
		newZ = max(GROUND_LEVEL+1, min(SIZE_OF_SPACE_Z-1, z))
	else:
		newZ = max(0, min(GROUND_LEVEL + ROOTS_CAN_GROW_THIS_MANY_BLOCKS_ABOVE_GROUND, z))
	return newX, newY, newZ
	
def boundLocation(location, aboveGround):
	x, y, z = boundXYZ(location.x, location.y, location.z, aboveGround)
	return Point3D(x, y, z)

def blocksOccupiedAboveLocation(location, treePart):
	x = int(round(location.x))
	y = int(round(location.y))
	z = int(round(location.z))
	result = 0
	zAbove = min(SIZE_OF_SPACE_XY-1, z + 1)
	while zAbove <= SIZE_OF_SPACE_XY-1:
		locationAbove = Point3D(x, y, zAbove)
		if space.has_key(locationAbove) and space[locationAbove] and not (space[locationAbove][0] is treePart):
			result += 1
		zAbove += 1
	return result

def waterOrMineralsInRegion(waterOrMinerals, location, radius):
	x = int(round(location.x))
	y = int(round(location.y))
	z = int(round(location.z))
	startX, startY, startZ = boundXYZ(x-radius, y-radius, z-radius, aboveGround=False)
	stopX, stopY, stopZ = boundXYZ(x+radius, y+radius, z+radius, aboveGround=False)
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

def seekBetterLocation(location, root, seekRadius):
	x = int(round(location.x))
	y = int(round(location.y))
	z = int(round(location.z))
	startX, startY, startZ = boundXYZ(x-seekRadius, y-seekRadius, z-seekRadius, root)
	stopX, stopY, stopZ = boundXYZ(x+seekRadius, y+seekRadius, z+seekRadius, root)
	bestLocation = None
	if root:
		if water.has_key((x,y,z)) and minerals.has_key((x,y,z)):
			bestWaterAndMinerals = water[(x,y,z)] + minerals[(x,y,z)]
		else:
			bestWaterAndMinerals = 0
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
		bestSun = sun[(x, y)]
		for i in range(startX, stopX):
			for j in range(startY, stopY):
				sunHere = sun[(i,j)]
				if sunHere > bestSun:
					bestSun = sunHere
					bestLocation = Point3D(i,j,z)
	if bestLocation:
		return bestLocation
	else:
		return location
	
def colorForLocation(location):
	if space.has_key(location):
		if space.has_key(location) and space[location]:
			treePart = space[location][0]
			if treePart:
				if COLOR_MAP == "parts":
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
				elif COLOR_MAP == "water":
					proportion = max(0.0, min(1.0, treePart.water / 20.0))
					return blues(proportion)
				elif COLOR_MAP == "minerals":
					proportion = max(0.0, min(1.0, treePart.minerals / 20.0))
					print proportion
					return copper(proportion)
				elif COLOR_MAP == "biomass":
					proportion = max(0.0, min(1.0, treePart.biomass / 50.0))
					return heatmap(proportion)
				elif COLOR_MAP == "photosynthate":
					name = treePart.__class__.__name__
					if name == "LeafCluster":
						proportion = max(0.0, min(1.0, treePart.newBiomass / 20.0))
						return greens(proportion)
					else:
						return greens(0.0)
	return None

# -------------------------------------------------------------------------------------------
# Graphing 3d space using scatter plot.

# This method can optionally draw all of the sun, water and mineral distributions as well,
# so you can see where the plant puts its roots. However since it is a stand-in for the 
# drawing of the blocky world it could be discarded.
# -------------------------------------------------------------------------------------------

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
		# the sorted method looks much better, but is far slower
		# so I turn it off when I want speed
		sortByDimension = True
		if not sortByDimension:
			for key in space:
				color = colorForLocation(key)
				if color:
					xValues.append(key.x)
					yValues.append(key.y)
					zValues.append(key.z)
					colors.append(color)
		else:
			for k in range (SIZE_OF_SPACE_Z): # order by height
				for i in range(SIZE_OF_SPACE_XY):
					for j in range(SIZE_OF_SPACE_XY):
						location = Point3D(i,j,k)
						if space.has_key(location):
							color = colorForLocation(location)
							if color:
								xValues.append(i)
								yValues.append(j)
								zValues.append(k)
								colors.append(color)
		allXValues.extend(xValues)
		allYValues.extend(yValues)
		allZValues.extend(zValues)
		allColors.extend(colors)
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

# -------------------------------------------------------------------------------------------
# Graphing 3d space using scatter plot.

# To have a way to draw trees without integrating the code with Terasology, I just 
# called on a 3D scattergraph method in matplotlib, which I use for other things.
# It is a poor rendering of the 3D space as I have used it, outputting to PNG files only.
# I think you can mix matplotlib with something (Tk?) to get an interactive view
# you can spin around, but I didn't have time for that. 
# In any case, you won't need this.
# -------------------------------------------------------------------------------------------

def cleanTextForFileName(fileName):
	result = fileName.replace("" + os.sep, " ").replace(":", " ").replace(".", " ").replace("\n", " ")
	result = result.replace("  ", " ")
	return result

def graphPNG3DScatter(xValues, yValues, zValues, colors, SIZE_OF_SPACE_XY, xAxisName, yAxisName, zAxisName, graphName, pngFileName, pngFilePath, drawLines=True):
	
	#print xValues, yValues, zValues
	
	npArrayX = np.array(xValues)
	npArrayY = np.array(yValues)
	npArrayZ = np.array(zValues)
	
	plt.clf()
	figure = plt.figure(figsize=(6,6.5))
	axes = axes3d.Axes3D(figure)
	
	# set limits
	lowest = 0 
	highest = SIZE_OF_SPACE_XY
	# for some reason you need both xlim and xlim3d, for x and y (not for z)
	axes.set_xlim(lowest, highest)
	axes.set_xlim3d(lowest, highest)
	axes.set_ylim(lowest, highest)
	axes.set_ylim3d(lowest, highest)
	axes.set_zlim3d(lowest, highest*3) 
	axes.view_init(20, 120)
	
	#plt.axvline(0, color='r', linewidth=2)
	#axes.bar([100], [100], [GROUND_LEVEL+1], zdir='z', color='b', alpha=0.8)
	
	if drawLines:
		lineWidth = 0.75
	else:
		lineWidth = 0
	
	try:
		axes.scatter(npArrayX, npArrayY, npArrayZ, c=colors, marker='s', s=10, alpha=1.0, linewidth=lineWidth)
		
		axes.grid(False)
		#axes.set_xlabel(xAxisName, fontsize=8)
		#axes.set_ylabel(yAxisName, fontsize=8)
		#plt.suptitle(graphName)
		if COLOR_MAP != "parts":
			bottomNote = "%s, showing %s" % (SPECIES, COLOR_MAP)
		else:
			bottomNote = SPECIES
		axes.text2D(0.5, 0.01, 
				bottomNote, 
				horizontalalignment='center', transform=figure.transFigure)
	
		
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


