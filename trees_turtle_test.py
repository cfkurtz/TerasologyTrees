from trees_turtle import *

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

point1 = Point3D(1,2,3)
point2 = Point3D(4,5,6)
point3 = Point3D(1,2,3)

print 'point1 == point1', point1 == point1
print 'point1 == point2', point1 == point2
print 'point1 == point3', point1 == point3
print 'point2 == point3', point2 == point3

print 'hash(point1)', hash(point1)
print 'hash(point2)', hash(point2)
print 'hash(point3)', hash(point3)