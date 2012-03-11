from math import sqrt, atan, sin, cos, pi

# ---------------------------------------------------------------------------------- KfPoint3D 
class Point3D:
	def __init__(self, x=0.0, y=0.0, z=0.0):
		self.x = x
		self.y = y
		self.z = z
		
	def __str__(self):
		return "Point3D(%s, %s, %s)" % (self.x, self.y, self.z)

def Point3D_setXYZ(thePoint, aX, aY, aZ):
	thePoint.x = aX
	thePoint.y = aY
	thePoint.z = aZ

def Point3D_addXYZ(thePoint, xOffset, yOffset, zOffset):
	#pdf - shift point by x y and z.
	thePoint.x = thePoint.x + xOffset
	thePoint.y = thePoint.y + yOffset
	thePoint.z = thePoint.z + zOffset

def Point3D_scaleBy(thePoint, aScale):
	#pdf - multiply point by scale.
	thePoint.x = thePoint.x * aScale
	thePoint.y = thePoint.y * aScale
	thePoint.z = thePoint.z * aScale

def Point3D_subtract(thePoint, aPoint):
	#pdf - subtract point from this point.
	thePoint.x = thePoint.x - aPoint.x
	thePoint.y = thePoint.y - aPoint.y
	thePoint.z = thePoint.z - aPoint.z

def Point3D_matchXYZ(pointOne, pointTwo, matchDistance):
	result = (abs(pointOne.x - pointTwo.x) <= matchDistance) and (abs(pointOne.y - pointTwo.y) <= matchDistance) and (abs(pointOne.z - pointTwo.z) <= matchDistance)
	return result

def Point3D_addPointToBoundsRect(boundsRect, aPoint):
	x = aPoint.x
	y = aPoint.y

	if (boundsRect.Left == 0) and (boundsRect.Right == 0) and (boundsRect.Top == 0) and (boundsRect.Bottom == 0):
		# on first point entered, initialize bounds rect
		boundsRect.Left = x
		boundsRect.Right = x
		boundsRect.Top = y
		boundsRect.Bottom = y
	else:
		if x < boundsRect.Left:
			boundsRect.Left = x
		elif x > boundsRect.Right:
			boundsRect.Right = x
		if y < boundsRect.Top:
			boundsRect.Top = y
		elif y > boundsRect.Bottom:
			boundsRect.Bottom = y

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
		return "KfMatrix: (%f %f %f) (%f %f %f) (%f %f %f)" %(self.a0, self.a1, self.a2, self.b0, self.b1, self.b2, self.c0, self.c1, self.c2)
	
	# ---------------------------------------------------------------------------------- matrix initializing and copying 
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
		
	def setXYZ(self, x, y, z):
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
	
	def copyTo(self, otherMatrix):
		otherMatrix.location.x = self.location.x
		otherMatrix.location.y = self.location.y
		otherMatrix.location.z = self.location.z
		otherMatrix.a0 = self.a0
		otherMatrix.a1 = self.a1
		otherMatrix.a2 = self.a2
		otherMatrix.b0 = self.b0
		otherMatrix.b1 = self.b1
		otherMatrix.b2 = self.b2
		otherMatrix.c0 = self.c0
		otherMatrix.c1 = self.c1
		otherMatrix.c2 = self.c2
	
	# ---------------------------------------------------------------------------- matrix moving and transforming 
	def move(self, distance):
		#pdf - move a distance by multiplying matrix values
		#   movement is along x axis (d, 0, 0, 1);
		self.location.x = self.location.x + distance * self.a0
		self.location.y = self.location.y + distance * self.b0
		self.location.z = self.location.z + distance * self.c0
	
	# transform the point, including offsetting it by the current location
	#Alters the point's contents
	def transform(self, aPoint3D):
		x = aPoint3D.x
		y = aPoint3D.y
		z = aPoint3D.z
		aPoint3D.x = (x * self.a0) + (y * self.a1) + (z * self.a2) + self.location.x
		aPoint3D.y = (x * self.b0) + (y * self.b1) + (z * self.b2) + self.location.y
		aPoint3D.z = (x * self.c0) + (y * self.c1) + (z * self.c2) + self.location.z
		
	def convertAngleFromDegreesToRadians(self, angle_degrees):
		return 2.0 * pi * angle_degrees / 360.0
		
	# ---------------------------------------------------------------------------------- matrix rotating 
	def rotateX(self, angle_degrees):
		angle_radians = self.convertAngleFromDegreesToRadians(angle_degrees)
		cosAngle = cos(angle_radians)
		sinAngle = sin(angle_radians)
		#moved minuses to middle to optimize
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
		#flipped to put minus in middle
		self.a2 = (self.a2 * cosAngle) - (self.a0 * sinAngle)
		self.a0 = temp0
		temp0 = (self.b0 * cosAngle) + (self.b2 * sinAngle)
		self.b1 = self.b1
		#flipped to put minus in middle
		self.b2 = (self.b2 * cosAngle) - (self.b0 * sinAngle)
		self.b0 = temp0
		temp0 = (self.c0 * cosAngle) + (self.c2 * sinAngle)
		self.c1 = self.c1
		#flipped to put minus in middle
		self.c2 = (self.c2 * cosAngle) - (self.c0 * sinAngle)
		self.c0 = temp0
	
	def rotateZ(self, angle_degrees):
		angle_radians = self.convertAngleFromDegreesToRadians(angle_degrees)
		cosAngle = cos(angle_radians)
		sinAngle = sin(angle_radians)
		#minuses moved to middle to optimize
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
	
	def angleX_degrees(self):
		try:
			result = 0
			temp = (self.a2 * self.a2) + (self.c2 * self.c2)
			if (temp < 0.0):
				temp = 0.0
			temp = sqrt(temp)
			if (temp == 0.0):
				if (self.b2 < 0):
					result = 90
				else:
					result = 360 - 90
			else:
				temp = self.b2 / temp
				temp = atan(temp)
				result = -temp * 360 / (2 * 3.1415926)
		except:
			result = 0
		return result
	
	def angleY_degrees(self):
		try:
			result = 0
			temp = (self.a0 * self.a0) + (self.c0 * self.c0)
			if (temp < 0.0):
				temp = 0.0
			temp = sqrt(temp)
			if (temp == 0.0):
				if (self.b0 < 0):
					result = 90
				else:
					result = 360 - 90
			else:
				temp = self.b0 / temp
				temp = atan(temp)
				result = -temp * 360 / (2 * 3.1415926)
		except:
			result = 0
		return result
	
	def angleZ_degrees(self): 
		try:
			result = 0
			temp = (self.a1 * self.a1) + (self.c1 * self.c1)
			if (temp < 0.0):
				temp = 0.0
			temp = sqrt(temp)
			if (temp == 0.0):
				if (self.b1 < 0):
					result = 90
				else:
					result = 360 - 90
			else:
				temp = self.b1 / temp
				temp = atan(temp)
				result = -temp * 360 / (2 * 3.1415926)
		except:
			result = 0
		return result
	