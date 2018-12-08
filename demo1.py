from browser import document
import brySVG as SVG

canvas = SVG.CanvasObject("98vw", "90vh", "cyan")
document["demo1"] <= canvas
canvas.setDimensions()

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
        
for i in range(10):
    for j in range(6):
        tile = tiles[(i+j)%6].cloneNode(True)
        canvas <= tile
        canvas.rotateElement(tile, 45*(i*6+j))
        canvas.translateElement(tile, (i*100, j*100))
canvas.fitContents()
