from browser import document, html
import brywidgets as ws

class DemoPage(ws.NotebookPage):
    def update(self):
        __import__(self.id)

pages = [ws.NotebookPage("Introduction", "powderblue", id="intro")]
for i in range(1,9):
    rgb1, rgb2 = ws.hwbtorgb(60+i*180,0.5,0)[1], ws.hwbtorgb(60+i*180,0.4,0.1)[1]
    pages.append(DemoPage("Demo "+str(i), "rgb({},{},{})".format(*rgb1), id="demo"+str(i)))
    pages.append(ws.NotebookPage("Code "+str(i), "rgb({},{},{})".format(*rgb2), html.TEXTAREA(open("demo"+str(i)+".py").read()), id="code"+str(i)))
document.select("body")[0].innerHTML = ""
document <= ws.Notebook(pages)

introtext = [
html.H1("BrySVG DEMO"),
html.P("""The other tabs on this page provide a series of short demos showing the capabilities of the BrySVG module.
For each demo there is also a tab showing the code needed to create it.  A brief description of each demo follows:"""),
html.P(html.B("Demo 1")+""" - This is a non-interactive demo which illustrates how to create most of the SVG objects:"""+html.BR()+
"""CanvasObject, PolylineObject, PolygonObject, RectangleObject, EllipseObject, CircleObject,
BezierObject, ClosedBezierObject, SmoothBezierObject, SmoothClosedBezierObject"""+html.BR()+
"""It also illustrates the use of the CanvasObject methods rotateElement and translateElement.
(The same set of objects is also used in Demo2, Demo 6 and Demo 7.)"""),
html.P(html.B("Demo 2")+""" - This demonstrates MouseMode.TRANSFORM. Right-clicking on the canvas will cycle between
the values of MouseTransformType:"""+html.BR()+
"""NONE, TRANSLATE, ROTATE, XSTRETCH, YSTRETCH, ENLARGE"""+html.BR()+
"""Then by left-clicking and dragging on an object, the relevant tranformation will be carried out."""),
html.P(html.B("Demo 3")+""" - This is the famous Tangram puzzle, which demonstrates canvas.Snap.
Drag a piece onto the square. If a vertex of the piece is close to a vertex of the square, the piece will "snap"
so that the vertices match. Right-clicking on a piece will rotate it by 45°.
To complete the puzzle, fill the square completely with the pieces."""),
html.P(html.B("Demo 4")+""" - This demonstrates canvas.RotateSnap, and also how to create RegularPolygons.
Drag the polygons around, matching edges as closely as possible. If the angle between the edges is not too great,
the dragged polygon should rotate so that the edges coincide.
Right-clicking on the canvas will toggle between dragging and rotating."""),
html.P(html.B("Demo 5")+""" - This demostrates MouseMode.DRAW. Click, then move to start drawing a shape.
Click again to create a new vertex. Double-click to finish the shape."""+html.BR()+
"""Right-clicking will cycle between different types of shape:"""+html.BR()+
"""polygon, polyline, rectangle, ellipse, circle, (smooth) bezier, and (smooth) closedbezier"""),
html.P(html.B("Demo 6")+""" - This demostrates MouseMode.EDIT. Clicking on a shape will display some handles,
which can be dragged to change the shape. Bezier shapes also have (green) control handles which change the curvature
at a vertex. For a smooth Bezier shape, these will move as a pair."""),
html.P(html.B("Demo 7")+""" - This demostrates switching between MouseMode.TRANSFORM and MouseMode.EDIT.
Right-clicking on the canvas will toggle between rotating a shape (as in Demo 2)
and editing it using the handles (as in Demo 6)."""),
html.P(html.B("Demo 8")+""" - This demostrates how to check the position of a polygon relative to another polygon.
Drag one of the yellow shapes, and its colour will change depending on its relationship with the white, fixed, polygon.
Green=Inside, Pink=Overlapping, Yellow=Disjoint, Orange=Containing, and Blue=Equal.
Right-click rotates a shape by 90 degrees.""")
]

pages[0] <= introtext
