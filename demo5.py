from browser import document
import brySVG.drawcanvas as SVG

def onButtonClick(event):
    event.stopPropagation()
    buttonid = event.currentTarget.id
    for button in buttons.values(): button.setFillColour("pink")
    buttons[buttonid].setFillColour("lime")
    canvas.setTool(buttonid)
    cursorname = buttonid if buttonid in ("select", "insertpoint", "deletepoint") else "draw"+buttonid
    canvas.style.cursor = "url(cursors/{}.png), auto".format(cursorname)

def onDoubleClick(event):
    for button in buttons.values(): button.setFillColour("pink")
    buttons["select"].setFillColour("lime")
    canvas.style.cursor = "auto"

canvas = SVG.CanvasObject("95vw", "100%", "cyan", objid="canvas")
document["demo5"] <= canvas
canvas.bind("dblclick", onDoubleClick)

icons = {
"polyline": SVG.PolylineObject([(-25,0), (0,-25), (12,25)], linewidth=3),
"polygon": SVG.PolygonObject([(-25,0), (0,-25), (12,25)], linewidth=3),
"rectangle": SVG.RectangleObject([(-50,-25), (50,25)], linewidth=5),
"ellipse": SVG.EllipseObject([(-50,-25), (50,25)], linewidth=5),
"sector": SVG.SectorObject((-25,0), 50, 60, 120, linewidth=3),
"bezier": SVG.BezierObject([(None,(-25,0),(0,-12)), ((0,-12),(0,-25),(25,-25)), ((25,0),(12,25),None)], linewidth=3),
"closedbezier": SVG.ClosedBezierObject([((-12,12),(-25,0),(0,-12)), ((0,-12),(0,-25),(25,-25)), ((25,0),(12,25),(-12,12))], linewidth=3),
"smoothbezier": SVG.SmoothBezierObject([(-25,0), (0,-25), (12,25)], linewidth=3),
"smoothclosedbezier": SVG.SmoothClosedBezierObject([(-25,0), (0,-25), (12,25)], linewidth=3),
"select": SVG.PolygonObject([(-20,-20), (20,-5), (5,0), (25,20), (20,25), (0,5), (-5,20)], linewidth=3, fillcolour="none"),
"insertpoint": SVG.GroupObject([SVG.BezierObject([(None,(0,25),(-60,-40)), ((60,-40),(0,25),None)], linewidth=3),SVG.LineObject([(-10,-5),(10,-5)], linewidth=3), SVG.LineObject([(0,-15),(0,5)], linewidth=3)]),
"deletepoint": SVG.GroupObject([SVG.BezierObject([(None,(0,25),(-60,-40)), ((60,-40),(0,25),None)], linewidth=3),SVG.LineObject([(-10,-5),(10,-5)], linewidth=3)])
}
icons["select"].style.strokeLinejoin = "round"

n = 9
iconsize = 50
buttons = {tool: SVG.ImageButton((10+(i//n)*(iconsize+10),5+(i%n)*(iconsize+10)), (iconsize, iconsize), icons[tool], onButtonClick, fillcolour="pink", canvas=canvas, objid=tool) for i, tool in enumerate(icons)}
for button in buttons.values():
    canvas.addObject(button)
canvas.mouseMode = SVG.MouseMode.DRAW
[(x1, y1), (x2, y2)] = canvas.fitContents()
canvas.setViewBox([(0, y1), (x2-x1, y2)])
