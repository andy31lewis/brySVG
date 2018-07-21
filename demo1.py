from browser import document
from brySVG import SVGobjects as SVG
from time import time

canvas = SVG.CanvasObject("98vw", "95vh", "cyan")
document <= canvas
canvas.setDimensions()

points = [SVG.PointObject((50,10*y)) for y in range(1,8)]
lines = [SVG.LineObject([(x,0), (x,100)]) for x in [25, 50, 75]]
tiles = [SVG.GroupObject([SVG.EllipseObject([(25,0), (75,100)]), SVG.PolylineObject([(0,0), (30,50), (70,50), (100,0)])]),
        SVG.GroupObject([SVG.PolygonObject([(50,25), (0,50), (50,75), (100,50)], fillcolour="lightgreen"), *lines]),
        SVG.ClosedBezierObject([((-100,50), (50,100), (200,50)), ((-100,50), (50,0), (200,50))]),
        SVG.GroupObject([SVG.CircleObject((50,50), 50), SVG.BezierObject([((0,100), (50,25)), ((50,25), (100,100))])]),
        SVG.GroupObject([SVG.RectangleObject([(25,0), (75,100)]), SVG.SmoothBezierObject([(100,0), (4,40), (4,60), (100,100)])]),
        SVG.GroupObject([SVG.SmoothClosedBezierObject([(50,5), (5,80), (95,80)]), *points])
        ]
        
t = time()        
for i in range(10):
    for j in range(6):
        tile = tiles[(i+j)%6].cloneObject()
        #tile = tiles[(i+j)%6].cloneNode(True)
        canvas.AddObject(tile)
        tile.rotate(45*(i*6+j))
        tile.translate((i*100, j*100))
        #canvas.rotate(tile, 90*(i*6+j))
        #canvas.translate(tile, (i*100, j*100))
canvas.fitContents()
print (time()-t)
