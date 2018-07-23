from browser import document
from brySVG import SVGobjects as SVG

canvas = SVG.CanvasObject("98vw", "95vh", "cyan")
document <= canvas
poly = SVG.PolygonObject([(0,0), (100,100), (150,100), (200,150), (250,150), (400,0), (300,200), (400,300), (200,200), (150, 200), (100,250), (50,250), (0,300), (50,150)])
canvas.AddObject(poly)
points = [(20,25), (80,100), (80, 150), (50,50), (125,100), (225,150), (125,200), (175,200), (30, 250), (75,250), (300,100), (350,100)]
for point in points:
    print (point, poly.containsPoint(point))
canvas.fitContents()
