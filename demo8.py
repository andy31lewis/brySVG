from browser import document
import time
tt = time.time()
import transformcanvas as SVG
from polygontesting import *
print(time.time()-tt)

def onDoubleClick(event):
    event.preventDefault()
    if canvas.selectedObject and canvas.selectedObject.id != "fixed":
        canvas.selectedObject.rotate(90)
        result = relativeposition(canvas.selectedObject, fixedshape)
        canvas.selectedObject.style.fill = colours[result]

def checkposition(event):
    event.preventDefault()
    if (event.type == "mouseup" and event.button > 1) or not canvas.selectedObject: return
    tt = time.time()
    result = relativeposition(canvas.selectedObject, fixedshape)
    print("position", time.time()-tt)
    canvas.selectedObject.style.fill = colours[result]

fixedshape = SVG.PolygonObject([(0,20), (40,60), (60,30), (80,60), (100,20), (110,40), (140,40), (120,60), (140,75), (120,90), (140,105), (120,120), (0,120)], fillcolour="white")
shapes = ([(190,30), (240,60), (260,40), (280,60), (290,30), (300,60), (330,60), (320,87.5), (330,95), (330,140), (190,140)],
        [(220,160), (240,180),(255,160), (270,180), (280,180), (290,170), (290,230), (270,230), (220,180)],
        [(110,150), (100,130), (80,170), (60,140), (40,170), (0,130), (0,230), (120,230), (140,215), (120,200), (140,185), (120,170), (140,150)])
colours = ["orange", "green", "pink", "blue", "yellow"]

canvas = SVG.CanvasObject("98vw", "90vh", "oldlace")
document["demo8"] <= canvas
canvas.setMouseTransformType(SVG.TransformType.TRANSLATE)
canvas.snap = 7
canvas.bind("mouseup", checkposition)
canvas.bind("touchend", checkposition)
canvas.bind("dblclick", onDoubleClick)

canvas.addObject(fixedshape, objid="fixed", fixed=True)
for points in shapes:
    shape = SVG.PolygonObject(points)
    shape.style.fillOpacity = 0.8
    canvas.addObject(shape)
canvas.fitContents()
