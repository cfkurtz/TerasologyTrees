from math import sqrt, atan, sin, cos, pi

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

def Point3D_setXYZ(thePoint, aX, aY, aZ):
	thePoint.x = aX
	thePoint.y = aY
	thePoint.z = aZ

def Point3D_addXYZ(thePoint, xOffset, yOffset, zOffset):
	thePoint.x = thePoint.x + xOffset
	thePoint.y = thePoint.y + yOffset
	thePoint.z = thePoint.z + zOffset

def Point3D_scaleBy(thePoint, aScale):
	thePoint.x = thePoint.x * aScale
	thePoint.y = thePoint.y * aScale
	thePoint.z = thePoint.z * aScale

def Point3D_subtract(thePoint, aPoint):
	thePoint.x = thePoint.x - aPoint.x
	thePoint.y = thePoint.y - aPoint.y
	thePoint.z = thePoint.z - aPoint.z

def Point3D_matchXYZ(pointOne, pointTwo, matchDistance):
	result = (abs(pointOne.x - pointTwo.x) <= matchDistance) and (abs(pointOne.y - pointTwo.y) <= matchDistance) and (abs(pointOne.z - pointTwo.z) <= matchDistance)
	return result

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
	
