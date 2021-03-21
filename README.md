# brySVG

To see examples of brySVG in action, try the demo [here](http://mathsanswers.org.uk/oddments/brySVG/demo.html). There are 7 demos, each in a separate tab on the page. In a tab next to each demo is the code used to generate it.

## Introduction

This module provides classes for simplifying the use of SVG graphics in Brython projects. It provides a `CanvasObject` and various `ShapeObjects` which are wrappers round the SVG elements and provide additional functionality.

To use, **either**:

- include the line `<script src="https://cdn.jsdelivr.net/gh/andy31lewis/brySVG@0.4.0/brySVG.brython.js"></script>` in your html file **or**  
- download the zip, and move the brySVG folder into your own project folder:  

Then just include an `import` statement in your brython file:  

- **`import brySVG.dragcanvas as SVG`** if only `MouseMode.DRAG` or `MouseMode.PAN` is required  
- **`import brySVG.transformcanvas as SVG`** if `MouseMode.TRANSFORM` is required (also allows `DRAG` or `PAN`)
- **`import brySVG.polygoncanvas as SVG`** if you want to use the extra functionality for polygons. (See the section **Polygon handling** below - also allows `TRANSFORM`, `DRAG` or `PAN`.)  
- **`import brySVG.drawcanvas as SVG`** if `MouseMode.DRAW` and `MouseMode.EDIT` are required (also allows `DRAG` or `PAN`)  
- **`import brySVG.fullcanvas as SVG`** if you think you might need all the above.

(See below for description of the different modes.)

## CanvasObject

`CanvasObject(width, height, colour="white", objid=None)`

Wrapper for SVG `svg` element.  

**Parameters:**  
`width, height`: NB these are the CSS properties, so can be given as percentages, or vh, vw units etc. (If you need the SVG attributes which are in pixels, call `canvas.setDimensions()` after creating the object.)  
`colour`: the background colour  
`objid`: the DOM id

### Summary (see below for more detail)
To add objects to the canvas, use `canvas.addObject()`.  Objects are stored in `canvas.objectDict` using their `id` as the dictionary key. (if not supplied, ids are made up.)

In most situations it is best to bind methods which manipulate these objects to events on the canvas, rather than the objects themselves. The object on which the event occurred can then be obtained using  `canvas.getSelectedObject(event.target.id)`.

To loop through all objects on the canvas, use `for obj in canvas.objectDict.values()`

### `canvas.mouseMode` and related attributes
After creation, there are various attributes which control how the canvas responds to mouse/touch actions.
`canvas.mouseMode` should be set **after** all initial objects have been added to the canvas.

#### `canvas.mouseMode = MouseMode.NONE`  
No user interaction with the canvas. (This is the default.)

#### `canvas.mouseMode = MouseMode.PAN`  
Dragging the canvas pans the viewport.

#### `canvas.mouseMode = MouseMode.DRAG`
Objects can be dragged around on the canvas.
`canvas.vertexSnap` and `canvas.snapDistance`: If `vertexSnap` is set to True, then after a drag, if a vertex of the dragged object is within `snapDistance` (default is 10) pixels of a vertex of another object in the canvas's `objectDict`, the dragged object is snapped so that the vertices coincide.
(If more than one pair of vertices are below the snap threshold, the closest pair are used.)

#### `canvas.mouseMode = MouseMode.TRANSFORM`
***Before enabling this mode, use `import transformcanvas`, `import polygoncanvas` or `import fullcanvas` instead of `import dragcanvas`***
Objects can be dragged around on the canvas.  In addition, clicking on an object shows a number of handles for transforming the object (which ones can be controlled by setting `canvas.transformTypes` to the list of transforms required).
By default, `canvas.transformTypes` includes all the available types:
`[TransformType.TRANSLATE, TransformType.ROTATE, TransformType.XSTRETCH, TransformType.YSTRETCH, TransformType.ENLARGE]`

#### `canvas.mouseMode = MouseMode.DRAW or MouseMode.EDIT`
***Before enabling one of these modes, use `import drawcanvas` or `import fullcanvas` instead of `import dragcanvas`***
These two modes work together.

##### `MouseMode.DRAW`

To switch from `MouseMode.EDIT` to `MouseMode.DRAW`, use `canvas.setTool(tool)`, where `tool` can be:
`line, polygon, polyline, rectangle, ellipse, circle, bezier, closedbezier, smoothbezier, smoothclosedbezier`
In `DRAW` mode, shapes can be drawn on the canvas by clicking, moving, clicking again...
The shape which will be drawn is chosen using `canvas.setTool(tool)`, as above.
The `stroke`, `stroke-width` and `fill` of the shape being drawn are set by `canvas.penColour`, `canvas.penWidth`, and `canvas.fillColour`. 
A shape is completed by double-clicking, which also switches the canvas to `EDIT` mode (see below).
Alternatively, on a touch screen, a shape is completed by tapping on a button to call  `canvas.setTool()` to switch to `EDIT` mode (for an example see Demo 5 in the brySVG Demo).

##### `MouseMode.EDIT`

To switch from `MouseMode.DRAW` to `MouseMode.EDIT`, use `canvas.setTool(tool)`, where `tool` can be:
`select, insertpoint, deletepoint`
If the tool is `select`, clicking on a shape causes "handles" to be displayed, which can be used to edit the shape.
(For Bezier shapes clicking on a handle causes "control handles" to be displayed, to control the curvature.)
While a shape is selected, pressing the DEL key on the keyboard will delete the shape.
Clicking elsewhere on the canvas deselects the shape.
If the tool is `insertpoint`, then for `polyshapes` or `beziershapes` clicking on the shape's edge inserts a point.
If the tool is `deletepoint`, then for `polyshapes` or `beziershapes` clicking on a handle deletes that point.
(For `line, rectangle, ellipse, circle`, the tools `insertpoint` and `deletepoint` have no effect.)

### Summary of attributes
**Read/write attributes:**
`canvas.mouseMode` (see above)
`canvas.lineWidthScaling`: If this is set to `False`, line thicknesses are independent of the scaling of the canvas (default is `True`).

*(Used if snapping required:)*
`canvas.vertexSnap` (see above)
`canvas.snapDistance` (see above)
`canvas.edgeSnap` (Only available if `polygoncanvas` has been imported, see below)
`canvas.snapAngle` (Only available if `polygoncanvas` has been imported, see below)

*(Only available in `MouseMode.TRANSFORM`, see above:)*
`canvas.transformTypes`

*(Only available in `MouseMode.DRAW`, see above:)*
`canvas.penColour` 
`canvas.penWidth`
`canvas.fillColour`

Other attributes of canvas are intended to be **read-only**:
`canvas.scaleFactor`  (Set automatically by `canvas.setViewBox()` or `canvas.fitContents()`) Multiply by this to convert CSS pixels to SVG units
`canvas.mouseDetected` If false, indicates a touchscreen device
`canvas.mouseOwner` The object (shape or handle) currently being dragged
`canvas.selectedObject` The shape which was last clicked on or dragged
`canvas.dragStartCoords` The coordinates at which the latest drag started
`canvas.viewWindow` After `canvas.setViewBox()` or `canvas.fitContents()`, this gives the SVG coordinates of the top-left and bottom-right of the canvas.
`canvas.tool` Only useful in `MouseMode.DRAW `or `mouseMODE.EDIT` - the current tool (see above)

### Canvas Methods  
`canvas.setDimensions()`
If the canvas was created using non-pixel dimensions (eg percentages), call this after creation to set the SVG width and height attributes. Returns a tuple `(width, height)`.

`canvas.setViewBox(pointlist)`
Should be done after the canvas has been added to the page. `pointlist` is the coordinates of the desired top-left and bottom-right of the canvas. Returns (and stores in `canvas.viewWindow`) the SVG coordinates of the actual top-left and bottom right of the canvas (which will usually be different due to the need to preserve the aspect ratio).

`canvas.fitContents()`
Scales the canvas so that all the objects on it are visible. Returns (and stores in `canvas.viewwindow`) the SVG coordinates of the top-left and bottom-right of the visible canvas.

`canvas.getSVGcoords(event)`
Returns the SVG coordinates if the point where a mouse or touch event occurred, as a `Point` object.

`canvas.getSelectedObject(id, getGroup=True)`
Returns the object on the canvas identified by `id`.  If `getGroup` is `True`, and the object is a member of a `GroupObject`, then the highest level `GroupObject` of which the object is a member is returned.  If `getGroup` is `False`, the object itself is returned.

`canvas.addObject(svgobject, objid=None, fixed=False)`
Adds an object to the canvas, and also adds it to the canvas's `objectDict` so that it can be referenced using `canvas.getSelectedObject(id)`.
This is also needed for the object to be capable of being snapped to.
(Note that referencing using `document[id]` will only give the SVG element, not the Python object.
If it is not desired that an object should be in the `objectDict`, just add it to the canvas using Brython's <= method.)
Set `fixed` to `True` (default `False`) if the object should not be capable of being dragged or transformed with mouse actions.

`canvas.addObjects(objectlist, fixed=False)`
 Add a (possibly nested) list of objects to the canvas.

`canvas.deleteObject(svgobject)`
Delete an object from the canvas, and from `canvas.objectDict`.  

`canvas.deleteAll()`
Clear all elements from the canvas, and from `canvas.objectDict`

`canvas.deleteSelection()`
Delete the currently selected object from the canvas, and from `canvas.objectDict`

`canvas.translateObject(svgobject, offset)`
Translate an `svgobject` by `offset`.  Unlike `translateElement` (below), this will preserve the extra functionality provided by this module - ie the shape will still be able to be selected, dragged, etc.

*(Note that the following three methods do not update the object's `pointList`, so that mouse interaction with the object will no longer work correctly.  If mouse interaction is needed, carry out transformations using the methods defined on the object itself (see __Shape Objects: Common methods__ below).  However, if mouse interaction is not needed, these methods are __faster__.)*

`canvas.translateElement(element, vector)`:
Translate `element` by `vector`.

`canvas.rotateElement(element, angle, centre=None)`:
Rotate `element` clockwise by `angle` degrees around `centre`.
If `centre` is not given, it is the centre of the object's bounding box.

`canvas.scaleElement(element, xscale, yscale=None)`:
Enlarge or stretch `element` by scale factors `xscale` and `yscale`, with centre (0, 0).
If `yscale` is not given, it is equal to `xscale`, ie the element is enlarged without stretching.

***(The methods below are only available if `canvas.mouseMode` has been set to `MouseMode.TRANSFORM`.)***

`canvas.showTransformHandles(svgobj)` Show the handles used to transform `svgobj` (for details see `MouseMode.TRANSFORM` above). Normally clicking on an object would call this method, but it might be useful to call it in other circumstances.

`canvas.hideTransformHandles()` Hide the handles used to transform an object. Normally clicking away from an object would call this method, but it might be useful to call it in other circumstances.

***(The methods below are only available if `canvas.mouseMode` has been set to `MouseMode.DRAW` or `MouseMode.EDIT`.)***

`canvas.setTool(tool)` Set the tool to be used when drawing or editing.  Switches between `DRAW` or `EDIT` mode as appropriate. For details see under `canvas.mouseMode = MouseMode.DRAW or MouseMode.EDIT` above.

`canvas.createHandles(svgobject)` Show the handles used to edit the points of `svgobject` (for details see `MouseMode.EDIT` above). Normally clicking on an object would call this method, but it might be useful to call it in other circumstances.

`canvas.deleteHandles()` Hide the handles used to edit the points of an object. Normally clicking away from an object would call this method, but it might be useful to call it in other circumstances. Unlike the next method, the object will still be selected (ie `canvas.selectedObject` will still refer to it).

`canvas.deselectObject()` If an object is selected, this deselects it.  This will also remove the handles.  Normally clicking away from an object would call this method, but it might be useful to call it in other circumstances. 

## Shape Objects

The following `XxxObject` classes which represent shapes share various common parameters, attributes and methods.

### Common Parameters

When created, as well as the parameters listed for each type of Object, they all share the following optional parameters:
`objid`: id of the object (for referencing in the document or using `canvas.getSelectedObject(id)`
(The following are not applicable to `TextObject`, `WrappingTextObject`, `PointObject` or `UseObject`.)
`linecolour`: colour of the "stroke" or outline of the shape
`linewidth`: width of the outline of the shape (its "stroke-width")
`fillcolour`: colour of the interior of the shape (not applicable to LineObject). Use "none" if no fill desired.

### Common Attributes

After creation and adding to the canvas using `canvas.addObject()`, they have following attributes:

`obj.fixed` (read/write): If set to `True`, the object cannot be dragged or transformed with the mouse (default `False`)

`obj.canvas` (read only): A reference to the canvas which contains the object

`obj.group` (read only): If the object is a member of a `GroupObject`, this is a reference to that group.

`obj.pointList` (read only): See individual object definitions for its meaning. (Not applicable to `TextObject`, `WrappingTextObject` or `PointObject`.)

### Common Methods

`obj.setPointList()`
Change the shape of an object by replacing its `pointList`. Not valid for `PointObjects`, `UseObjects`, `TextObjects` or `WrappingTextObjects`. 
(For `UseObjects`, use instead `obj.setPosition(origin)` to move the object by changing its `origin`, after it has been added to the canvas.)

 `obj.setStyle()`
Utility function to set a CSS style attribute, can be overridden for specific types of object

`obj.cloneObject`
Returns a clone of an object, including the extra functionality provided by this module.
If that functionality is not needed, it is better to call the DOM method `canvas.cloneNode(object)`, as that is much faster. Not valid for `UseObjects`, `TextObjects` or `WrappingTextObjects`.

***(The methods below are only available after `import transformcanvas`, `import polygoncanvas` or `import fullcanvas` )***

`obj.translate(vector)`: Translate object by `vector`.

`obj.rotate(angle, centre=None)`: Rotate object clockwise by `angle` degrees about `centre`. If `centre` is not given, it is the centre of the object's bounding box.

`obj.rotateByVectors(vec1, vec2, centre=(0, 0))`: Rotate object clockwise by the angle between `vec1` and `vec2` about `centre`. If `centre` is not given, it is the origin.

`obj.rotateAndTranslate(self, angle, centre=None, vector=(0,0))`: Rotate object clockwise by `angle` degrees around `centre`, and then translate by `vector`. If `centre` is not given, it is the centre of the object's bounding box.

`obj.xstretch(xscale, cx=0)`: Stretch object in the x-direction by scale factor `xscale`, with invariant line `x = cx`. If cx is not given, the invariant line is the y-axis.

`obj.ystretch(yscale, cy=0)`: Stretch object in the y-direction by scale factor `yscale`, with invariant line `y = cy`. If cy is not given, the invariant line is the x-axis.

`obj.enlarge(scalefactor, centre`): Enlarge object by scale factor `scalefactor`, with centre `centre`. If `centre` is not given, the centre is the origin.

***(The methods below are only available after `import drawcanvas` or `import fullcanvas` )***

`obj.setPoint(self, i, point)`: change the point with index `i` in `obj.pointList` to `point` (which should be a `Point` object)

*(All the following are not available for `LineObject`, `RectangleObject`, `EllipseObject`, `CircleObject`)*

`obj.insertPoint(self, index, point)`: insert a `Point` object at index `i` in `obj.pointList`

`obj.deletePoint(self, index)`: delete the point with index `i` from `obj.pointList`

`obj.deletePoints(self, start, end)`:  delete a slice of points `obj.pointList[start:end]`

*(The following are only available for Bezier type objects)*

`obj.setPointset(self, i, pointset)`: change the pointset with index `i` to `pointset` 
(a "pointset" is a tuple of 3 `Points`,`(previous-control-point, vertex, next-control-point)`.  
The control points control the curvature of the curve at that vertex.)

`obj.setPointsetList(self, pointsetlist)`: replace `obj.pointsetList` with a whole new list of pointsets

*There follows details specific to the different types of object.*

### PolygonObject, PolyLineObject

**`PolygonObject(pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow", objid=None)`  
`PolylineObject(pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="none", objid=None)`** 
Wrappers for SVG `polygon` and `polyline`.  
Parameter:  
`pointlist`: a list of coordinates for the vertices.

### RectangleObject, EllipseObject

**`RectangleObject(pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow", objid=None)`**  
Parameters:  
`pointlist`: Two diagonally opposite corners of the rectangle.  
`angle`: The angle (in degrees, clockwise) through which the edges of the rectangle are rotated from horizontal and vertical.

**`EllipseObject(pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow", objid=None)` ** 
Parameters:  
`pointlist`: Two diagonally opposite corners of the bounding box of the ellipse.  
`angle`: The angle (in degrees, clockwise) through which the edges of the bounding box are rotated from horizontal and vertical.

### CircleObject, LineObject

**`CircleObject(self, centre=(0,0), radius=0, pointlist=None, linecolour="black", linewidth=1, fillcolour="yellow", objid=None)`**  
Parameters:  
**Either** `centre` and `radius` of the circle.  
**or** `pointlist`: a list of two points - the centre of the circle and any point on the circumference.  
(If both are given, the `pointlist` takes priority.)

**`LineObject(pointlist=[(0,0), (0,0)], style="solid", linecolour="black", linewidth=1, fillcolour="none", objid=None)` ** 
Parameters:  
`pointlist`: the two endpoints of the line.  
`style`: Either `"solid"`, `"faintdash1"` or `"faintdash2"` (the last two are for use when drawing graph paper).

### Bezier Objects

**`BezierObject(pointsetlist=[(None, (0,0), (0,0)), ((0,0), (0,0), None)], linecolour="black", linewidth=1, fillcolour="none", objid=None)`**  
A general Bezier curve. Parameter:  
`pointsetlist`: a list of tuples, each tuple consisting of three points: `(previous-control-point, vertex, next-control-point)`.  
The control points control the curvature of the curve at that vertex.
For the first vertex, the `previous-control-point` must be `None`,
and for the last vertex, the `next-control-point` must be `None`.

**`ClosedBezierObject(pointsetlist=[((0,0), (0,0), (0,0))], linecolour="black", linewidth=1, fillcolour="yellow", objid=None)` **
A closed general Bezier curve (the first vertex does not need to be repeated). Parameter:  
`pointsetlist`: a list of tuples, each tuple consisting of three points: `(previous-control-point, vertex, next-control-point)`.

**`SmoothBezierObject(pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="none", objid=None)` ** 
A smooth Bezier curve. Parameter:  
`pointlist`: a list of vertices. (Control points will be calculated automatically so that the curve is smooth at each vertex.)

**`SmoothClosedBezierObject(pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow", objid=None)`**
A closed smooth Bezier curve (the first vertex does not need to be repeated).  Parameter:  
`pointlist`: a list of vertices. (Control points will be calculated automatically so that the curve is smooth at each vertex.)

### Regular polygons

**`RegularPolygon(sidecount, centre=None, radius=None, startpoint=None, sidelength=None, offsetangle=0, linecolour="black", linewidth=1, fillcolour="yellow", objid=None)`**
Parameters:  
`sidecount`: the number of sides.  
**Either** `centre`: the centre of the polygon, **or** `startpoint`: the coordinates of a vertex at the top of the polygon.  
**Either** `radius`: the radius of the polygon, **or** `sidelength`: the length of each side.  
`offsetangle`: (optional) the angle (in degrees, clockwise) by which the top edge of the polygon is rotated from the horizontal.

## Other Objects

### TextObjects

**`TextObject(string, anchorpoint, anchorposition=1, fontsize=12, style="normal", ignorescaling=False, canvas=None, objid=None)`**  
A multiline textbox.  Use `"\n"` within `string` to separate lines. To make sure the font-size is not affected by the scaling of the canvas, set `ignorescaling` to `True`, and specify the `canvas` on which the object will be placed.  
The box is placed at the coordinates given by `anchorpoint`; the `anchorposition` can be from 1 to 9:  
1  2  3  
4  5  6  
7  8  9  
ie if `anchorposition` is 1, the `anchorpoint` is top-left, if it is 5 it is in the centre of the box, etc.

**`WrappingTextObject(canvas, string, anchorpoint, width, anchorposition=1, fontsize=12, style="normal", ignorescaling=False, objid=None)`**  
See `TextObject` above for explanation of most of the parameters; however, note that `canvas` *must* be specified.  
A `width` in SVG units is also specified, and the text `string` will be wrapped at word boundaries to fit that width.

### Buttons

**`Button(position, size, text, onclick, fontsize=None, fillcolour="lightgrey", objid=None)`**  
A clickable button with (multiline) `text` on it(use `\n` for line breaks). If `fontsize` is not specified, the text will be scaled to fit the height (but not width) of the button. The `onclick` parameter is the function which handles the click event.

**`ImageButton(position, size, image, onclick, fillcolour="lightgrey", canvas=None, objid=None)`**  
A clickable button with an SVG image on it. The centre of the image should be at (0,0). If the `canvas` is specified, the image will be scaled to fit inside the button. The onclick parameter is the function which handles the event.

### Miscellaneous

**`GroupObject(objlist=[], objid=None)`**
Wrapper for SVG `g` element. Parameter:
`objlist`: list of the objects to include in the group.

Attribute:
`objectList`: To loop through all the objects in the group, use `for obj in group.objectList`

Methods:
`addObject()`: add an object to the group
`addObjects()`: add a list of objects to the group
`removeObject()`: remove an object from the group (and from the canvas if the group is on the canvas)
`deleteAll()`: remove all objects from the group (and from the canvas if the group is on the canvas)

**`UseObject(href=None, origin=(0,0), angle=0, objid=None)`**
Wrapper for SVG `use` element.  Parameters:
`href`: the `#id` of the object being cloned
`origin`: coordinates on the canvas of the point (0,0) of the object being cloned
`angle`: an optional angle of rotation (clockwise, in degrees).
Method:
`obj.setPosition(origin)`: Move the object by changing its `origin`, after it has been added to the canvas.

## Polygon handling

Using `import polygoncanvas as SVG` provides the following additional class, methods and functions.

### PolygonGroups

**`PolygonGroup(objlist=[], objid=None)`**
This class is a `GroupObject` which can only contain polygons.  It has the same parameters and methods as `GroupObject`

If the polygons all touch or overlap, it also has a property `group.boundary` which is a `PolygonObject` forming the outer boundary of all the polygons in the group.  In this case, the `PolygonGroup` has the same methods as listed below for `PolygonObjects`, operating on its `boundary`.

### Methods on `PolygonObjects` and `PolygonGroups`

`area()`:
Returns the area of the PolygonObject.

`getBoundingBox()`:
Returns bounding box based strictly on coordinates. This can be used before the polygon is on the canvas (unlike built-in `getBBox`).

`isEqual(other)`:
Returns `True` if the polygon is identical to `other`, `False` otherwise.

`positionRelativeTo(other)`:
Returns an Enum value showing the position of the polygon relative to `other`: `Position.CONTAINS`, `Position.INSIDE`, `Position.OVERLAPS`, `Position.DISJOINT` or `Position.EQUAL`.  
`other` is another `PolygonObject`.

`getIntersections(other)`:
Returns a list of the intersections between the polygon and `other`.  
Each intersection is represented by an Intersection object which has 3 attributes:  
`.point`: a `Point` whose coordinates are the intersection  
`.selfindex`: if this is an integer `i`, the intersection is at a vertex of the polygon, namely `pointList[i]`; if this is a tuple `(i-1, i)`, the intersection is between `pointList[i-1]` and `pointList[i]`  
`.otherindex`: same as `selfindex` but describes the location of the intersection on the other polygon.

`merge(other)`:
If `other` touches or overlaps the polygon, this returns a PolygonObject which is the outer boundary of the polygon and `other`.  Otherwise returns `None`.

### Functions operating on list of `PolygonObjects` and/or `PolygonGroups`

`SVG.boundary(polylist)`: If all the objects in the `polylist` touch or overlap, this returns a PolygonObject which is their outer boundary.  Otherwise returns `None`.

`SVG.findintersections(polylist)`:
Returns a list of all the intersections between the objects in `polylist`.  
Each intersection is represented by an `Intersection` object which has 2 attributes:  
`.point`: a `Point` whose coordinates are the intersection  
`.polyrefs`: a dictionary whose keys are the polygons which intersect at the that point.  For each key, the value is the `index`.  
If this is an integer `i`, the intersection is at `key.pointList[i]`  
If this is a tuple `(i-1, i)`, the intersection is between `key.pointList[i-1]` and `key.pointList[i]`

### Edge Snapping
The attributes `canvas.edgeSnap` and `canvas.snapAngle` apply to `PolygonObjects` and `PolygonGroups` only:  
If `edgeSnap` is set to `True`, then after a drag or rotate, if an edge of the moved object is within `snapAngle` degrees (default is 10) and `snapDistance` SVG units (default 10) of an edge of another object in the canvas's `objectDict`, the moved object is snapped so that the edges coincide. This can be combined with vertex snapping, if `canvas.vertexSnap` is also set to `True`.



## What was new in previous versions:

## New in version 0.4.0

- New mode `MouseMode.PAN`: in this mode dragging the canvas pans the viewport.  
- `import polygoncanvas` introduces a lot of new functionality relating to intersecting or touching polygons - see section **"Polygon Testing"** below.  
- Zero-install option - brySVG can now be used simply by including one line in your HTML file.  See below for details.


## New in version 0.2.0

- Support for touch screens, including larger, "finger-sized" handles and more touch-friendly selection of thin lines.  
- Redesigned mouse transformations, now using handles on a bounding-box.  
- The module is now split into several files, for faster imports if only a subset of the full functionality is needed.
- More consistent API; all methods now follow the DOM convention of camelCase eg `canvas.addObject(obj)`
- `Button`, `ImageButton`, (multiline) `TextObject`, and `WrappingTextObject` added.
