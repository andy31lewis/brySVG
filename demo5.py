from browser import document
import brySVG as SVG
from itertools import cycle
import time

def onRightClick(event):
    event.preventDefault()
    canvas.Tool = next(toolcycle)
    canvas.style.cursor = "url(brySVG/draw{}.png), auto".format(canvas.Tool)

"""
rotatelefticon = SVG.svg.path(d="M 0,8 a 8,8 0 1 0 -5.66,-13.66 l 0,-4 m 0,4 l 4,1", style={"stroke":"black", "strokeWidth":2, "fill":None, "strokeLinejoin":"round", "strokeLinecap":"round"})
canvas <= SVG.ImageButton((160,0), (24,24), rotatelefticon, rotateleft, fillcolour="pink")
rotaterighticon = SVG.svg.path(d="M 0,8 a 8,8 0 1 1 5.66,-13.66 l 0,-4 m 0,4 l -4,1", style={"stroke":"black", "strokeWidth":2, "fill":None, "strokeLinejoin":"round", "strokeLinecap":"round"})
canvas <= SVG.ImageButton((200,0), (24,24), rotaterighticon, rotateright, fillcolour="pink")
"""

toollist = ["polygon", "polyline", "rectangle", "ellipse", "circle", "bezier", "closedbezier"]
toolcycle = cycle(toollist)
canvas = SVG.CanvasObject("98vw", "90vh", "cyan")
document["demo5"] <= canvas
canvas.MouseMode = SVG.MouseMode.DRAW
canvas.Tool = "closedbezier"
canvas.style.cursor = "url(brySVG/draw{}.png), auto".format(canvas.Tool)
canvas.bind("contextmenu", onRightClick)
#canvas.bind("touchstart", onTouchStart)
