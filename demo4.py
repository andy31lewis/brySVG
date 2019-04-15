from browser import document
import transformcanvas as SVG

poly = SVG.RegularPolygon(6, startpoint=(0, 20), sidelength=40, offsetangle=0)
canvas = SVG.CanvasObject("98vw", "90vh", "cyan")
document["demo4"] <= canvas
canvas.mouseMode = SVG.MouseMode.TRANSFORM
canvas.transformTypes = [SVG.TransformType.TRANSLATE, SVG.TransformType.ROTATE]
canvas.snap = 15
canvas.rotateSnap = 20

for n,m in [(12, 3), (8, 4), (6, 6)]:
    for i in range(n):
        poly = SVG.RegularPolygon(m, startpoint=(0, 20), sidelength=60, offsetangle=i*5)
        canvas.addObject(poly)
        poly.translate((i*m*25, m*100))
canvas.fitContents()
