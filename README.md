# brySVG

Classes for simplifying the use of SVG graphics in Brython projects.

To use, download the zip, and move the brySVG folder into your own project folder.  Then just include `import brySVG` in your brython file.  
(I use `import brySVG as SVG` to make references shorter.)

Description of some of the classes:

## CanvasObject

`CanvasObject(width, height, colour="white", id=None)`

Wrapper for SVG svg element.  

**Parameters:**  
`width, height`: NB these are the CSS properties, so can be given as percentages, or vh, vw units etc.(To set the SVG attributes which are in pixels, call `canvas.setDimensions()` after creating the object.)  
`colour`: the background colour  
`id`: the DOM id

### Methods  
`setDimensions()`:
If the canvas was created using non-pixel dimensions (eg percentages), call this after creation to set the SVG width and height attributes.

`AddObject(self, svgobject)`:  
Adds an object to the canvas, and also adds it to the canvas's `ObjectDict` so that it can be referenced using `canvas.ObjectDict[id]`. This is also needed for the object to be capable of being *snapped* to.  
(Note that referencing using `document[id]` will only give the SVG element, not the Python object.)   
If it is not desired that an object should be in the `ObjectDict`, just add it to the canvas using Brython's <= method.

`fitContents()`:
Scales the canvas so that all the objects on it are visible.

`ClearAll()`:
Clear all elements from the canvas.

`getSVGcoords(event)`:
Converts mouse event coordinates to SVG coordinates.

*(Note that the following three methods do not update the object's `PointList`, so that mouse interaction with the object will no longer work correctly.  If mouse interaction is needed, carry out transformations using the methods defined on the object itself (see __Common methods for shape objects__ below).  However, if mouse interaction is not needed, these methods are faster.)*

`translateElement(element, vector)`:
Translate `element` by `vector`.

`rotateElement(element, angle, centre=None)`:
Rotate `element` clockwise by `angle` degrees around `centre`.
If `centre` is not given, it is the centre of the object's bounding box.

`scaleElement(element, xscale, yscale=None)`:
Enlarge or stretch `element` by scale factors `xscale` and `yscale`, with centre (0, 0).
If `yscale` is not given, it is equal to `xscale`, ie the element is enlarged without stretching.

The CanvasObject also has various attributes which affect how mouse interaction works.  These are described in the section *Canvas Mouse Interaction* below.

## Shape Objects

**Common Parameters**
`linecolour`: Colour of the edges of the object.  
`linewidth`: Width of the edges in SVG units.  
`fillcolour`: Colour of the inside of the object.

### PolygonObject, PolyLineObject

`PolygonObject(pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow")`  
`PolylineObject(pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow")`  
Wrappers for SVG polygon and polyline.  
Parameter:  
`pointlist`: a list of coordinates for the vertices.

### RectangleObject, EllipseObject

`RectangleObject(pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow")`  
Parameters:  
`pointlist`: Two diagonally opposite corners of the rectangle.  
`angle`: The angle (in degrees, clockwise) through which the edges of the rectangle are rotated from horizontal and vertical.


`EllipseObject(pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow")`  
Parameters:  
`pointlist`: Two diagonally opposite corners of the bounding box of the ellipse.  
`angle`: The angle (in degrees, clockwise) through which the edges of the bounding box are rotated from horizontal and vertical.

### CircleObject, LineObject

`CircleObject(self, centre=(0,0), radius=0, pointlist=None, linecolour="black", linewidth=1, fillcolour="yellow")`  
Parameters:  
**Either** `centre` and `radius` of the circle.  
**or** `pointlist`: a list of two points - the centre of the circle and any point on the circumference.  
(If both are given, the `pointlist` takes priority.)

`LineObject(pointlist=[(0,0), (0,0)], style="solid", linecolour="black", linewidth=1, fillcolour=None)`  
Parameters:  
`pointlist`: the two endpoints of the line.  
`style`: Either `"solid"`, `"faintdash1"` or `"faintdash2"` (the last two are for use when drawing graph paper).

### Bezier Objects

`BezierObject(pointsetlist=[(None, (0,0), (0,0)), ((0,0), (0,0), None)], linecolour="black", linewidth=1, fillcolour=None)`  
A general Bezier curve. Parameter:  
`pointsetlist`: a list of tuples, each tuple consisting of three points: `(previous-control-point, vertex, next-control-point)`.  
The control points control the curvature of the curve at that vertex.
For the first vertex, the `previous-control-point` must be `None`,
and for the last vertex, the `next-control-point` must be `None`.

`ClosedBezierObject(pointsetlist=[((0,0), (0,0), (0,0))], linecolour="black", linewidth=1, fillcolour="yellow")`  
A closed general Bezier curve (the first vertex does not need to be repeated). Parameter:  
`pointsetlist`: a list of tuples, each tuple consisting of three points: `(previous-control-point, vertex, next-control-point)`.

`SmoothBezierObject(pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour=None)`  
A smooth Bezier curve. Parameter:  
`pointlist`: a list of vertices. (Control points will be calculated automatically so that the curve is smooth at each vertex.)

`SmoothClosedBezierObject(pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow")`  
A closed smooth Bezier curve (the first vertex does not need to be repeated).  Parameter:
`pointlist`: a list of vertices. (Control points will be calculated automatically so that the curve is smooth at each vertex.)

### Common methods for shape objects

These can be applied to all the shapes above.

`cloneObject()`: Returns a clone of an object, including the extra functionality provided by this module. (NB If that functionality is not needed, it is better to call the DOM method `cloneNode(object)` on the CanvasObject, as that is much faster.)

`translate(vector)`: Translate object by `vector`.

`rotate(angle, centre=None)`: Rotate object clockwise by `angle` degrees about `centre`. If `centre` is not given, it is the centre of the object's bounding box.

`rotateByVectors(vec1, vec2, centre=(0, 0))`: Rotate object clockwise by the angle between `vec1` and `vec2` about `centre`. If `centre` is not given, it is the origin.

`xstretch(xscale, cx=0)`: Stretch object in the x-direction by scale factor `xscale`, with invariant line `x = cx`. If cx is not given, the invariant line is the y-axis.

`ystretch(yscale, cy=0)`: Stretch object in the y-direction by scale factor `yscale`, with invariant line `y = cy`. If cy is not given, the invariant line is the x-axis.

`enlarge(scalefactor, centre`): Enlarge object by scale factor `scalefactor`, with centre `centre`. If `centre` is not given, the centre is the origin.

