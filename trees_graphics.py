# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

import os, math
import numpy as np

import matplotlib
matplotlib.use('TkAgg') # do this before importing pylab

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d

from trees_parameters import *

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
	axes.set_zlim3d(lowest, highest*2) # twice as tall 
	axes.view_init(20, 120)
	
	if drawLines:
		lineWidth = 1
	else:
		lineWidth = 0
	
	try:
		axes.scatter(npArrayX, npArrayY, npArrayZ, c=colors, marker='s', s=10, alpha=1.0, linewidth=lineWidth)

		#axes.bar([0], [GROUND_LEVEL+1], [SIZE_OF_SPACE_XY], color='b', alpha=0.5)
	
		axes.grid(True)
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
# movement and rotation in space
# -------------------------------------------------------------------------------------------

def boundLocation(location, aboveGround):
	newX = location[0]
	newY = location[1]
	newZ = location[2]
	newX = max(0, min(SIZE_OF_SPACE_XY-1, newX))
	newY = max(0, min(SIZE_OF_SPACE_XY-1, newY))
	if aboveGround:
		newZ = max(GROUND_LEVEL+1, min(SIZE_OF_SPACE_Z-1, newZ))
	else:
		newZ = max(0, min(GROUND_LEVEL + ROOTS_CAN_GROW_THIS_MANY_BLOCKS_ABOVE_GROUND, newZ))
	return (newX, newY, newZ)

def displacementInDirection(location, direction, amount, aboveGround=True):
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
	newLocation = boundLocation((newX, newY, newZ), aboveGround)
	return newLocation

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
	#print 'rotation: forward', forward, 'side', side, 'turns', turns
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

def circleAroundPoint(center, diameter, forward, side, aboveGround=True):
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
		locationBounded = boundLocation(locationConsideringBothDisplacements, aboveGround)
		if not locationBounded in locations:
			locations.append(locationBounded)
		angle += angleStep
	return locations
				
def endPointOfAngledLine(location, length, angleInDegrees, swayInDegrees, forward, parentForward, side, aboveGround=True):
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
	endLocation[forwardDimensionIndex] = int(round(location[forwardDimensionIndex] + forwardMultiplier * movementInForwardDimension))
	
	# set the value for the dimension corresponding to the parent branch's forward direction
	parentForwardDimensionIndex = xyzTupleIndexForDimensionName(parentForwardDimension)
	if parentForwardDimension.find('-') >= 0:
		parentForwardMultiplier = -1
	else:
		parentForwardMultiplier = 1
	endLocation[parentForwardDimensionIndex] = int(round(location[parentForwardDimensionIndex] + parentForwardMultiplier * movementInParentForwardDimension))
	
	# now set the one remaining value not set, keeping the value it had before
	# because the movement was in two dimensions but not in the third
	for index in range(len(endLocation)):
		if endLocation[index] == valueNotSet:
			endLocation[index] = location[index]
			
	#print 'length', length, 'start', location, 'end', endLocation
	#print '.... forwardDimension', forwardDimension, 'parentForwardDimension', parentForwardDimension
	#print '........ movementInForwardDimension', movementInForwardDimension, 'movementInParentForwardDimension', movementInParentForwardDimension

	endLocation = boundLocation(endLocation, aboveGround)
	return endLocation





