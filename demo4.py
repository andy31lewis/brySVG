from browser import document
import brySVG.polygoncanvas as SVG

canvas = SVG.CanvasObject("95vw", "100%", "cyan")
document["demo4"] <= canvas

for n,m in [(12, 3), (8, 4), (6, 6)]:
    for i in range(n):
        poly = SVG.RegularPolygon(m, startpoint=(0, 20), sidelength=60, offsetangle=i*5)
        canvas.addObject(poly)
        poly.translate((i*m*25, m*100))
canvas.fitContents()

canvas.mouseMode = SVG.MouseMode.TRANSFORM
canvas.transformTypes = [SVG.TransformType.TRANSLATE, SVG.TransformType.ROTATE]
canvas.edgeSnap = True
canvas.snapAngle = 20
canvas.vertexSnap = True
canvas.snapDistance = 15
