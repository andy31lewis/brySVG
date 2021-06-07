from browser import document
import brySVG.transformcanvas as SVG

canvas = SVG.CanvasObject("95vw", "100%", "cyan")
document["demo3"] <= canvas
canvas.mouseMode = SVG.MouseMode.TRANSFORM

tiles = [SVG.ClosedBezierObject([((-100,50), (50,100), (200,50)), ((-100,50), (50,0), (200,50))]),
        SVG.GroupObject([SVG.PolygonObject([(50,25), (0,50), (50,75), (100,50)]),
                         SVG.SmoothBezierObject([(100,0), (4,40), (4,60), (100,100)])]),
        SVG.EllipseObject([(25,0), (75,100)], angle=30, fillcolour="none"),
        SVG.GroupObject([SVG.SectorObject((50,50), 50, 90, -45),
                         SVG.BezierObject([(None, (0,100), (50,25)), ((50,25), (100,100), None)])]),
        SVG.RectangleObject([(40,0), (50,90)], angle=20, fillcolour="none"),
        SVG.GroupObject([SVG.SmoothClosedBezierObject([(50,5), (5,80), (95,80)]),
                         SVG.PolylineObject([(0,0), (30,50), (70,50), (100,0)])])
        ]

for i, tile in enumerate(tiles):
    canvas.addObject(tile)
    tile.translate((i*100, i*100))
canvas.fitContents()
canvas.mouseMode = SVG.MouseMode.TRANSFORM
