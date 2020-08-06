pixelPerFoot = 10
footPerMeter = 3.28

frontWall = 3.05
backWall = -10.7
sideWall1 = 1.23
sideWall2 = 11.22

roomWidthMeters = 12.45
roomHeightMeters = 13.75

frontTable = (3.6, -4)
viewpointTable = (3.6, -7)
acrossTable = (7.6, -7)
perpendicularTable = (5.6, -10)

frontGoal = (4.3, -4.3)
viewGoal = (4.3, -7.3)
acrossGoal = (6.9, -7.3)
perpGoal = (5.6, -9.3)

startLoc = (6.46, 2.37)
insideStartLoc = (7.4, 2.37)

viewpointA = (3.51, -6.37)
viewpointB = (3.49, -7.71)

def pixelToMeter(pixels):
    return pixels / (pixelPerFoot * footPerMeter)

def meterToPixels(meters):
    return meters * footPerMeter * pixelPerFoot 

def pixelToFeet(pixels):
    return pixels * pixelPerFoot

def feetToPixel(feet):
    return feet * pixelPerFoot

def feetToMeter(feet):
    return feet / footPerMeter

def meterToFeet(meters):
    return meters* footPerMeter

def distanceFromWalls(table):
    fromFront = frontWall - table[1] 
    fromBack = - (backWall - table[1] )
    fromSide1 = table[0] - sideWall1
    fromSide2 = sideWall2 - table[0]
    return((fromFront,fromBack,fromSide1,fromSide2))


frontDistancesMeters = distanceFromWalls(frontTable)
viewpointDistancesMeters= distanceFromWalls(viewpointTable)
acrossDistancesMeters = distanceFromWalls(acrossTable)
perpendicularDistancesMeters = distanceFromWalls(perpendicularTable)

frontGoalDistancesMeters = distanceFromWalls(frontGoal)
viewGoalDistancesMeters= distanceFromWalls(viewGoal)
acrossGoalDistancesMeters = distanceFromWalls(acrossGoal)
perpGoalDistancesMeters = distanceFromWalls(perpGoal)

startDistancesMeters = distanceFromWalls(startLoc)
insideStartDistancesMeters = distanceFromWalls(insideStartLoc)

viewADistM = distanceFromWalls(viewpointA)
viewBDistM = distanceFromWalls(viewpointB)


#For the room in pixels, it is a 451 x 408.36 pixel rectangle
roomWidthPixels = meterToPixels(roomWidthMeters)
roomHeightPixels = meterToPixels(roomHeightMeters)

#if the bottom left corner is (0,0), we can calculate the centers of the tables and the goal loacations as such:
#front
frontXCor = meterToPixels(frontDistancesMeters[0]) #from front measurement
frontYCor = meterToPixels(frontDistancesMeters[2]) #from side1 measurement
frontTableCoordinatesPixels = (frontXCor, frontYCor)

frontGoalXCor = meterToPixels(frontGoalDistancesMeters[0]) #from front measurement
frontGoalYCor = meterToPixels(frontGoalDistancesMeters[2]) #from side1 measurement
frontGoalCoordinatesPixels = (frontGoalXCor, frontGoalYCor)

#viewpoint
viewXCor = meterToPixels(viewpointDistancesMeters[0]) #from front measurement
viewYCor = meterToPixels(viewpointDistancesMeters[2]) #from side1 measurement
viewTableCoordinatesPixels = (viewXCor, viewYCor)

viewGoalXCor = meterToPixels(viewGoalDistancesMeters[0]) #from front measurement
viewGoalYCor = meterToPixels(viewGoalDistancesMeters[2]) #from side1 measurement
viewGoalCoordinatesPixels = (viewGoalXCor, viewGoalYCor)

#across
acrossXCor = meterToPixels(acrossDistancesMeters[0]) #from front measurement
acrossYCor = meterToPixels(acrossDistancesMeters[2]) #from side1 measurement
acrossTableCoordinatesPixels = (acrossXCor, acrossYCor)

