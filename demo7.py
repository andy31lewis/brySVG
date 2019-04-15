from browser import document
import dragcanvas as SVG
from polygontesting import *

def checkposition(event):
    event.preventDefault()
    if (event.type == "mouseup" and event.button > 1) or not canvas.selectedObject or canvas.selectedObject.fixed: return
    result = relativeposition(canvas.selectedObject, fixedshape)
    canvas.selectedObject.style.fill = colours[result]
    #print(canvas.selectedObject.pointList[0], containspoint(fixedshape, canvas.selectedObject.pointList[0]))

fixedshape = SVG.PolygonObject([(0,20), (40,60), (60,30), (80,60), (100,20), (110,40), (140,40), (120,60), (140,75), (120,90), (140,105), (120,120), (0,120)], fillcolour="white")
shapes = ([(190,30), (240,60), (260,40), (280,60), (290,30), (300,60), (330,60), (320,87.5), (330,95), (330,140), (190,140)],
        [(110,150), (100,130), (80,170), (60,140), (40,170), (0,130), (0,230), (120,230), (140,215), (120,200), (140,185), (120,170), (140,150)],
        [(180,160), (200,180), (215,160), (230,180), (240,180), (250,170), (250,230), (230,230), (180,180)],
        [(330,160), (310,180), (330,195), (310,210), (310,220), (320,230), (260,230), (260,210), (310,160)])
colours = ["orange", "green", "pink", "blue", "yellow"]

canvas = SVG.CanvasObject("98vw", "90vh", "oldlace")
document["demo7"] <= canvas
canvas.snap = 7
canvas.bind("mouseup", checkposition)
canvas.bind("touchend", checkposition)

canvas.addObject(fixedshape, objid="fixed", fixed=True)
for points in shapes:
    shape = SVG.PolygonObject(points)
    shape.style.fillOpacity = 0.8
    canvas.addObject(shape)
canvas.fitContents()
