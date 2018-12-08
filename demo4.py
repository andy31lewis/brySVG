from browser import document
import brySVG as SVG
from itertools import cycle

def onRightClick(event):
    event.preventDefault()
    canvas.setMouseTransformType(next(transformtoggle))

canvas = SVG.CanvasObject("98vw", "90vh", "cyan", id="canvas1")
document["demo4"] <= canvas
transformtoggle = cycle((SVG.TransformType.TRANSLATE, SVG.TransformType.ROTATE))
canvas.setMouseTransformType(next(transformtoggle))
canvas.Snap = 15
canvas.RotateSnap = 20
canvas.bind("contextmenu", onRightClick)

for n,m in [(12, 3), (8, 4), (6, 6)]:
    for i in range(n):
        poly = SVG.RegularPolygon(m, startpoint=(0, 20), sidelength=40, offsetangle=i*5)
        canvas.AddObject(poly)
        poly.translate((i*m*20, m*100))
canvas.fitContents()
