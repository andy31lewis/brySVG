from browser import document
import brySVG as SVG
from time import time

def onRightClick(event):
    event.preventDefault()
    canvas.setMouseTransformType(3-canvas.MouseTransformType)

canvas = SVG.CanvasObject("98vw", "95vh", "cyan", id="canvas1")
document <= canvas
canvas.setMouseTransformType(SVG.TransformType.TRANSLATE)
canvas.Snap = 15
canvas.RotateSnap = 20
canvas.bind("contextmenu", onRightClick)

t = time()
for n,m in [(12, 3), (8, 4), (6, 6)]:
    for i in range(n):
        poly = SVG.RegularPolygon(m, startpoint=(0, 20), sidelength=40, offsetangle=i*5)
        canvas.AddObject(poly)
        poly.translate((i*m*20, m*100))
canvas.fitContents()
print (time() - t)
