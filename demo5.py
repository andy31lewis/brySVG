from browser import document
import brySVG as SVG
from itertools import cycle

def onRightClick(event):
    event.preventDefault()
    canvas.Tool = next(toolcycle)
    canvas.style.cursor = "url(brySVG/draw{}.png), auto".format(canvas.Tool)

toollist = ["polygon", "polyline", "rectangle", "ellipse", "circle", "bezier", "closedbezier"]
toolcycle = cycle(toollist)
canvas = SVG.CanvasObject("98vw", "90vh", "cyan")
document["demo5"] <= canvas
canvas.MouseMode = SVG.MouseMode.DRAW
canvas.Tool = next(toolcycle)
canvas.style.cursor = "url(brySVG/draw{}.png), auto".format(canvas.Tool)
canvas.bind("contextmenu", onRightClick)

