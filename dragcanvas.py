#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014-2018 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License version 2 as published by #
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,     #
# MA 02111-1307 USA                                                           #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY. See the GNU General Public License for more details.          #
import time
from browser import document, alert
import browser.svg as svg
from math import sin, cos, atan2, pi, hypot
svgbase = svg.svg()
mouseDetected = False
lasttaptime = 0

class Enum(list):
    def __init__(self, name, string):
        values = string.split()
        for i, value in enumerate(values):
            setattr(self, value, i)
            self.append(i)

MouseMode = Enum('MouseMode', 'NONE DRAG TRANSFORM DRAW EDIT')
TransformType = Enum('TransformType', 'NONE TRANSLATE ROTATE XSTRETCH YSTRETCH ENLARGE')
Position = Enum ('Position', 'CONTAINS INSIDE OVERLAPS EQUAL DISJOINT')

class TransformMixin(object):
    '''Provides methods for objects to be cloned, translated, rotated, stretched or enlarged.
    Note that if no mouse interaction is needed with the objects after the transformation, it is better to use the
    translateElement, rotateElement, scaleElement methods provided by the CanvasObject, as they are much faster.'''

    def cloneObject(self):
        '''Returns a clone of an object, including the extra functionality provided by this module.
        If that functionality is not needed, it is better to call the DOM method cloneNode(object) on the CanvasObject,
        as that is much faster'''
        newobject = self.__class__()
        if isinstance(newobject, GroupObject):
            newobject.ObjectList = []
            for obj in self.ObjectList:
                newobj = obj.cloneObject()
                newobject.addObject(newobj)
        elif isinstance(self, PointObject):
            newobject.XY = self.XY
        else:
            newobject.pointList = self.pointList[:]
            if isinstance(self, BezierMixin): newobject.pointsetList = self.pointsetList[:]
        if hasattr(self, "angle"): newobject.angle = self.angle
        for (key, value) in self.attrs.items():
            newobject.attrs[key] = value
        return newobject

    def transformedpointlist(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        newpointlist = []
        for point in self.pointList:
            (pt.x, pt.y) = point
            pt =  pt.matrixTransform(matrix)
            newpointlist.append(Point((pt.x, pt.y)))
        return newpointlist

class NonBezierMixin(object):
    pass

class PolyshapeMixin(object):
    pass

class BezierMixin(object):
    pass

class SmoothBezierMixin(BezierMixin):
    '''Extra methods for SmoothBezierObject and SmoothClosedBezierObject.'''
    def calculatecontrolpoints(self, points):
        [(x1, y1), (x2, y2), (x3, y3)] = points
        (dx1, dy1) = ((x2-x1), (y2-y1))
        (dx3, dy3) = ((x2-x3), (y2-y3))
        d1 = hypot(dx1, dy1)
        d2 = hypot(dx3, dy3)
        if d1 == 0 or d2 == 0: return ((x2, y2), (x2, y2))
        cos1, sin1 = dx1/d1, dy1/d1
        cos2, sin2 = dx3/d2, dy3/d2

        (c1x, c1y) = (x2 - d1*(cos1-cos2)/2, y2 - d1*(sin1-sin2)/2)
        (c2x, c2y) = (x2 + d2*(cos1-cos2)/2, y2 + d2*(sin1-sin2)/2)
        c1 = ((c1x+x2)/2, (c1y+y2)/2)
        c2 = ((c2x+x2)/2, (c2y+y2)/2)
        return (Point(c1), Point(c2))

class LineObject(svg.line, TransformMixin, NonBezierMixin):
    def __init__(self, pointlist=[(0,0), (0,0)], style="solid", linecolour="black", linewidth=1, fillcolour=None):
        [(x1, y1), (x2, y2)] = pointlist

        if style == "faintdash1":
            dasharray = "10,5"
            linecolour = "grey"
        elif style == "faintdash2":
            dasharray = "2,2"
            linecolour = "lightgrey"
        else:
            dasharray = None

        svg.line.__init__(self, x1=x1, y1=y1, x2=x2, y2=y2, style={"stroke":linecolour, "strokeDasharray":dasharray, "strokeWidth":linewidth})
        self.pointList = [Point(coords) for coords in pointlist]

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        self.attrs["x1"] = x1
        self.attrs["y1"] = y1
        self.attrs["x2"] = x2
        self.attrs["y2"] = y2

class TextObject(svg.text):
    def __init__(self, string, anchorpoint, anchorposition=1, fontsize=12, style="normal", ignorescaling=False, canvas=None):
        (x, y) = anchorpoint
        stringlist = string.split("\n")
        rowcount = len(stringlist)
        if anchorposition in [3, 6, 9]:
            horizpos = "end"
        elif anchorposition in [2, 5, 8]:
            horizpos = "middle"
        else:
            horizpos = "start"
        if ignorescaling and canvas and "viewBox" in canvas.attrs:
            fontsize = fontsize*canvas.scaleFactor
        if anchorposition in [1, 2, 3]:
            yoffset = fontsize
        elif anchorposition in [4, 5, 6]:
            yoffset = fontsize*(1-rowcount/2)
        else:
            yoffset = fontsize*(1-rowcount)

        svg.text.__init__(self, stringlist[0], x=x, y=y+yoffset, font_size=fontsize, text_anchor=horizpos)
        #canvas <= self
        for s in stringlist[1:]:
            self <= svg.tspan(s, x=x, dy=fontsize)

class WrappingTextObject(svg.text):
    def __init__(self, canvas, string, anchorpoint, width, anchorposition=1, fontsize=12, style="normal", ignorescaling=False):
        (x, y) = anchorpoint
        if ignorescaling and "viewBox" in canvas.attrs:
            fontsize = fontsize*canvas.scaleFactor
        words = string.split()
        svg.text.__init__(self, "", x=x, font_size=fontsize)
        canvas <= self
        tspan = svg.tspan(words.pop(0), x=x, dy=0)
        self <= tspan
        rowcount = 1
        for word in words:
            tspan.text += " "+word
            if tspan.getComputedTextLength() > width:
                tspan.text = tspan.text[:-len(word)-1]
                tspan = svg.tspan(word, x=x, dy=fontsize)
                self <= tspan
                rowcount += 1

        if anchorposition in [3, 6, 9]:
            horizpos = "end"
        elif anchorposition in [2, 5, 8]:
            horizpos = "middle"
        else:
            horizpos = "start"
        self.attrs["text-anchor"] = horizpos
        if anchorposition in [1, 2, 3]:
            yoffset = fontsize
        elif anchorposition in [4, 5, 6]:
            yoffset = fontsize*(1-rowcount/2)
        else:
            yoffset = fontsize*(1-rowcount)
        self.attrs["y"] = y+yoffset

class PolylineObject(svg.polyline, TransformMixin, NonBezierMixin, PolyshapeMixin):
    '''Wrapper for SVG polyline. Parameter:
    pointlist: a list of coordinates for the vertices'''
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour=None):
        svg.polyline.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.pointList = [Point(coords) for coords in pointlist]
        self.update()

    def update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.pointList])