acrossGoalXCor = meterToPixels(acrossGoalDistancesMeters[0]) #from front measurement
acrossGoalYCor = meterToPixels(acrossGoalDistancesMeters[2]) #from side1 measurement
acrossGoalCoordinatesPixels = (acrossGoalXCor, acrossGoalYCor)

#perpendicular
perpXCor = meterToPixels(perpendicularDistancesMeters[0]) #from front measurement
perpYCor = meterToPixels(perpendicularDistancesMeters[2]) #from side1 measurement
perpTableCoordinatesPixels = (perpXCor, perpYCor)

perpGoalXCor = meterToPixels(perpGoalDistancesMeters[0]) #from front measurement
perpGoalYCor = meterToPixels(perpGoalDistancesMeters[2]) #from side1 measurement
perpGoalCoordinatesPixels = (perpGoalXCor, perpGoalYCor)

#start locations
startXCor = meterToPixels(startDistancesMeters[0]) #from front measurement
startYCor = meterToPixels(startDistancesMeters[2]) #from side1 measurement
startCoordinatesPixels = (startXCor, startYCor)

insideStartXCor = meterToPixels(insideStartDistancesMeters[0]) #from front measurement
insideStartGoalYCor = meterToPixels(insideStartDistancesMeters[2]) #from side1 measurement
insideStartCoordinatesPixels = (insideStartXCor, insideStartGoalYCor)

#camera/viewpoint locations
viewAXCor = meterToPixels(viewADistM[0]) #from front measurement
viewAYCor = meterToPixels(viewADistM[2]) #from side1 measurement
viewACoordinatesPixels = (viewAXCor, viewAYCor)

viewBXCor = meterToPixels(viewBDistM[0]) #from front measurement
viewBYCor = meterToPixels(viewBDistM[2]) #from side1 measurement
viewBCoordinatesPixels = (viewBXCor, viewBYCor)


print("===========ROOM MEASUREMENTS - PIXELS============ \n *note: the front wall and back walls are the width measurement. the side walls are the height measurement")
print("pixel width", roomWidthPixels)
print("pixel height", roomHeightPixels)
print("===========START COORDINATES - PIXELS============ \n *note: where the server should start. If you want the server to always start inside the kitchen before emerging, start at the insideStartCoordinates, move to the startCoordinates, and then follow the path. Otherwise, just start at the startCoordinates")
print("start coordinates", startCoordinatesPixels)
print("inside start coordinates", insideStartCoordinatesPixels)


print("============TABLE COORDINATES - PIXELS =========== \n *note: this is the case when the room is a 451 pixel x 408.36 pixel rectangle and (0,0) is the bottom left coordinate and (451,408.36) is the top right coordinate")
print("Front table pixel coordinates:", frontTableCoordinatesPixels)
print("Viewpoint table pixel coordinates:", viewTableCoordinatesPixels)
print("Across table pixel coordinates:", acrossTableCoordinatesPixels)
print("Perpendicular table pixel coordinates:", perpTableCoordinatesPixels)

print("============GOAL COORDINATES - PIXELS =========== \n *note: these are the locations where the server should go")
print("Front table goal pixel coordinates:", frontGoalCoordinatesPixels)
print("Viewpoint table goal pixel coordinates:", viewGoalCoordinatesPixels)
print("Across table goal pixel coordinates:", acrossGoalCoordinatesPixels)
print("Perpendicular table goal pixel coordinates:", perpGoalCoordinatesPixels)

print("============CAMERA/VIEWPOINT COORDINATES - PIXELS =========== \n *note: these are just their locations, should also take into account that they are rotated 35º towards the middle of the restaraunt")
print("viewpointA camera coordinates", viewACoordinatesPixels)
print("viewpointB camera coordinates", viewBCoordinatesPixels)

