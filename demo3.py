from browser import document
from brySVG import SVGobjects as SVG

def onRightClick(event):
    event.preventDefault()
    if event.target.id == "": return
    canvas.ObjectDict[event.target.id].rotate(45)

data = [[[(0,0), (50, 50), (100,0)], 45, 0], [[(0,0), (50, 50), (100,0)], 45, 80], [[(0,-20), (50, -20), (50, 30)], 0, 160],
[[(0,0), (25, 25), (50,0)], 45, 210], [[(0,0), (25, 25), (50,0)], 45, 260], [[(25,0), (50, 25), (25, 50), (0,25)], 45, 310],
[[(0,0), (25, 25), (75,25), (50,0)], 0, 360]]

canvas = SVG.CanvasObject("98vw", "95vh", "cyan")
document <= canvas
canvas.setMouseAction(1)
canvas.Snap = 10
canvas.bind("contextmenu", onRightClick)

for points, angle, offset in data:
    piece = SVG.PolygonObject(points)
    canvas.AddObject(piece)
    piece.rotate(angle)
    piece.translate((offset, 0))
canvas.AddObject(SVG.PolygonObject([(180, 100), (280,100), (280,200), (180,200)], fillcolour=None))
canvas.fitContents()
