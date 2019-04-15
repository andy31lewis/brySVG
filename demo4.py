from browser import document
import brySVG as SVG

canvas = SVG.CanvasObject("98vw", "90vh", "cyan", id="canvas1")
document["demo4"] <= canvas
canvas.MouseMode = SVG.MouseMode.TRANSFORM
canvas.transformTypes = [SVG.TransformType.TRANSLATE, SVG.TransformType.ROTATE]
canvas.Snap = 15
canvas.RotateSnap = 20

for n,m in [(12, 3), (8, 4), (6, 6)]:
    for i in range(n):
        poly = SVG.RegularPolygon(m, startpoint=(0, 20), sidelength=40, offsetangle=i*5)
        canvas.AddObject(poly)
        poly.translate((i*m*20, m*100))
canvas.fitContents()