class PolygonObject(svg.polygon, TransformMixin, NonBezierMixin, PolyshapeMixin):
    '''Wrapper for SVG polygon. Parameter:
    pointlist: a list of coordinates for the vertices'''
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.polygon.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.pointList = [Point(coords) for coords in pointlist]
        self.update()

    def update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.pointList])

class RectangleObject(svg.rect, TransformMixin, NonBezierMixin):
    '''Wrapper for SVG rect.  Parameters:
    pointlist: a list of coordinates for two opposite vertices
    angle: an optional angle of rotation (clockwise, in degrees).'''
    def __init__(self, pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.rect.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.pointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.update()

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        #print((x1, y1), (x2, y2))
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        t = svgbase.createSVGTransform()
        t.setRotate(self.angle, cx, cy)
        self.transform.baseVal.initialize(t)
        self.rotatestring = self.attrs["transform"]

        basepointlist = self.transformedpointlist(t.matrix.inverse())
        [(x1, y1), (x2, y2)] = basepointlist
        #print((x1, y1), (x2, y2))
        self.attrs["x"] = x2 if x2<x1 else x1
        self.attrs["y"] = y2 if y2<y1 else y1
        self.attrs["width"] = abs(x2-x1)
        self.attrs["height"] = abs(y2-y1)

class EllipseObject(svg.ellipse, TransformMixin, NonBezierMixin):
    '''Wrapper for SVG ellipse.  Parameters:
    pointlist: a list of coordinates for two opposite vertices of the bounding box,
    and an optional angle of rotation (clockwise, in degrees).'''
    def __init__(self, pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.ellipse.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.pointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.update()

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        t = svgbase.createSVGTransform()
        t.setRotate(self.angle, cx, cy)
        self.transform.baseVal.initialize(t)
        self.rotatestring = self.attrs["transform"]

        basepointlist = self.transformedpointlist(t.matrix.inverse())
        [(x1, y1), (x2, y2)] = basepointlist
        self.attrs["cx"]=(x1+x2)/2
        self.attrs["cy"]=(y1+y2)/2
        self.attrs["rx"]=abs(x2-x1)/2
        self.attrs["ry"]=abs(y2-y1)/2

class CircleObject(svg.circle, TransformMixin, NonBezierMixin):
    '''Wrapper for SVG circle. Parameters:
    EITHER  centre and radius,
    OR pointlist: a list of two points: the centre, and any point on the circumference.'''
    def __init__(self, centre=(0,0), radius=0, pointlist=None, linecolour="black", linewidth=1, fillcolour="yellow"):
        if pointlist:
            self.pointList = [Point(coords) for coords in pointlist]
        else:
            (x, y) = centre
            self.pointList = [Point((x, y)), Point((x+radius, y))]
        svg.circle.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.update()

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        self.attrs["cx"]=x1
        self.attrs["cy"]=y1
        self.attrs["r"]=hypot(x2-x1, y2-y1)

class BezierObject(svg.path, BezierMixin, TransformMixin):
    '''Wrapper for svg path element.  Parameter:
    pointsetlist: a list of tuples, each tuple consisting of three points:
    (previous-control-point, vertex, next-control-point).
    For the first vertex, the previous-control-point must be None,
    and for the last vertex, the next-control-point must be None.'''
    def __init__(self, pointsetlist=None, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour=None):
        def toPoint(coords):
            return None if coords is None else Point(coords)
        svg.path.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        if pointsetlist:
            self.pointList = [Point(pointset[1]) for pointset in pointsetlist]
        else:
            self.pointList = [Point(coords) for coords in pointlist]
            pointsetlist = self.getpointsetlist(self.pointList)
        self.pointsetList = [[toPoint(coords) for coords in pointset] for pointset in pointsetlist]
        self.update()

    def getpointsetlist(self, pointlist):
        pointsetlist = [(None, pointlist[0], (pointlist[0]+pointlist[1])/2)]
        for i in range(1, len(pointlist)-1):
            pointsetlist.append(((pointlist[i-1]+pointlist[i])/2, pointlist[i], (pointlist[i]+pointlist[i+1])/2))
        pointsetlist.append(((pointlist[-2]+pointlist[-1])/2, pointlist[-1], None))
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = [[None]+self.pointList, self.pointList+[None]]
        else:
            self.pointsetList[-1] = ((self.pointList[-1]+self.pointList[-2])/2, self.pointList[-1], None)
            self.pointsetList[-2] = ((self.pointList[-3]+self.pointList[-2])/2, self.pointList[-2], (self.pointList[-1]+self.pointList[-2])/2)

    def update(self):
        (dummy, (x1, y1), (c1x, c1y)) = self.pointsetList[0]
        ((c2x, c2y), (x2, y2), dummy) = self.pointsetList[-1]
        self.plist = ["M", x1, y1, "C", c1x, c1y]+[x for p in self.pointsetList[1:-1] for c in p for x in c]+[c2x, c2y, x2, y2]
        self.attrs["d"] = " ".join(str(x) for x in self.plist)

class ClosedBezierObject(svg.path, BezierMixin, TransformMixin):
    '''Wrapper for svg path element.  Parameter:
    pointsetlist: a list of tuples, each tuple consisting of three points:
    (previous-control-point, vertex, next-control-point).
    The path will be closed (the first vertex does not need to be repeated).'''
    def __init__(self, pointsetlist=None, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.path.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        if pointsetlist:
            self.pointList = [Point(pointset[1]) for pointset in pointsetlist]
        else:
            self.pointList = [Point(coords) for coords in pointlist]
            pointsetlist = self.getpointsetlist(self.pointList)
        self.pointsetList = [[Point(coords) for coords in pointset] for pointset in pointsetlist]
        self.update()

    def getpointsetlist(self, pointlist):
        pointsetlist = [((pointlist[0]+pointlist[-1])/2, pointlist[0], (pointlist[0]+pointlist[1])/2)]
        for i in range(1, len(pointlist)-1):
            pointsetlist.append(((pointlist[i-1]+pointlist[i])/2, pointlist[i], (pointlist[i]+pointlist[i+1])/2))
        pointsetlist.append(((pointlist[-2]+pointlist[-1])/2, pointlist[-1], (pointlist[0]+pointlist[-1])/2))
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = self.getpointsetlist(self.pointList)
        else:
            self.pointsetList[0] = ((self.pointList[-1]+self.pointList[0])/2, self.pointList[0], (self.pointList[1]+self.pointList[0])/2)
            self.pointsetList[-1] = ((self.pointList[-1]+self.pointList[-2])/2, self.pointList[-1], (self.pointList[-1]+self.pointList[0])/2)
            self.pointsetList[-2] = ((self.pointList[-3]+self.pointList[-2])/2, self.pointList[-2], (self.pointList[-1]+self.pointList[-2])/2)

    def update(self):
        ((c1x, c1y), (x, y), (c2x, c2y)) = self.pointsetList[0]
        self.plist = ["M", x, y, "C", c2x, c2y] + [x for p in self.pointsetList[1:] for c in p for x in c] + [c1x, c1y, x, y]
        self.attrs["d"] = " ".join(str(x) for x in self.plist)

class SmoothBezierObject(SmoothBezierMixin, BezierObject):
    '''Wrapper for svg path element.  Parameter:
    pointlist: a list of vertices.
    Control points will be calculated automatically so that the curve is smooth at each vertex.'''
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour=None):
        self.pointList = [Point(coords) for coords in pointlist]
        pointsetlist = self.getpointsetlist(self.pointList)
        BezierObject.__init__(self, pointsetlist, linecolour=linecolour, linewidth=linewidth, fillcolour=fillcolour)

    def getpointsetlist(self, pointlist):
        if len(pointlist) == 2: return [[None]+pointlist, pointlist+[None]]
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            if i == 1:
                pointsetlist = [(None, pointlist[0], (pointlist[0]+c1)/2)]
            pointsetlist.append((c1, pointlist[i], c2))
        pointsetlist.append(((pointlist[-1]+c2)/2, pointlist[-1], None))
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = [[None]+self.pointList, self.pointList+[None]]
        else:
            (c1, c2) = self.calculatecontrolpoints(self.pointList[-3:])
            self.pointsetList[-1] = ((self.pointList[-1]+c2)/2, self.pointList[-1], None)
            self.pointsetList[-2] = (c1, self.pointList[-2], c2)

class SmoothClosedBezierObject(SmoothBezierMixin, ClosedBezierObject):
    '''Wrapper for svg path element.  Parameter:
    pointlist: a list of vertices.
    The path will be closed (the first vertex does not need to be repeated).
    Control points will be calculated automatically so that the curve is smooth at each vertex.'''
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        self.pointList = [Point(coords) for coords in pointlist]
        pointsetlist = self.getpointsetlist(self.pointList)
        ClosedBezierObject.__init__(self, pointsetlist, linecolour=linecolour, linewidth=linewidth, fillcolour=fillcolour)

    def getpointsetlist(self, pointlist):
        pointlist = [pointlist[-1]]+pointlist[:]+[pointlist[0]]
        pointsetlist = []
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            pointsetlist.append((c1, pointlist[i], c2))
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = self.getpointsetlist(self.pointList)
        else:
            L = len(self.pointList)
            pointlist = self.pointList[:]+self.pointList[:2]
            for j in range(L-2, L+1):
                (c1, c2) = self.calculatecontrolpoints(pointlist[j-1:j+2])
                self.pointsetList[j%L] = (c1, pointlist[j], c2)

class PointObject(svg.circle, TransformMixin):
    '''A point (small circle) on a diagram. Parameters:
    XY: the coordinates of the point,
    pointsize: (optional) the radius of the point.'''
    def __init__(self, XY=(0,0), colour="black", pointsize=2, canvas=None):
        (x, y) = XY
        sf = canvas.scaleFactor if canvas else 1
        svg.circle.__init__(self, cx=x, cy=y, r=pointsize*sf, style={"stroke":colour, "strokeWidth":1, "fill":colour})
        self._XY = None
        self.XY = Point(XY)

    def update(self):
        pass

    @property
    def XY(self):
        return self._XY

    @XY.setter
    def XY(self, XY):
        self._XY = Point(XY)
        self.attrs["cx"] = self._XY[0]
        self.attrs["cy"] = self._XY[1]

class RegularPolygon(PolygonObject):
    '''A regular polygon.  Parameters:
    sidecount: the number of sides
    EITHER centre: the centre of the polygon, OR startpoint: the coordinates of a vertex at the top of the polygon
    EITHER radius: the radius of the polygon, OR sidelength: the length of each side
    offsetangle: (optional) the angle (in degrees, clockwise) by which the top edge of the polygon is rotated from the horizontal.'''

    def __init__(self, sidecount, centre=None, radius=None, startpoint=None, sidelength=None, offsetangle=0, linecolour="black", linewidth=1, fillcolour="yellow"):
        angle = 2*pi/sidecount
        radoffset = offsetangle*pi/180
        if not radius: radius = sidelength/(2*sin(pi/sidecount))
        if not centre:
            (x, y) = startpoint
            centre = (x-radius*sin(radoffset), y+radius*cos(radoffset))
        (cx, cy) = centre
        self.pointList = []
        for i in range(sidecount):
            t = radoffset+i*angle
            self.pointList.append(Point((cx+radius*sin(t), cy-radius*cos(t))))
        PolygonObject.__init__(self, self.pointList, linecolour, linewidth, fillcolour)

class GroupObject(svg.g, TransformMixin):
    '''Wrapper for SVG g element. Parameters:
    objlist: list of the objects to include in the group
    id: (optional) id to identify the element in the DOM'''
    def __init__(self, objlist=[], objid=None):
        svg.g.__init__(self)
        if objid: self.attrs["id"] = objid
        if not isinstance(objlist, list): objlist = [objlist]
        self.ObjectList = []
        for obj in objlist:
            self.addObject(obj)
        self._Canvas = None
        self.Group = None

    def addObject(self, svgobject):
        self <= svgobject
        svgobject.Group = self
        self.ObjectList.append(svgobject)

    def deleteAll(self):
        while self.firstChild:
            self.removeChild(self.firstChild)
        self.ObjectList = []

    @property
    def canvas(self):
        return self._canvas

    @canvas.setter
    def canvas(self, canvas):
        self._canvas = canvas
        for obj in self.ObjectList:
            obj.canvas = canvas

class Button(GroupObject):
    def __init__(self, position, size, text, onclick, fontsize=None, fillcolour="yellow"):
        (x, y), (width, height) = position, size
        button = RectangleObject([(x,y),(x+width, y+height)], fillcolour=fillcolour)
        button.attrs["rx"] = height/3
        rowcount = text.count("\n") + 1
        if not fontsize: fontsize = height*0.8/rowcount
        text = TextObject(text,(x+width/2,y+height/2-fontsize/6),anchorposition=5, fontsize=fontsize)
        self <= [button, text]
        self.bind("click", onclick)
        self.bind("touchstart", onclick)
        self.attrs["cursor"] = "pointer"

class ImageButton(GroupObject):
    def __init__(self, position, size, image, onclick, fillcolour="yellow"):
        (x, y), (width, height) = position, size
        button = RectangleObject([(x,y),(x+width, y+height)], fillcolour=fillcolour)
        button.attrs["rx"] = height/3
        image.attrs["transform"] = "translate({},{})".format(x+width/2, y+height/2)
        self <= [button, image]
        self.bind("click", onclick)
        self.bind("touchstart", onclick)
        self.attrs["cursor"] = "pointer"

class CanvasObject(svg.svg):
    '''Wrapper for SVG svg element.  Parameters:
    width, height: NB these are the CSS properties, so can be given as percentages, or vh, vw units etc.
                    (to set the SVG attributes which are in pixels, call canvas.setDimensions() after creating the object.)
    colour: the background colour
    id: the DOM id

    After creation, there are various attributes which control how the canvas responds to mouse actions:

    canvas.mouseMode = MouseMode.TRANSFORM
        ***Clicking on an object and dragging carries out the transformation
        which has been set using canvas.setMouseTransformType().  This can be:
        TransformType.NONE, TransformType.TRANSLATE, TransformType.ROTATE, TransformType.XSTRETCH, TransformType.YSTRETCH, TransformType.ENLARGE
        canvas.snap: set to a number of pixels. After a transform, if a vertex of the transformed object is within
            this many pixels of a vertex of another object in the canvas's objectdict, the transformed object is snapped
            so that the vertices coincide. (If more than one pair of vertices are below the snap threshold, the closest pair are used.
            If canvas.snap is set to None (the default), no snapping will be done.
        canvas.rotateSnap: set to a number of degrees. After a transform, if a snap is to be done, and the edges
            of the two shapes at the vertex to be snapped are within this many degrees of each other,
            the transformed shape will be rotated so that the edges coincide.
            If canvas.rotateSnap is set to None (the default), no rotating will be done.

    canvas.mouseMode = MouseMode.DRAW
        Shapes can be drawn on the canvas by clicking, moving, clicking again...
        A shape is completed by double-clicking.
        The shape which will be drawn is chosen by setting canvas.tool, which can be:
        line, polygon, polyline, rectangle, ellipse, circle, bezier, closedbezier, smoothbezier, smoothclosedbezier
        The stroke, stroke-width and fill of the shape are set by canvas.penColour, canvas.penWidth, and canvas.fillColour

    canvas.mouseMode = MouseMode.EDIT
        Clicking on a shape causes "handles" to be displayed, which can be used to edit the shape.
        (For Bezier shapes there are also "control handles" to control the curvature.)
        While a shape is selected, pressing the DEL key on the keyboard will delete the shape.
        canvas.selectedObject is the shape curently being edited.
        Use canvas.deselectObject to stop editing a shape and hide the handles.

    canvas.mouseMode = MouseMode.NONE
        No user interaction with the canvas.
    '''

    def __init__(self, width, height, colour="white", id=None):
        svg.svg.__init__(self, style={"width":width, "height":height, "backgroundColor":colour})
        if id: self.id = id
        self.scaleFactor = 1
        #self.shapetypes = {"line":LineObject, "polygon":PolygonObject, "polyline":PolylineObject,
        #"rectangle":RectangleObject, "ellipse":EllipseObject, "circle":CircleObject,
        #"bezier":BezierObject, "closedbezier":ClosedBezierObject, "smoothbezier":SmoothBezierObject, "smoothclosedbezier":SmoothClosedBezierObject}
        self.cursors = ["auto", "move", "url(brySVG/rotate.png), auto", "col-resize", "row-resize", "url(brySVG/enlarge.png), auto"]
        self.objectdict = {}
        self.mouseMode = MouseMode.DRAG
        self.transformTypes = TransformType
        self.mouseDetected = False
        #self.setMouseTransformType(TransformType.NONE)
        self.mouseOwner = None
        self.selectedObject = None
        self.transformorigin = None
        self.transformBBox = RectangleObject(linecolour="blue", fillcolour=None)
        self.transformHandles = []
        self.handles = None
        self.controlhandles  = None
        self.selectedhandle = None
        self.hittargets = []
        self.snap = None
        self.rotateSnap = None
        self.tool = "select"
        self.penColour = "black"
        self.fillColour  = "yellow"
        self.penWidth = 3
        self.bind("mousedown", self.onMouseDown)
        self.bind("mousemove", self.onMouseMove)
        self.bind("mouseup", self.onLeftUp)
        self.bind("touchstart", self.onTouchStart)
        self.bind("touchmove", self.onMouseMove)
        self.bind("touchend", self.onLeftUp)
        self.bind("dragstart", self.onDragStart)
        self.bind("dblclick", self.onDoubleClick)
        document.bind("keydown", self.deleteSelection)

    def setDimensions(self):
        '''If the canvas was created using non-pixel dimensions (eg percentages),
        call this after creation to set the SVG width and height attributes.'''
        bcr = self.getBoundingClientRect()
        self.attrs["width"] = bcr.width
        self.attrs["height"] = bcr.height

    def fitContents(self):
        '''Scales the canvas so that all the objects on it are visible.'''
        bbox = self.getBBox()
        bboxstring = str(bbox.x-10)+" "+str(bbox.y-10)+" "+str(bbox.width+20)+" "+str(bbox.height+20)
        self.attrs["viewBox"] = bboxstring
        self.scaleFactor = self.getScaleFactor()
        #self.attrs["preserveAspectRatio"] = "none"

    def getScaleFactor(self):
        bcr = self.getBoundingClientRect()
        vbleft, vbtop, vbwidth, vbheight = [float(x) for x in self.attrs["viewBox"].split()]
        self <= RectangleObject([(vbleft, vbtop), (vbleft+vbwidth, vbtop+vbheight)], 0, "red", 1, None)
        return max(vbwidth/bcr.width, vbheight/bcr.height)

    def getSVGcoords(self, event):
        '''Converts mouse event coordinates to SVG coordinates'''
        x = event.changedTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.changedTouches[0].clientY if "touch" in event.type else event.clientY
        pt = self.createSVGPoint()
        (pt.x, pt.y) = (x, y)
        SVGpt =  pt.matrixTransform(self.getScreenCTM().inverse())
        return Point((SVGpt.x, SVGpt.y))

    def addObject(self, svgobject, objid=None, fixed=False):
        '''Adds an object to the canvas, and also adds it to the canvas's objectdict so that it can be referenced
        using canvas.objectdict[id]. This is also needed for the object to be capable of being snapped to.
        (Note that referencing using document[id] will only give the SVG element, not the Python object.)
        If it is not desired that an object should be in the objectdict, just add it to the canvas using Brython's <= method.'''
        def AddToDict(svgobj, fixed):
            if not svgobj.id: svgobj.id = "id"+str(len(self.objectdict))
            self.objectdict[svgobj.id] = svgobj
            svgobj.Fixed = fixed
            if isinstance(svgobj, GroupObject):
                for obj in svgobj.ObjectList:
                    AddToDict(obj, fixed)
        if objid: svgobject.id = objid
        self <= svgobject
        AddToDict(svgobject, fixed)
        svgobject.canvas = self
        return svgobject

    def deleteObject(self, svgobject):
        if not svgobject: return
        self.removeChild(svgobject)
        try:
            del self.objectdict[svgobject.id]
        except (AttributeError, KeyError):
            pass

    def deleteAll(self):
        '''Clear all elements from the canvas'''
        while self.firstChild:
            self.removeChild(self.firstChild)
        self.objectdict = {}

    def deleteSelection(self,event):
        #print (event.target, event.currentTarget)
        if event.keyCode == 46:
            if self.selectedObject:
                if self.handles: self.deleteObject(self.handles)
                if self.controlhandles: self.deleteObject(self.controlhandles)
                self.deleteObject(self.selectedObject)
                self.selectedObject = self.handles = self.controlhandles = None

    def rotateElement(self, element, angle, centre=None):
        '''Rotate an element clockwise by angle degrees around centre.
        If centre is not given, it is the centre of the object's bounding box.'''

        if not centre:
            bbox = element.getBBox()
            centre = (bbox.x+bbox.width/2, bbox.y+bbox.height/2)
        t = svgbase.createSVGTransform()
        t.setRotate(angle, *centre)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def translateElement(self, element, vector):
        '''Translate an element by vector.'''
        t = svgbase.createSVGTransform()
        t.setTranslate(*vector)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def scaleElement(self, element, xscale, yscale=None):
        '''Enlarge or stretch an element by scale factors xscale and yscale, with centre (0, 0).
        If yscale is not given, it is equal to xscale, ie the element is enlarged without stretching.'''
        if not yscale: yscale = xscale
        t = svgbase.createSVGTransform()
        t.setScale(xscale, yscale)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def setMouseMode(self, mm):
        self.mouseMode = mm
        if mm != MouseMode.DRAW:
            self.tool = "select"
        if mm in [MouseMode.DRAG, MouseMode.EDIT, MouseMode.TRANSFORM]:
            for obj in self.objectdict.values():
                if obj.style.fill != "none" or obj.Fixed: continue
                if hasattr(obj, "hitTarget"): continue
                if hasattr(obj, "reference"): continue # A hitTarget doesn't need its own hitTarget
                newobj = obj.cloneObject()
                newobj.style.strokeWidth = 10*self.scaleFactor if self.mouseDetected else 25*self.scaleFactor
                #newobj.style.strokeWidth = 25*self.scaleFactor
                newobj.style.opacity = 0.2
                newobj.reference = obj
                obj.hitTarget = newobj
                self.hittargets.append(newobj)
                self.addObject(newobj)
    """
    def setMouseTransformType(self, mtt):
        '''Set canvas.MouseTransformType and show the appropriate cursor.'''
        self.MouseTransformType = mtt
        self.style.cursor = self.cursors[mtt]
    """
    def onRightClick(self, event):
        event.preventDefault()

    def onDragStart(self, event):
        event.preventDefault()

    def onTouchStart(self, event):
        event.preventDefault()
        global lasttaptime
        latesttaptime = time.time()
        if latesttaptime - lasttaptime < 0.3:
            for function in self.events("dblclick"):
                function(event)
        else:
            self.onLeftDown(event)
        lasttaptime = latesttaptime

    def onMouseDown(self, event):
        if not self.mouseDetected:
            self.mouseDetected = True
            for obj in self.objectdict.values():
                if hasattr(obj, "reference"):
                    obj.style.strokeWidth = 10*self.scaleFactor
        if event.button > 0: return
        self.onLeftDown(event)

    def onLeftDown(self, event):
        #event.preventDefault()
        if self.mouseMode == MouseMode.DRAG:
            self.prepareDrag(event)
        elif self.mouseMode == MouseMode.TRANSFORM:
            self.prepareTransform(event)
        elif self.mouseMode == MouseMode.DRAW:
            self.drawPoint(event)
        elif self.mouseMode == MouseMode.EDIT:
            self.prepareEdit(event)

    def onMouseMove(self, event):
        event.preventDefault()
        if not self.mouseOwner: return
        if self.mouseMode == MouseMode.DRAG:
            self.doDrag(event)
        else:
            self.movePoint(event)

    def onLeftUp(self, event):
        if event.type == "mouseup" and event.button > 0: return
        if not self.mouseOwner: return
        if self.mouseMode == MouseMode.DRAG:
            self.endDrag(event)
        elif self.mouseMode == MouseMode.TRANSFORM:
            self.endTransform(event)
            self.mouseOwner = None
        elif self.mouseMode == MouseMode.EDIT:
            self.endEdit(event)

    def onDoubleClick(self,event):
        if self.mouseMode == MouseMode.DRAW: self.endDraw(event)

    def prepareDrag(self, event):
        self.mouseOwner = self.selectedObject = self.getSelectedObject(event.target.id)
        if not self.mouseOwner or self.mouseOwner.Fixed: return
        self.StartPoint = self.getSVGcoords(event)
        self.startx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        self.starty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY

    def doDrag(self, event):
        x = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        dx, dy = (x-self.startx)*self.scaleFactor, (y-self.starty)*self.scaleFactor
        self.mouseOwner.attrs["transform"] = "translate({},{})".format(dx, dy)
        if isinstance(self.mouseOwner, [EllipseObject, RectangleObject]):
            self.mouseOwner.attrs["transform"] += self.mouseOwner.rotatestring

    def endDrag(self, event):
        self.mouseOwner.attrs["transform"] = ""
        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.StartPoint
        tt = time.time()
        self.translateObject(self.mouseOwner, offset)
        #print(time.time()-tt)
        if self.snap:
            if self.rotateSnap: self.doRotateSnap(self.mouseOwner)
            else: self.doSnap(self.mouseOwner)
        self.mouseOwner = None

    def getSelectedObject(self, objectid, getGroup = True):
        try:
            svgobj = self.objectdict[objectid]
        except KeyError:
            return
        try:
            svgobj = svgobj.reference
        except AttributeError:
            pass
        if getGroup:
            while getattr(svgobj, "Group", None):
                svgobj = svgobj.Group
        return svgobj

    def doSnap(self, svgobject):
        #tt = time.time()
        if not hasattr(svgobject, "pointList"): return
        bbox = svgobject.getBBox()
        L, R, T, B = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
        bestdx = bestdy = None
        for objid in self.objectdict:
            if objid == svgobject.id: continue
            obj = self.objectdict[objid]
            if not hasattr(obj, "pointList"): continue
            bbox = obj.getBBox()
            L1, R1, T1, B1 = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
            if L1-R > self.snap or R1-L < -self.snap or T1-B > self.snap or B1-T < -self.snap: continue
            for point1 in obj.pointList:
                for point2 in svgobject.pointList:
                    (dx, dy) = point1 - point2
                    if abs(dx) < self.snap and abs(dy) < self.snap:
                        if not bestdx or hypot(dx, dy) < hypot(bestdx, bestdy):
                            (bestdx, bestdy) = (dx, dy)
        if bestdx or bestdy:
            self.translateObject(svgobject, Point((bestdx, bestdy)))
        #print("snap", time.time()-tt)

    def translateObject(self, svgobject, offset):
        offset = Point(offset)
        if isinstance(svgobject, GroupObject):
            for obj in svgobject.ObjectList:
                self.translateObject(obj, offset)
        elif isinstance(svgobject, PointObject):
            svgobject.XY += offset
        else:
            svgobject.pointList = [point+offset for point in svgobject.pointList]
            if isinstance(svgobject, BezierMixin):
                svgobject.pointsetList = [(p1+offset,p2+offset,p3+offset) for (p1,p2,p3) in svgobject.pointsetList]
            svgobject.update()
            hittarget = getattr(svgobject, "hitTarget", None)
            if hittarget:
                hittarget.pointList = svgobject.pointList
                if isinstance(svgobject, BezierMixin): hittarget.pointsetList = svgobject.pointsetList
                hittarget.update()

class Point(object):
    '''Class to represent coordinates and also give some vector functionality'''
    def __init__(self, coords):
        self.coords = coords.coords if isinstance(coords, Point) else list(coords)

    def __str__(self):
        return str(tuple(self.coords))

    def __add__(self, other):
        if isinstance(other, Point):
            return Point([xi+yi for (xi, yi) in zip(self.coords, other.coords)])
        elif isinstance(other, (list, tuple)):
            return Point([xi+yi for (xi, yi) in zip(self.coords, other)])
        elif other is None:
            return None
        else:
            return NotImplemented

    def __radd__(self, other):
        return self + other

    def __iadd__(self, other):
        if isinstance(other, (list, tuple)):
            for i in range(len(self.coords)):
                self.coords[i] += other[i]
        else:
            for i in range(len(self.coords)):
                self.coords[i] += other.coords[i]
        return self

    def __sub__(self, other):
        return Point([xi-yi for (xi, yi) in zip(self.coords, other.coords)])

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Point([other*xi for xi in self.coords])
        elif isinstance(other, (list, tuple)):
            return Point([xi*yi for (xi, yi) in zip(self.coords, other)])
        elif isinstance(other, Point):
            return sum([xi*yi for (xi, yi) in zip(self.coords, other.coords)])
        elif isinstance(other, Matrix):
            return Point([self*col for col in other.cols])
        else:
            return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return Point([other*xi for xi in self.coords])
        elif isinstance(other, (list, tuple)):
           return Point([xi*yi for (xi, yi) in zip(self.coords, other)])
        elif isinstance(other, Point):
            return sum([xi*yi for (xi, yi) in zip(self.coords, other.coords)])
        else:
            return NotImplemented

    def __truediv__(self, other):
        return Point([xi/other for xi in self.coords])

    def __getitem__(self, i):
        return self.coords[i]

    def __len__(self):
        return len(self.coords)

    def length(self):
        (x, y) = self.coords
        return hypot(x, y)

    def angle(self):
        return atan2(self.coords[1], self.coords[0])
