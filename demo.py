from browser import document, html, window
#import time
#tt = time.time()
import brywidgets as ws
#print(time.time()-tt)

class DemoPage(ws.NotebookPage):
    def update(self):
        __import__(self.id)

pages = [ws.NotebookPage("Introduction", "powderblue", tabwidth="12%", id="intro")]
for i in range(1,8):
    rgb1, rgb2 = ws.hwbtorgb(60+i*180,0.5,0)[1], ws.hwbtorgb(60+i*180,0.4,0.1)[1]
    pages.append(DemoPage("Demo "+str(i), "rgb({},{},{})".format(*rgb1), tabwidth=None, id="demo"+str(i)))
    pages.append(ws.NotebookPage("Code "+str(i), "rgb({},{},{})".format(*rgb2), html.TEXTAREA(open("demo"+str(i)+".py").read()), tabwidth=None, id="code"+str(i)))
document.select("body")[0].innerHTML = ""
document <= (notebook := ws.Notebook(pages))
pageheight = f"calc(95vh - {notebook.tabrow.offsetHeight}px)"
for page in pages: page.style.height = pageheight

introtext = html.DIV([
html.H1("BrySVG DEMO"),
html.P("""The other tabs on this page provide a series of short demos showing the capabilities of the BrySVG module.
For each demo there is also a tab showing the code needed to create it.  A brief description of each demo follows:"""),
html.P(html.B("Demo 1")+""" - This illustrates MouseMode.PAN: drag the canvas to move the viewport."""+html.BR()+
"""It also shows how to create most of the SVG objects:
CanvasObject, PolylineObject, PolygonObject, RectangleObject, EllipseObject, CircleObject, BezierObject,
ClosedBezierObject, SmoothBezierObject, SmoothClosedBezierObject, TextObject, WrappingTextObject"""+html.BR()+
"""and the use of the CanvasObject methods rotateElement and translateElement.
(The same set of objects is also used in Demo2 and Demo 6.)"""),
html.P(html.B("Demo 2")+""" - This is the famous Tangram puzzle, which demonstrates MouseMode.DRAG and canvas.vertexSnap.
Drag a piece onto the square. If a vertex of the piece is close to a vertex of the square, the piece will "snap"
so that the vertices match. To complete the puzzle, fill the square completely with the pieces."""),
html.P(html.B("Demo 3")+""" - This demonstrates MouseMode.TRANSFORM. Objects can be dragged around on the canvas.
In addition, clicking on an object shows a bounding box and a number of handles which can be used to transform the shape:
top-left: rotate; middle-right: stretch horizontally; bottom-middle: stretch vertically; bottom-right: enlarge"""),
html.P(html.B("Demo 4")+""" - This demonstrates canvas.edgeSnap, and also how to create RegularPolygons.
Drag the polygons around, matching edges as closely as possible. If the angle between the edges is not too great,
the dragged polygon should rotate so that the edges coincide. Polygons can also be rotated by hand."""),
html.P(html.B("Demo 5")+""" - This demonstrates ImageButtons, MouseMode.DRAW, and MouseMode.EDIT. Choose a type of shape.
Click on the canvas, then move to start drawing a shape. Click again to create a new vertex.
To finish the shape and switch to MouseMode.EDIT, either double-click on the canvas or tap on the "select" button (top left)"""+html.BR()+
"""Now clicking on a shape will display some (red) handles, which can be dragged to change the shape.
Clicking on a handle of a Bezier shape will display (green) control handles which control the curvature at that vertex.
For a smooth Bezier shape, these will move as a pair."""),
html.P(html.B("Demo 6")+""" - This demonstrates switching between MouseMode.TRANSFORM and MouseMode.EDIT.
Double-clicking on the canvas will toggle between transforming the shapes (as in Demo 2)
and editing them using the handles (as in Demo 5)."""),
html.P(html.B("Demo 7")+""" - This demonstrates some of the methods in the polygoncanvas module.
Drag one of the yellow shapes; its colour will change depending on its position relative to the white, fixed, polygon.
Green=Inside, Pink=Overlapping, Yellow=Disjoint, Orange=Containing, and Blue=Equal. The intersection points (if any) will also be shown.""")
], id="introtext")

pages[0] <= introtext
#print(window.location.href)
#tabno = document.query.getfirst("tab", 0)
#notebook.pagelist[int(tabno)].tab.select()
