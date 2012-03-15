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

import os, math
import numpy as np
from math import sqrt, atan, sin, cos, pi

# -------------------------------------------------------------------------------------------
# Movement and rotation in space.

# This is actually some code from our original 3D turtle we used in our plant simulator
# more than a decade ago. It is probably very inefficient, and there may be many better ways
# to calculate movement in 3D space using vectors by now. But this does work.
# -------------------------------------------------------------------------------------------

class Point3D:
	def __init__(self, x=0.0, y=0.0, z=0.0):
		self.x = x
		self.y = y
		self.z = z
		
	def __str__(self):
		return "Point3D (%s, %s, %s)" % (self.x, self.y, self.z)
	
	def __eq__(self, other):
		return self.x == other.x and self.y == other.y and self.z == other.z
	
	def __hash__(self):
		return hash((self.x, self.y, self.z))
	
	def rounded(self):
		return Point3D(int(round(self.x)), int(round(self.y)), int(round(self.z)))
	
	def makeCopy(self):
		return Point3D(self.x, self.y, self.z)
	
class Matrix3D:
	def __init__(self, x, y, z):
		self.a0 = 0.0
		self.a1 = 0.0
		self.a2 = 0.0
		self.b0 = 0.0
		self.b1 = 0.0
		self.b2 = 0.0
		self.c0 = 0.0
		self.c1 = 0.0
		self.c2 = 0.0
		self.location = Point3D(x, y, z)
		
	def __repr__(self):
		return "Matrix3D: (%f %f %f) (%f %f %f) (%f %f %f)" %(self.a0, self.a1, self.a2, self.b0, self.b1, self.b2, self.c0, self.c1, self.c2)
	
	def initializeAsUnitMatrix(self):
		self.a0 = 1.0
		self.a1 = 0.0
		self.a2 = 0.0
		self.b0 = 0.0
		self.b1 = 1.0
		self.b2 = 0.0
		self.c0 = 0.0
		self.c1 = 0.0
		self.c2 = 1.0
		self.location.x = 0.0
		self.location.y = 0.0
		self.location.z = 0.0
		
	def setLocation(self, x, y, z):
		self.location.x = x
		self.location.y = y
		self.location.z = z
	
	def makeCopy(self):
		result = Matrix3D(self.location.x, self.location.y, self.location.z)
		result.a0 = self.a0
		result.a1 = self.a1
		result.a2 = self.a2
		result.b0 = self.b0
		result.b1 = self.b1
		result.b2 = self.b2
		result.c0 = self.c0
		result.c1 = self.c1
		result.c2 = self.c2
		return result
	
	def move(self, distance):
		# movement is along x axis (d, 0, 0, 1)
		self.location.x = self.location.x + distance * self.a0
		self.location.y = self.location.y + distance * self.b0
		self.location.z = self.location.z + distance * self.c0
	
	def calculateMove(self, distance):
		x = self.location.x + distance * self.a0
		y = self.location.y + distance * self.b0
		z = self.location.z + distance * self.c0
		return Point3D(x,y,z)
	
	def convertAngleFromDegreesToRadians(self, angle_degrees):
		return 2.0 * pi * angle_degrees / 360.0
	
	def rotateX(self, angle_degrees):
		angle_radians = self.convertAngleFromDegreesToRadians(angle_degrees)
		cosAngle = cos(angle_radians)
		sinAngle = sin(angle_radians)
		self.a0 = self.a0
		temp1 = (self.a1 * cosAngle) - (self.a2 * sinAngle)
		self.a2 = (self.a1 * sinAngle) + (self.a2 * cosAngle)
		self.a1 = temp1
		self.b0 = self.b0
		temp1 = (self.b1 * cosAngle) - (self.b2 * sinAngle)
		self.b2 = (self.b1 * sinAngle) + (self.b2 * cosAngle)
		self.b1 = temp1
		self.c0 = self.c0
		temp1 = (self.c1 * cosAngle) - (self.c2 * sinAngle)
		self.c2 = (self.c1 * sinAngle) + (self.c2 * cosAngle)
		self.c1 = temp1
	
	def rotateY(self, angle_degrees):
		angle_radians = self.convertAngleFromDegreesToRadians(angle_degrees)
		cosAngle = cos(angle_radians)
		sinAngle = sin(angle_radians)
		temp0 = (self.a0 * cosAngle) + (self.a2 * sinAngle)
		self.a1 = self.a1
		self.a2 = (self.a2 * cosAngle) - (self.a0 * sinAngle)
		self.a0 = temp0
		temp0 = (self.b0 * cosAngle) + (self.b2 * sinAngle)
		self.b1 = self.b1
		self.b2 = (self.b2 * cosAngle) - (self.b0 * sinAngle)
		self.b0 = temp0
		temp0 = (self.c0 * cosAngle) + (self.c2 * sinAngle)
		self.c1 = self.c1
		self.c2 = (self.c2 * cosAngle) - (self.c0 * sinAngle)
		self.c0 = temp0
	
	def rotateZ(self, angle_degrees):
		angle_radians = self.convertAngleFromDegreesToRadians(angle_degrees)
		cosAngle = cos(angle_radians)
		sinAngle = sin(angle_radians)
		temp0 = (self.a0 * cosAngle) - (self.a1 * sinAngle)
		self.a1 = (self.a0 * sinAngle) + (self.a1 * cosAngle)
		self.a2 = self.a2
		self.a0 = temp0
		temp0 = (self.b0 * cosAngle) - (self.b1 * sinAngle)
		self.b1 = (self.b0 * sinAngle) + (self.b1 * cosAngle)
		self.b2 = self.b2
		self.b0 = temp0
		temp0 = (self.c0 * cosAngle) - (self.c1 * sinAngle)
		self.c1 = (self.c0 * sinAngle) + (self.c1 * cosAngle)
		self.c2 = self.c2
		self.c0 = temp0

