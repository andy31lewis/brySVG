from browser import document
from brySVG import SVGobjects as SVG
from time import time

def onRightClick(event):
    event.preventDefault()
    canvas.setMouseAction((canvas.MouseAction+1)%6)

canvas = SVG.CanvasObject("98vw", "95vh", "cyan")
document <= canvas
canvas.Snap = 5
canvas.RotateSnap = 0.2
canvas.bind("contextmenu", onRightClick)

tile1 = SVG.PolygonObject([(50,25), (0,50), (50,75), (100,50)])
for i in range(10):
        tile = tile1.cloneObject()
        canvas.AddObject(tile)
        tile.rotate(45*i)
        tile.translate((i*100, i*50))
canvas.fitContents()
