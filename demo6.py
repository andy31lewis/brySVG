from browser import document
import brySVG as SVG
from time import time

canvas = SVG.CanvasObject("98vw", "95vh", "cyan")
document <= canvas
canvas.MouseMode = SVG.MouseMode.EDIT

points = [SVG.PointObject((50,10*y)) for y in range(1,8)]
lines = [SVG.LineObject([(x,0), (x,100)], linewidth=5) for x in [25, 50, 75]]
rectangle = SVG.RectangleObject([(25,0), (75,100)])
rectangle.rotate(20, (50, 50))
tiles = [SVG.GroupObject([SVG.EllipseObject([(25,0), (75,100)]), SVG.PolylineObject([(0,0), (30,50), (70,50), (100,0)])]),
        SVG.GroupObject([SVG.PolygonObject([(50,25), (0,50), (50,75), (100,50)], fillcolour="lightgreen"), *lines]),
        SVG.ClosedBezierObject([((-100,50), (50,100), (200,50)), ((-100,50), (50,0), (200,50))]),
        SVG.GroupObject([SVG.CircleObject((50,50), 50), SVG.BezierObject([(None, (0,100), (50,25)), ((50,25), (100,100), None)], linewidth=5)]),
        SVG.GroupObject([rectangle, SVG.SmoothBezierObject([(100,0), (4,40), (4,60), (100,100)], linewidth=5)]),
        SVG.GroupObject([SVG.SmoothClosedBezierObject([(50,5), (5,80), (95,80)]), *points])
        ]
        
t = time()        
for i, tile in enumerate(tiles):
    canvas.AddObject(tile)
    tile.translate((i*100, i*100))
canvas.fitContents()
print (time()-t)