# This method brute-forces a line through voxels.
# To interpolate between voxels, two locations are added:
# the voxel with all values truncated, and the voxel with all values rounded.
# This makes it nearly impossible to get perfectly one-width lines, but
# it is necessary when lines are to be set at arbitrary angles.
def locationsBetweenTwoPoints(firstLocation, secondLocation, length, lineMethod="solid"):
	locations = []
	intLength = int(round(length))
	for i in range(intLength):
		proportion = i / length
		x = firstLocation.x + proportion * (secondLocation.x - firstLocation.x)
		y = firstLocation.y + proportion * (secondLocation.y - firstLocation.y)
		z = firstLocation.z + proportion * (secondLocation.z - firstLocation.z)
		if lineMethod == "spiral":
			remainder = i % 3
			if remainder == 0:
				x += 1.0
			elif remainder == 1:
				y += 1.0
			elif remainder == 2:
				z += 1.0
			locations.append(Point3D(x,y,z))
		elif lineMethod == "sparse":
			locations.append(Point3D(x,y,z))
		elif lineMethod == "solid":
			floorPoint = Point3D(math.floor(x), math.floor(y), math.floor(z))
			ceilingPoint = Point3D(math.ceil(x), math.ceil(y), math.ceil(z))
			locations.append(floorPoint)
			locations.append(ceilingPoint)
		else:
			raise Exception.create("Unrecognized internode line drawing method: %s" % lineMethod)
	locations.append(secondLocation) 
	return locations

# This method brute-forces a series of lines around a central spine to create either a 3D shape
# for a leaf/flower/fruit cluster, or a cylinder (hollow or solid) for a stem.
# Sadly, this method seems to bog things down horribly (by a factor of ten or more) 
# in terms of performance when stems are thick.
# Probably there are better solutions ...
def locationsForShapeAroundSpine(spine, pattern, numSides, sizeProportion, hollow, matrix):
	wings = []
	lengthIndex = 0
	turnMatrix = matrix.makeCopy()
	turnMatrix.rotateZ(90)
	turnDegrees = 360.0 / numSides
	for location in spine:
		shapeLookupIndex = lengthIndex % len(pattern)
		sideExtent = int(pattern[shapeLookupIndex])
		sideExtentConsideringProportion = max(0, min(sideExtent, int(round(sizeProportion * sideExtent))))
		turnMatrix.setLocation(location.x, location.y, location.z)
		for sideNumber in range(numSides):
			turnMatrix.rotateY(turnDegrees)
			sideEndLocation = turnMatrix.calculateMove(sideExtentConsideringProportion)
			if hollow:
				wings.append(sideEndLocation)
			else:
				oneSidePiece = locationsBetweenTwoPoints(location, sideEndLocation, sideExtentConsideringProportion)
				wings.extend(oneSidePiece)	
		lengthIndex += 1
	return wings

# for testing the 3D movement/rotation matrix
def testGraphics():
	m = Matrix3D(0.0, 0.0, 0.0)
	m.initializeAsUnitMatrix()
	
	print "initial", m.location
	m.move(1.0)
	print "after move 1.0", m.location
	m.move(1.0)
	print "after move 1.0", m.location
	
	#m.rotateY(10)
	#m.move(1.0)
	#print "after rotateY 90 move 1.0", m.location
	
	m.rotateZ(0)
	m.move(1.0)
	print "after rotateZ 180 move 1.0", m.location

	
def main():
	testGraphics()
	
if __name__ == "__main__":
	main()
