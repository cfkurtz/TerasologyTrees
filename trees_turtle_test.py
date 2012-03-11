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