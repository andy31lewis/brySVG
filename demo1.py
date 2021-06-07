from browser import document
import brySVG.dragcanvas as SVG

canvas = SVG.CanvasObject("95vw", "100%", "cyan")
document["demo1"] <= canvas

tiles = [SVG.ClosedBezierObject([((-100,50), (50,100), (200,50)), ((-100,50), (50,0), (200,50))]),
        SVG.GroupObject([SVG.PolygonObject([(50,25), (0,50), (50,75), (100,50)]),
                         SVG.SmoothBezierObject([(100,0), (4,40), (4,60), (100,100)])]),
        SVG.EllipseObject([(25,0), (75,100)], angle=30),
        SVG.GroupObject([SVG.CircleObject((50,50), 50),
                         SVG.BezierObject([(None, (0,100), (50,25)), ((50,25), (100,100), None)])]),
        SVG.RectangleObject([(40,0), (50,90)], angle=20),
        SVG.GroupObject([SVG.SmoothClosedBezierObject([(50,5), (5,80), (95,80)]),
                         SVG.PolylineObject([(0,0), (30,50), (70,50), (100,0)])]),
        ]

for i in range(10):
    for j in range(6):
        tile = tiles[(i+j)%6].cloneNode(True)
        #tile = tiles[(i+j)%6].cloneObject() #is slower but allows MouseMode.DRAG, TRANSFORM or EDIT to be used
        canvas <= tile
        canvas.rotateElement(tile, 45*(i*6+j))
        canvas.translateElement(tile, (i*100, j*100))

canvas.fitContents()
multilinetext = "This is a\nmultiline\nTextObject\nwith anchor\nat top left\nand fontsize 16"
canvas <= SVG.TextObject(multilinetext, (1025,10), 1, fontsize=16, ignorescaling=True, canvas=canvas)
longtext = "This is a WrappingTextObject with a width of 200 SVG units, with the anchor at bottom left."
canvas <= SVG.WrappingTextObject(canvas, longtext, (1025,600), 200, 7, 16, ignorescaling=True)
canvas.fitContents()
canvas.mouseMode = SVG.MouseMode.PAN

