from browser import document
import brySVG as SVG
from itertools import cycle

def onRightClick(event):
    event.preventDefault()
    canvas.setMouseTransformType(next(transformcycle))

canvas = SVG.CanvasObject("98vw", "90vh", "cyan")
document["demo2"] <= canvas
canvas.MouseMode = SVG.MouseMode.TRANSFORM
canvas.bind("contextmenu", onRightClick)
transformcycle = cycle(SVG.TransformType)

tiles = [SVG.ClosedBezierObject([((-100,50), (50,100), (200,50)), ((-100,50), (50,0), (200,50))]),
        SVG.GroupObject([SVG.PolygonObject([(50,25), (0,50), (50,75), (100,50)]),
                         SVG.SmoothBezierObject([(100,0), (4,40), (4,60), (100,100)])]),
        SVG.EllipseObject([(25,0), (75,100)], 30),
        SVG.GroupObject([SVG.CircleObject((50,50), 50),
                         SVG.BezierObject([(None, (0,100), (50,25)), ((50,25), (100,100), None)])]),
        SVG.RectangleObject([(40,0), (50,90)], 20),
        SVG.GroupObject([SVG.SmoothClosedBezierObject([(50,5), (5,80), (95,80)]),
                         SVG.PolylineObject([(0,0), (30,50), (70,50), (100,0)])])
        ]

for i, tile in enumerate(tiles):
    canvas.AddObject(tile)
    tile.translate((i*100, i*100))
canvas.fitContents()
canvas.setMouseTransformType(next(transformcycle))
