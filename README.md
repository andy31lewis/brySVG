# brySVG

## New in version 0.2.0

- Support for touch screens, including larger, "finger-sized" handles and more touch-friendly selection of thin lines.  
- Redesigned mouse transformations, now using handles on a bounding-box.  
- The module is now split into several files, for faster imports if only a subset of the full functionality is needed.
- More consistent API; all methods now follow the DOM convention of camelCase eg `canvas.addObject(obj)`
- `Button`, `ImageButton`, (multiline) `TextObject`, and `WrappingTextObject` added.

## Introduction

This module provides classes for simplifying the use of SVG graphics in Brython projects.

To use, download the zip, and move the brySVG folder into your own project folder:  

Then just include an `import` statement in your brython file:  
`import brySVG.dragcanvas as SVG` if only MouseMode.DRAG is required  
`import brySVG.transformcanvas as SVG` if MouseMode.TRANSFORM is required (also allows MouseMode.DRAG)  
`import brySVG.drawcanvas as SVG` if MouseMode.DRAW and MouseMode.EDIT are required (also allows MouseMode.DRAG)  
`import brySVG.fullcanvas as SVG` if all four MouseModes are required  
(See below for description of the different modes.)

You can add extra functionality for polygons by including, in addition to one of the above:  
`from brySVG.polygontesting import *`  
See the section **Polygon Testing** below for details of these functions.

Description of some of the classes:

## CanvasObject

`CanvasObject(width, height, colour="white", objid=None)`

Wrapper for SVG svg element.  

**Parameters:**  
`width, height`: NB these are the CSS properties, so can be given as percentages, or vh, vw units etc.(To set the SVG attributes which are in pixels, call `canvas.setDimensions()` after creating the object.)  
`colour`: the background colour  
`objid`: the DOM id

### Methods  
`setDimensions()`:
If the canvas was created using non-pixel dimensions (eg percentages), call this after creation to set the SVG width and height attributes. Returns a tuple `(width, height)`.

`fitContents()`:
Scales the canvas so that all the objects on it are visible.

`getScaleFactor()`
Recalculates `self.scaleFactor` (which is used for converting css pixels to the SVG units of this canvas). This is called automatically by `fitContents()`, but should be called manually after zooming in or out of the canvas in some other way.

`getSVGcoords(event)`:
Converts mouse event coordinates to SVG coordinates. Returns a `Point` object.

`addObject(svgobject, objid=None, fixed=False)`:  
Adds an object to the canvas, and also adds it to the canvas's `objectDict` so that it can be referenced using `canvas.objectDict[id]`. This is also needed for the object to be capable of being *snapped* to.  If the object should not be capable of being dragged or transformed with mouse actions, set `fixed` to True.  
(Note that referencing using `document[id]` will only give the SVG element, not the Python object.)   
If it is not desired that an object should be in the `objectDict`, just add it to the canvas using Brython's `<=` method.

`deleteObject(svgobject)`
Delete an object from the canvas.  

`deleteAll()`
Clear all elements from the canvas.

`translateObject(svgobject, offset)`
Translate an `svgobject` by `offset`.  Unlike `translateElement` (below), this will preserve the extra functionality provided by this module - ie the shape will still be able to be selected, dragged, etc.

