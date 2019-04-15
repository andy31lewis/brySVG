from browser import document
import dragcanvas as SVG

data = [[[(0,0), (50,50), (100,0)], 0], [[(0,50), (50, 0), (50,100)], 80], [[(0,0), (0,50), (50,50)], 160],
[[(0,25), (25,0), (50,25)], 210], [[(0,0), (25, 25), (0,50)], 270], [[(25,0), (50, 25), (25, 50), (0,25)], 310],
[[(0,0), (25, 25), (75,25), (50,0)], 360]]

canvas = SVG.CanvasObject("98vw", "90vh", "cyan")
document["demo2"] <= canvas
canvas.snap = 10

for points, offset in data:
    piece = SVG.PolygonObject(points)
    canvas.addObject(piece)
    canvas.translateObject(piece, (offset, 0))

canvas.addObject(SVG.PolygonObject([(180, 100), (280,100), (280,200), (180,200)], fillcolour="none"), fixed=True)
canvas.fitContents()
canvas.mouseMode = SVG.MouseMode.DRAG
