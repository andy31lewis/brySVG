from browser import document, window
import brySVG.dragcanvas as SVG

data = [[[(0,0), (50,50), (100,0)], 0], [[(0,50), (50, 0), (50,100)], 80], [[(0,0), (0,50), (50,50)], 160],
[[(0,25), (25,0), (50,25)], 210], [[(0,0), (25, 25), (0,50)], 270], [[(25,0), (50, 25), (25, 50), (0,25)], 310],
[[(0,0), (25, 25), (75,25), (50,0)], 360]]

def onresize(event):
    canvas.fitContents()

canvas = SVG.CanvasObject("95vw", "100%", "cyan")
document["demo2"] <= canvas

for points, offset in data:
    piece = SVG.PolygonObject(points)
    canvas.addObject(piece)
    canvas.translateObject(piece, (offset, 0))

outline = SVG.PolygonObject([(180, 100), (280,100), (280,200), (180,200)], fillcolour="none")
canvas.addObject(outline, fixed=True)
canvas.fitContents()

canvas.mouseMode = SVG.MouseMode.DRAG
canvas.vertexSnap = True
window.bind("resize", onresize)