*(Note that the following three methods do not update the object's `PointList`, so that mouse interaction with the object will no longer work correctly.  If mouse interaction is needed, carry out transformations using the methods defined on the object itself (see __Common methods for shape objects__ below).  However, if mouse interaction is not needed, these methods are __faster__.)*

`translateElement(element, vector)`:
Translate `element` by `vector`.

`rotateElement(element, angle, centre=None)`:
Rotate `element` clockwise by `angle` degrees around `centre`.
If `centre` is not given, it is the centre of the object's bounding box.

`scaleElement(element, xscale, yscale=None)`:
Enlarge or stretch `element` by scale factors `xscale` and `yscale`, with centre (0, 0).
If `yscale` is not given, it is equal to `xscale`, ie the element is enlarged without stretching.

The CanvasObject also has various attributes which affect how mouse interaction works.  These are described in the section *__Canvas Mouse Interaction__* below.

## Shape Objects

**Common Parameters**  
`linecolour`: Colour of the edges of the object.  
`linewidth`: Width of the edges in SVG units.  
`fillcolour`: Colour of the inside of the object.

### PolygonObject, PolyLineObject

`PolygonObject(pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow")`  
`PolylineObject(pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="none")`  
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

`LineObject(pointlist=[(0,0), (0,0)], style="solid", linecolour="black", linewidth=1, fillcolour="none")`  
Parameters:  
`pointlist`: the two endpoints of the line.  
`style`: Either `"solid"`, `"faintdash1"` or `"faintdash2"` (the last two are for use when drawing graph paper).

### Bezier Objects

`BezierObject(pointsetlist=[(None, (0,0), (0,0)), ((0,0), (0,0), None)], linecolour="black", linewidth=1, fillcolour="none")`  
A general Bezier curve. Parameter:  
`pointsetlist`: a list of tuples, each tuple consisting of three points: `(previous-control-point, vertex, next-control-point)`.  
The control points control the curvature of the curve at that vertex.
For the first vertex, the `previous-control-point` must be `None`,
and for the last vertex, the `next-control-point` must be `None`.

`ClosedBezierObject(pointsetlist=[((0,0), (0,0), (0,0))], linecolour="black", linewidth=1, fillcolour="yellow")`  
A closed general Bezier curve (the first vertex does not need to be repeated). Parameter:  
`pointsetlist`: a list of tuples, each tuple consisting of three points: `(previous-control-point, vertex, next-control-point)`.

`SmoothBezierObject(pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="none")`  
A smooth Bezier curve. Parameter:  
`pointlist`: a list of vertices. (Control points will be calculated automatically so that the curve is smooth at each vertex.)

`SmoothClosedBezierObject(pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow")`  
A closed smooth Bezier curve (the first vertex does not need to be repeated).  Parameter:  
`pointlist`: a list of vertices. (Control points will be calculated automatically so that the curve is smooth at each vertex.)

### Regular polygons

`RegularPolygon(sidecount, centre=None, radius=None, startpoint=None, sidelength=None, offsetangle=0, linecolour="black", linewidth=1, fillcolour="yellow")`  
Parameters:  
`sidecount`: the number of sides.  
**Either** `centre`: the centre of the polygon, **or** `startpoint`: the coordinates of a vertex at the top of the polygon.  
**Either** `radius`: the radius of the polygon, **or** `sidelength`: the length of each side.  
`offsetangle`: (optional) the angle (in degrees, clockwise) by which the top edge of the polygon is rotated from the horizontal.

### Common methods for shape objects

These can be applied to all the shapes above. Apart from `cloneObject()`, which is always available, the methods in this section are only available if the module has been imported using `import transformcanvas as SVG` or `import fullcanvas as SVG`.

`cloneObject()`: Returns a clone of an object, including the extra functionality provided by this module. (NB If that functionality is not needed, it is better to call the DOM method `cloneNode(object)` on the CanvasObject, as that is much faster.)

`translate(vector)`: Translate object by `vector`.

`rotate(angle, centre=None)`: Rotate object clockwise by `angle` degrees about `centre`. If `centre` is not given, it is the centre of the object's bounding box.

`rotateByVectors(vec1, vec2, centre=(0, 0))`: Rotate object clockwise by the angle between `vec1` and `vec2` about `centre`. If `centre` is not given, it is the origin.

`xstretch(xscale, cx=0)`: Stretch object in the x-direction by scale factor `xscale`, with invariant line `x = cx`. If cx is not given, the invariant line is the y-axis.

`ystretch(yscale, cy=0)`: Stretch object in the y-direction by scale factor `yscale`, with invariant line `y = cy`. If cy is not given, the invariant line is the x-axis.

`enlarge(scalefactor, centre`): Enlarge object by scale factor `scalefactor`, with centre `centre`. If `centre` is not given, the centre is the origin.

## Canvas Mouse Interaction

The `CanvasObject` has various attributes which control how it responds to mouse actions:

### canvas.mouseMode = MouseMode.DRAG

Objects can be dragged around on the canvas.  
`canvas.selectedObject` is the shape which was lasted dragged.

`canvas.snap`: set to a number of pixels. After a drag, if a vertex of the transformed object is within this many pixels of a vertex of another object in the canvas's objectDict, the dragged object is snapped so that the vertices coincide. (If more than one pair of vertices are below the snap threshold, the closest pair are used.  
If `canvas.snap` is set to `None` (the default), no snapping will be done.

### canvas.mouseMode = MouseMode.TRANSFORM

