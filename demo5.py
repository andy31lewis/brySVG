from browser import document
from brySVG import SVGobjects as SVG
from time import time

def onRightClick(event):
    event.preventDefault()
    canvas.setMouseAction(3-canvas.MouseAction)

canvas = SVG.CanvasObject("98vw", "95vh", "cyan")
document <= canvas
canvas.setMouseAction(1)
canvas.Snap = 15
canvas.RotateSnap = 30
canvas.bind("contextmenu", onRightClick)

t = time()
for n,m in [(12, 3), (8, 4), (6, 6)]:
    for i in range(n):
        poly = SVG.RegularPolygon(m, startpoint=(0, 20), sidelength=40, offsetangle=i*5)
        canvas.AddObject(poly)
        poly.translate((i*m*20, m*100))
canvas.fitContents()
print (time() - t)
