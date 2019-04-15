from browser import document
import drawcanvas as SVG

def onButtonClick(event):
    event.stopPropagation()
    canvas.mouseMode = SVG.MouseMode.DRAW
    canvas.tool = event.currentTarget.id
    for button in buttons.values(): button.setBackgroundColour("pink")
    buttons[event.currentTarget.id].setBackgroundColour("lime")
    canvas.style.cursor = "url(cursors/draw{}.png), auto".format(canvas.tool)

def onDoubleClick(event):
    for button in buttons.values(): button.setBackgroundColour("pink")
    buttons["select"].setBackgroundColour("lime")
    canvas.style.cursor = "auto"

canvas = SVG.CanvasObject("98vw", "90vh", "cyan", objid="canvas")
document["demo5"] <= canvas
width, height = canvas.setDimensions()
canvas.mouseMode = SVG.MouseMode.DRAW
canvas.bind("dblclick", onDoubleClick)
icons = {
"select": SVG.PolygonObject([(-20,-20), (20,-5), (5,0), (25,20), (20,25), (0,5), (-5,20)], linewidth=3, fillcolour=None),
"polyline": SVG.PolylineObject([(-25,0), (0,-25), (12,25)], linewidth=3),
"polygon": SVG.PolygonObject([(-25,0), (0,-25), (12,25)], linewidth=3),
"rectangle": SVG.RectangleObject([(-50,-25), (50,25)], linewidth=5),
"ellipse": SVG.EllipseObject([(-50,-25), (50,25)], linewidth=5),
"circle": SVG.CircleObject((0,0), 25, linewidth=3),
"bezier": SVG.BezierObject([(None,(-25,0),(0,-12)), ((0,-12),(0,-25),(25,-25)), ((25,0),(12,25),None)], linewidth=3),
"closedbezier": SVG.ClosedBezierObject([((-12,12),(-25,0),(0,-12)), ((0,-12),(0,-25),(25,-25)), ((25,0),(12,25),(-12,12))], linewidth=3),
"smoothbezier": SVG.SmoothBezierObject([(-25,0), (0,-25), (12,25)], linewidth=3),
"smoothclosedbezier": SVG.SmoothClosedBezierObject([(-25,0), (0,-25), (12,25)], linewidth=3)
}
icons["select"].style.strokeLinejoin = "round"
iconsize = height/10-10
buttons = {tool: SVG.ImageButton((10,5+i*(iconsize+10)), (iconsize, iconsize), icons[tool], onButtonClick, fillcolour="pink", canvas=canvas, objid=tool) for i, tool in enumerate(icons)}
for button in buttons.values():
    canvas.addObject(button)