Objects can be dragged around on the canvas.  In addition, clicking on an object shows a bounding box and a number of handles (which ones can be controlled by setting `canvas.transformTypes` to the list of transforms required. By default, `canvas.transformTypes` includes:  
`[TransformType.TRANSLATE, TransformType.ROTATE, TransformType.XSTRETCH, TransformType.YSTRETCH, TransformType.ENLARGE]`  
`canvas.selectedObject` is the shape curently being transformed.

`canvas.rotateSnap`: set to a number of degrees. After a transform, if a snap is to be done, and the edges of the two shapes at the vertex to be snapped are within this many degrees of each other, the transformed shape will be rotated so that the edges coincide.  
If `canvas.rotateSnap` is set to `None` (the default), no rotating will be done.  
If `canvas.snap` is set to `None`, the value of `canvas.rotateSnap` has no effect.

### canvas.mouseMode = MouseMode.DRAW
Shapes can be drawn on the canvas by clicking, moving, clicking again...  
A shape can be completed by double-clicking (for touch-screen use, it may be better to provide a button which calls the `canvas.endDraw()` method).  
The shape which will be drawn is chosen by setting `canvas.tool`, which can be:
`line, polygon, polyline, rectangle, ellipse, circle, bezier, closedbezier, smoothbezier, smoothclosedbezier`  
If `canvas.tool` is set to `"select"`, no drawing will be done. 
The stroke, stroke-width and fill of the shape are determined by the values of by `canvas.penColour`, `canvas.penWidth`, and `canvas.fillColour`.

### canvas.mouseMode = MouseMode.EDIT
Clicking on a shape causes "handles" to be displayed, which can be used to edit the shape. (For Bezier shapes clicking on a handle causes "control handles" to be displayed, to control the curvature.) In this mode, `canvas.tool` will be set to `"select"`.  
While a shape is selected, pressing the `DEL` key on the keyboard will delete the shape.  
`canvas.selectedObject` is the shape curently being edited. Use `canvas.deselectObject()` to stop editing a shape and hide the handles.
    
### canvas.MouseMode = MouseMode.NONE
No user interaction with the canvas.

## Other Objects

### TextObjects

`TextObject(string, anchorpoint, anchorposition=1, fontsize=12, style="normal", ignorescaling=False, canvas=None)`  
A multiline textbox.  Use `"\n"` within `string` to separate lines. To make sure the font-size is not affected by the scaling of the canvas, set `ignorescaling` to `True`, and specify the `canvas` on which the object will be placed.  
The box is placed at the coordinates given by `anchorpoint`; the `anchorposition` can be from 1 to 9:  
1  2  3  
4  5  6  
7  8  9  
ie if `anchorposition` is 1, the `anchorpoint` is top-left, if it is 5 it is in the centre of the box, etc.

`WrappingTextObject(canvas, string, anchorpoint, width, anchorposition=1, fontsize=12, style="normal", ignorescaling=False`  
See `TextObject` above for explanation of most of the parameters; however, note that `canvas` *must* be specified.  
A `width` in SVG units is also specified, and the text `string` will be wrapped at word boundaries to fit that width.

### Buttons

`Button(position, size, text, onclick, fontsize=None, fillcolour="lightgrey", objid=None)`  
A clickable button with (multiline) `text` on it(use `\n` for line breaks). If `fontsize` is not specified, the text will be scaled to fit the height (but not width) of the button. The `onclick` parameter is the function which handles the click event.

`ImageButton(position, size, image, onclick, fillcolour="lightgrey", canvas=None, objid=None)`  
A clickable button with an SVG image on it. The centre of the image should be at (0,0). If the `canvas` is specified, the image will be scaled to fit inside the button. The onclick parameter is the function which handles the event.

## Polygon testing

Including `from polygontesting import *` provides the following additional functions. `poly`, `poly1`, `poly2` are `PolygonObjects`, `point` is a `PointObject`.

`polygonobjectarea(poly)`  
Returns the area of the PolygonObject.

`equalpolygonobjects(poly1, poly2)`  
Returns True if poly1 is identical to poly2, False otherwise.

`containspoint(poly, point)`  
Returns "interior" if point is inside the polygon, "edge" if it is on an edge,  "vertex" if it is at a vertex, or False otherwise.
`dp` is the precision to which the coordinates of the vertices are used.

`relativeposition(poly1, poly2, dp=1)`  
Returns an Enum value: `Position.CONTAINS`, `Position.INSIDE`, `Position.OVERLAPS`, `Position.DISJOINT` or `Position.EQUAL` which describes the position of poly1 relative to poly2.  
`dp` is the precision to which the coordinates of the vertices are used.

`polygonobjectboundingbox(poly)`  
Returns the coordinates of the top left and bottom right vertices of the bounding box of the PolygonObject.

(Note that this module also provides versions of these functions for which the parameter `point` is just a tuple giving the coordinates, and `poly`, `poly1`, and `poly2` are just lists of tuples. Thus the module can be used **independently of brySVG** if required.  In this case the functions are:

`polygonarea(poly)`  
`equalpolygons(poly1, poly2)`  
`containspoint(poly, point)`  
`relativeposition(poly1, poly2, dp=1)`  
`polygonboundingbox(poly)` )