## Canvas Mouse Interaction

The `CanvasObject` has various attributes which control how it responds to mouse actions:

### canvas.MouseMode = MouseMode.TRANSFORM
In this mode, clicking on an object and dragging carries out the transformation which has been set using `canvas.setMouseTransformType()`.  This can be:  
`TransformType.NONE, TransformType.TRANSLATE, TransformType.ROTATE, TransformType.XSTRETCH, TransformType.YSTRETCH, TransformType.ENLARGE`

`canvas.Snap`: To force "snapping", set this parameter to a number of pixels. After a transform, if a vertex of the transformed object is within `canvas.Snap` pixels of a vertex of another object in the canvas's ObjectDict, the transformed object is snapped so that the vertices coincide. (If more than one pair of vertices are below the snap threshold, the closest pair are used.  
If `canvas.Snap` is set to `None` (the default), no snapping will be done.

`canvas.RotateSnap`: To allow rotation when "snapping", set this to a number of degrees. After a transform, if a snap is to be done, and the edges of the two shapes at the vertex to be snapped are within this many degrees of each other, the transformed shape will be rotated so that the edges coincide.  
If `canvas.RotateSnap` is set to `None` (the default), no rotating will be done.  
If `canvas.Snap` is set to `None`, the value of `canvas.RotateSnap` has no effect.

### canvas.MouseMode = MouseMode.DRAW
Shapes can be drawn on the canvas by clicking, moving, clicking again...  
A shape is completed by double-clicking.
The shape which will be drawn is chosen by setting `canvas.Tool`, which can be:
`line, polygon, polyline, rectangle, ellipse, circle, bezier, closedbezier`  
(NB the bezier shapes will be smooth.)
The stroke, stroke-width and fill of the shape are determined by the values of by `canvas.PenColour`, `canvas.PenWidth`, and `canvas.FillColour`.

### canvas.MouseMode = MouseMode.EDIT
Clicking on a shape causes "handles" to be displayed, which can be used to edit the shape. (For Bezier shapes there are also "control handles" to control the curvature.) In this mode, `canvas.Tool` will normally be set to `select`.  
`canvas.SelectedShape` is the shape curently being edited. Use `canvas.DeSelectShape()` to stop editing a shape and hide the handles.
    
### canvas.MouseMode = MouseMode.NONE
No user interaction with the canvas.








