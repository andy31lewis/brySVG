from browser import document
import brySVG as SVG
from time import time

def onRightClick(event):
    global toolno
    event.preventDefault()
    toolno = (toolno+1)%7
    canvas.Tool = toollist[toolno]

toollist = ["polygon", "polyline", "rectangle", "ellipse", "circle", "bezier", "closedbezier"]
canvas = SVG.CanvasObject("98vw", "95vh", "cyan")
document <= canvas
canvas.MouseMode = SVG.MouseMode.DRAW
canvas.Tool = "polygon"
toolno = 0
canvas.bind("contextmenu", onRightClick)

