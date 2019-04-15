from browser import document
import time
print("Starting")
tt = time.time()
import transformcanvas as SVG
print(time.time()-tt)

def onDoubleClick(event):
    event.preventDefault()
    if canvas.selectedObject: canvas.selectedObject.rotate(45)
    #if event.target.id: canvas.objectDict[event.target.id].rotate(45)

data = [[[(0,0), (50, 50), (100,0)], 45, 0], [[(0,0), (50, 50), (100,0)], 45, 80], [[(0,-20), (50, -20), (50, 30)], 0, 160],
[[(0,0), (25, 25), (50,0)], 45, 210], [[(0,0), (25, 25), (50,0)], 45, 260], [[(25,0), (50, 25), (25, 50), (0,25)], 45, 310],
[[(0,0), (25, 25), (75,25), (50,0)], 0, 360]]

canvas = SVG.CanvasObject("98vw", "90vh", "cyan")
document["demo3"] <= canvas
canvas.snap = 10
canvas.bind("dblclick", onDoubleClick)

for points, angle, offset in data:
    piece = SVG.PolygonObject(points)
    canvas.addObject(piece)
    #piece.rotate(angle)
    canvas.translateObject(piece, (offset, 0))

canvas.addObject(SVG.PolygonObject([(180, 100), (280,100), (280,200), (180,200)], fillcolour=None), fixed=True)
canvas.fitContents()
canvas.setMouseMode(SVG.MouseMode.DRAG)
