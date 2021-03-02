#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014-2020 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License version 2 as published by #
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,     #
# MA 02111-1307 USA                                                           #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY. See the GNU General Public License for more details.          #
import time
from browser import document, alert, window
import browser.svg as svg
from math import sin, cos, atan2, pi, hypot, floor, log10
svgbase = svg.svg()
basepoint = svgbase.createSVGPoint()
lasttaptime = 0
fixeddefault = False

class Enum(list):
    def __init__(self, name, string):
        values = string.split()
        for i, value in enumerate(values):
            setattr(self, value, i)
            self.append(i)

MouseMode = Enum('MouseMode', 'NONE DRAG TRANSFORM DRAW EDIT PAN')
TransformType = Enum('TransformType', 'NONE TRANSLATE ROTATE XSTRETCH YSTRETCH ENLARGE')
Position = Enum ('Position', 'CONTAINS INSIDE OVERLAPS EQUAL DISJOINT')

class ObjectMixin(object):
    '''Methods applicable to all svgobjects defined in this module.  The main one is the cloneObject method.'''

    def cloneObject(self):
        '''Returns a clone of an object, including the extra functionality provided by this module.
        If that functionality is not needed, it is better to call the DOM method cloneNode(object) on the CanvasObject,
        as that is much faster'''
        if isinstance(self, GroupObject):
            newobject = self.__class__()
            for obj in self.objectList:
                if isinstance(obj, ObjectMixin):
                    newobj = obj.cloneObject()
                    newobject <= newobj
                    newobj.group = newobject
                    newobject.objectList.append(newobj)
        elif isinstance(self, ObjectMixin):
            newobject = self.__class__()
            for attrname in ["XY", "pointList", "pointsetList", "angle", "fixed"]:
                attr = getattr(self, attrname, "NO_SUCH_ATTRIBUTE")
                if attr == "NO_SUCH_ATTRIBUTE": continue
                newattr = list(attr) if isinstance(attr, list) else attr
                setattr(newobject, attrname, newattr)
        else:
            return None

        for (key, value) in self.attrs.items():
            newobject.attrs[key] = value
        newobject.id = ""
        return newobject

    def setStyle(self, attribute, value):
        '''Utility function, can be overridden for specific types of object'''
        self.style = {attribute:value}

    def __repr__(self):
        return f"{self.__class__}{self.id}"

    def updatehittarget(self):
        '''Not intended to be called by end users.'''
        hittarget = getattr(self, "hitTarget", None)
        if hittarget:
            hittarget.pointList = self.pointList
            if isinstance(self, BezierObject): hittarget.pointsetList = self.pointsetList
            hittarget.update()

    def transformedpointlist(self, matrix):
        '''Not intended to be called by end users.'''
        newpointlist = []
        for point in self.pointList:
            (basepoint.x, basepoint.y) = point
            newpt =  basepoint.matrixTransform(matrix)
            newpointlist.append(Point((newpt.x, newpt.y)))
        return newpointlist

class SmoothBezierMixin(object):
    '''Extra methods for SmoothBezierObject and SmoothClosedBezierObject.'''
    def calculatecontrolpoints(self, points):
        '''Not intended to be called by end users.'''
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

class LineObject(svg.line, ObjectMixin):
    '''A wrapper for SVG line.'''
    def __init__(self, pointlist=[(0,0), (0,0)], style="solid", linecolour="black", linewidth=1, fillcolour="none", objid=None):
        [(x1, y1), (x2, y2)] = pointlist

        if style == "faintdash1":
            dasharray = "10,5"
            linecolour = "grey"
        elif style == "faintdash2":
            dasharray = "2,2"
            linecolour = "lightgrey"
        else:
            dasharray = None

        svg.line.__init__(self, x1=x1, y1=y1, x2=x2, y2=y2, style={"stroke":linecolour, "strokeDasharray":dasharray, "stroke-width":linewidth})
        self.pointList = [Point(coords) for coords in pointlist]
        if objid: self.id = objid

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        self.attrs["x1"] = x1
        self.attrs["y1"] = y1
        self.attrs["x2"] = x2
        self.attrs["y2"] = y2

class TextObject(svg.text, ObjectMixin):
    '''A multiline textbox.  Use "\n" within string to separate lines. To make sure the font-size is not affected by the scaling of the
    canvas, set ignorescaling to True, and specify the canvas on which the object will be placed.
    The box is placed at the coordinates given by anchorpoint; the anchorposition can be from 1 to 9:
    1  2  3  ie if anchorposition is 1, the anchorpoint is top-left, if it is 5 it is in the centre of the box, etc
    4  5  6
    7  8  9'''
    def __init__(self, string="", anchorpoint=(0,0), anchorposition=1, fontsize=12, style="normal", ignorescaling=False, canvas=None):
        (x, y) = anchorpoint
        stringlist = string.split("\n")
        rowcount = len(stringlist)
        if anchorposition in [3, 6, 9]:
            horizpos = "end"
        elif anchorposition in [2, 5, 8]:
            horizpos = "middle"
        else:
            horizpos = "start"
        lineheight = fontsize*1.2
        if ignorescaling and canvas:
            fontsize *= canvas.scaleFactor
            lineheight *= canvas.scaleFactor
        if anchorposition in [1, 2, 3]:
            yoffset = fontsize
        elif anchorposition in [4, 5, 6]:
            yoffset = fontsize*(1-rowcount/2)
        else:
            yoffset = fontsize*(1-rowcount)

        svg.text.__init__(self, stringlist[0], x=x, y=y+yoffset, font_size=fontsize, text_anchor=horizpos)
        for s in stringlist[1:]:
            self <= svg.tspan(s, x=x, dy=lineheight)

class WrappingTextObject(svg.text):
    '''See TextObject above for explanation of most of the parameters; however, note that canvas must be specified.
    A width in SVG units is also specified, and text will be wrapped at word boundaries to fit that width.'''
    def __init__(self, canvas, string, anchorpoint, width, anchorposition=1, fontsize=12, style="normal", ignorescaling=False):
        (x, y) = anchorpoint
        lineheight = fontsize*1.2
        if ignorescaling:
            fontsize *= canvas.scaleFactor
            lineheight *= canvas.scaleFactor
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
                tspan = svg.tspan(word, x=x, dy=lineheight)
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

class PolylineObject(svg.polyline, ObjectMixin):
    '''Wrapper for SVG polyline. Parameter:
    pointlist: a list of coordinates for the vertices'''
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="none", objid=None):
        svg.polyline.__init__(self, style={"stroke":linecolour, "stroke-width":linewidth, "fill":fillcolour})
        self.pointList = [Point(coords) for coords in pointlist]
        self.update()
        if objid: self.id = objid

    def update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.pointList])

class PolygonObject(svg.polygon, ObjectMixin):
    '''Wrapper for SVG polygon. Parameter:
    pointlist: a list of coordinates for the vertices'''
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow", objid=None):
        svg.polygon.__init__(self, style={"stroke":linecolour, "stroke-width":linewidth, "fill":fillcolour})
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in pointlist])
        if objid: self.id = objid

    def update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self._pointList])

    def __repr__(self):
        return f"polygon {self.id}" if self.id else f"polygon {id(self)}"

    def __str__(self):
        return self.__repr__()

    @property
    def pointList(self):
        if getattr(self, "_pointList", None) is None:
            #print(f"calculating pointList for {self}")
            P = self.points
            L = P.numberOfItems
            self._pointList = [Point([P.getItem(i).x, P.getItem(i).y]) for i in range(L)]
        return self._pointList

    @pointList.setter
    def pointList(self, pointlist):
        self._pointList = [Point(coords) for coords in pointlist]
        self.update()

    def cloneObject(self):
        newobject = self.__class__()
        for (key, value) in self.attrs.items():
            newobject.attrs[key] = value
        newobject.id = ""

        P = self.points
        P2 = newobject.points
        L = P.numberOfItems
        P2.clear()
        for i in range(L):
            pt = P.getItem(i)
            P2.appendItem(pt)

        return newobject

    def transformpoints(self, points, matrix):
        L = points.numberOfItems
        for i in range(L):
            pt = points.getItem(i)
            newpt =  pt.matrixTransform(matrix)
            points.replaceItem(newpt, i)

class RectangleObject(svg.rect, ObjectMixin):
    '''Wrapper for SVG rect.  Parameters:
    pointlist: a list of coordinates for two opposite vertices
    angle: an optional angle of rotation (clockwise, in degrees).'''
    def __init__(self, pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow", objid=None):
        svg.rect.__init__(self, style={"stroke":linecolour, "stroke-width":linewidth, "fill":fillcolour})
        self.pointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.update()
        if objid: self.id = objid

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        self.rotatestring = self.style.transform = f"rotate({self.angle}deg)"
        self.style.transformOrigin = f"{cx}px {cy}px"

        t = svgbase.createSVGTransform()
        t.setRotate(-self.angle, cx, cy)
        basepointlist = self.transformedpointlist(t.matrix)
        [(x1, y1), (x2, y2)] = basepointlist
        self.attrs["x"] = x2 if x2<x1 else x1
        self.attrs["y"] = y2 if y2<y1 else y1
        self.attrs["width"] = abs(x2-x1)
        self.attrs["height"] = abs(y2-y1)

class EllipseObject(svg.ellipse, ObjectMixin):
    '''Wrapper for SVG ellipse.  Parameters:
    pointlist: a list of coordinates for two opposite vertices of the bounding box,
    and an optional angle of rotation (clockwise, in degrees).'''
    def __init__(self, pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow", objid=None):
        svg.ellipse.__init__(self, style={"stroke":linecolour, "stroke-width":linewidth, "fill":fillcolour})
        self.pointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.update()
        if objid: self.id = objid

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        self.rotatestring = self.style.transform = f"rotate({self.angle}deg)"
        self.style.transformOrigin = f"{cx}px {cy}px"

        t = svgbase.createSVGTransform()
        t.setRotate(-self.angle, cx, cy)
        basepointlist = self.transformedpointlist(t.matrix)
        [(x1, y1), (x2, y2)] = basepointlist
        self.attrs["cx"]=(x1+x2)/2
        self.attrs["cy"]=(y1+y2)/2
        self.attrs["rx"]=abs(x2-x1)/2
        self.attrs["ry"]=abs(y2-y1)/2

class CircleObject(svg.circle, ObjectMixin):
    '''Wrapper for SVG circle. Parameters:
    EITHER  centre and radius,
    OR pointlist: a list of two points: the centre, and any point on the circumference.'''
    def __init__(self, centre=(0,0), radius=0, pointlist=None, linecolour="black", linewidth=1, fillcolour="yellow", objid=None):
        if pointlist:
            self.pointList = [Point(coords) for coords in pointlist]
        else:
            (x, y) = centre
            self.pointList = [Point((x, y)), Point((x+radius, y))]
        svg.circle.__init__(self, style={"stroke":linecolour, "stroke-width":linewidth, "fill":fillcolour})
        self.update()
        if objid: self.id = objid

    def update(self):
        [(x1, y1), (x2, y2)] = self.pointList
        self.attrs["cx"]=x1
        self.attrs["cy"]=y1
        self.attrs["r"]=hypot(x2-x1, y2-y1)

class UseObject(svg.use, ObjectMixin):
    '''Wrapper for SVG use.  Parameters:
    topleft: coordinates of the top left point of the shape's bounding box
    angle: an optional angle of rotation (clockwise, in degrees).'''
    def __init__(self, href, origin=(0,0), angle=0, objid=None):
        svg.use.__init__(self, href=href)
        (self.attrs["x"], self.attrs["y"]) = origin
        self.origin = Point(origin)
        self.angle = angle
        if objid: self.id = objid

    def getPointList(self):
        bbox = self.getBBox()
        self.pointList = [(bbox.x, bbox.y), (bbox.x+bbox.width, bbox.y+bbox.height)]
        [(x1, y1), (x2, y2)] = self.pointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        t = svgbase.createSVGTransform()
        t.setRotate(self.angle, cx, cy)
        self.pointList = self.transformedpointlist(t.matrix)

    def update(self):
        (self.attrs["x"], self.attrs["y"]) = self.origin
        [(x1, y1), (x2, y2)] = self.pointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        self.rotatestring = self.style.transform = f"rotate({self.angle}deg)"
        self.style.transformOrigin = f"{cx}px {cy}px"

class BezierObject(svg.path, ObjectMixin):
    '''Wrapper for svg path element.  Parameter:
    EITHER pointlist: a list of coordinates for the vertices (in which case the edges will initially be straight lines)
    OR  pointsetlist: a list of tuples, each tuple consisting of three points:
    (previous-control-point, vertex, next-control-point).
    For the first vertex, the previous-control-point must be None,
    and for the last vertex, the next-control-point must be None.'''
    def __init__(self, pointsetlist=None, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="none", objid=None):
        def toPoint(coords):
            return None if coords is None else Point(coords)
        svg.path.__init__(self, style={"stroke":linecolour, "stroke-width":linewidth, "fill":fillcolour})
        if pointsetlist:
            self.pointList = [Point(pointset[1]) for pointset in pointsetlist]
        else:
            self.pointList = [Point(coords) for coords in pointlist]
            pointsetlist = self.getpointsetlist(self.pointList)
        self.pointsetList = [[toPoint(coords) for coords in pointset] for pointset in pointsetlist]
        self.update()
        if objid: self.id = objid

    def getpointsetlist(self, pointlist):
        pointsetlist = [[None, pointlist[0], (pointlist[0]+pointlist[1])/2]]
        for i in range(1, len(pointlist)-1):
            pointsetlist.append([(pointlist[i-1]+pointlist[i])/2, pointlist[i], (pointlist[i]+pointlist[i+1])/2])
        pointsetlist.append([(pointlist[-2]+pointlist[-1])/2, pointlist[-1], None])
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = [[None]+self.pointList, self.pointList+[None]]
        else:
            cpoint = (self.pointList[-1]+self.pointList[-2])/2
            self.pointsetList[-1] = [cpoint, self.pointList[-1], None]
            self.pointsetList[-2][2] = cpoint

    def update(self):
        (dummy, (x1, y1), (c1x, c1y)) = self.pointsetList[0]
        ((c2x, c2y), (x2, y2), dummy) = self.pointsetList[-1]
        self.plist = ["M", x1, y1, "C", c1x, c1y]+[x for p in self.pointsetList[1:-1] for c in p for x in c]+[c2x, c2y, x2, y2]
        self.attrs["d"] = " ".join(str(x) for x in self.plist)

class ClosedBezierObject(BezierObject):
    '''Wrapper for svg path element.  Parameter:
    EITHER pointlist: a list of coordinates for the vertices (in which case the edges will initially be stright lines)
    OR  pointsetlist: a list of tuples, each tuple consisting of three points:
    (previous-control-point, vertex, next-control-point).
    The path will be closed (the first vertex does not need to be repeated).'''
    def __init__(self, pointsetlist=None, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow", objid=None):
        svg.path.__init__(self, style={"stroke":linecolour, "stroke-width":linewidth, "fill":fillcolour})
        if pointsetlist:
            self.pointList = [Point(pointset[1]) for pointset in pointsetlist]
        else:
            self.pointList = [Point(coords) for coords in pointlist]
            pointsetlist = self.getpointsetlist(self.pointList)
        self.pointsetList = [[Point(coords) for coords in pointset] for pointset in pointsetlist]
        self.update()
        if objid: self.id = objid

    def getpointsetlist(self, pointlist):
        pointsetlist = [[(pointlist[0]+pointlist[-1])/2, pointlist[0], (pointlist[0]+pointlist[1])/2]]
        for i in range(1, len(pointlist)-1):
            pointsetlist.append([(pointlist[i-1]+pointlist[i])/2, pointlist[i], (pointlist[i]+pointlist[i+1])/2])
        pointsetlist.append([(pointlist[-2]+pointlist[-1])/2, pointlist[-1], (pointlist[0]+pointlist[-1])/2])
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = self.getpointsetlist(self.pointList)
        else:
            cpoint1, cpoint2 = (self.pointList[-1]+self.pointList[-2])/2, (self.pointList[-1]+self.pointList[0])/2
            self.pointsetList[-1] = (cpoint1, self.pointList[-1], cpoint2)
            self.pointsetList[-2][2] = cpoint1
            self.pointsetList[0][0] = cpoint2

    def update(self):
        ((c1x, c1y), (x, y), (c2x, c2y)) = self.pointsetList[0]
        self.plist = ["M", x, y, "C", c2x, c2y] + [x for p in self.pointsetList[1:] for c in p for x in c] + [c1x, c1y, x, y]
        self.attrs["d"] = " ".join(str(x) for x in self.plist)

class SmoothBezierObject(SmoothBezierMixin, BezierObject):
    '''Wrapper for svg path element.  Parameter:
    pointlist: a list of vertices.
    Control points will be calculated automatically so that the curve is smooth at each vertex.'''
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="none", objid=None):
        self.pointList = [Point(coords) for coords in pointlist]
        pointsetlist = self.getpointsetlist(self.pointList)
        BezierObject.__init__(self, pointsetlist, linecolour=linecolour, linewidth=linewidth, fillcolour=fillcolour, objid=objid)

    def getpointsetlist(self, pointlist):
        if len(pointlist) == 2: return [[None]+pointlist, pointlist+[None]]
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            if i == 1:
                pointsetlist = [[None, pointlist[0], (pointlist[0]+c1)/2]]
            pointsetlist.append([c1, pointlist[i], c2])
        pointsetlist.append([(pointlist[-1]+c2)/2, pointlist[-1], None])
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = [[None]+self.pointList, self.pointList+[None]]
        else:
            (c1, c2) = self.calculatecontrolpoints(self.pointList[-3:])
            self.pointsetList[-1] = [(self.pointList[-1]+c2)/2, self.pointList[-1], None]
            self.pointsetList[-2] = [c1, self.pointList[-2], c2]

class SmoothClosedBezierObject(SmoothBezierMixin, ClosedBezierObject):
    '''Wrapper for svg path element.  Parameter:
    pointlist: a list of vertices.
    The path will be closed (the first vertex does not need to be repeated).
    Control points will be calculated automatically so that the curve is smooth at each vertex.'''
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow", objid=None):
        self.pointList = [Point(coords) for coords in pointlist]
        pointsetlist = self.getpointsetlist(self.pointList)
        ClosedBezierObject.__init__(self, pointsetlist, linecolour=linecolour, linewidth=linewidth, fillcolour=fillcolour, objid=objid)

    def getpointsetlist(self, pointlist):
        pointlist = [pointlist[-1]]+pointlist[:]+[pointlist[0]]
        pointsetlist = []
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            pointsetlist.append([c1, pointlist[i], c2])
        return pointsetlist

    def updatepointsetlist(self):
        if len(self.pointList) == 2:
            self.pointsetList = self.getpointsetlist(self.pointList)
        else:
            L = len(self.pointList)
            pointlist = self.pointList[:]+self.pointList[:2]
            for j in range(L-2, L+1):
                (c1, c2) = self.calculatecontrolpoints(pointlist[j-1:j+2])
                self.pointsetList[j%L] = [c1, pointlist[j], c2]

class PointObject(svg.circle, ObjectMixin):
    '''A point (small circle) on a diagram. Parameters:
    XY: the coordinates of the point,
    pointsize: (optional) the radius of the point.'''
    def __init__(self, XY=(0,0), colour="black", pointsize=2, canvas=None, objid=None):
        (x, y) = XY
        sf = canvas.scaleFactor if canvas else 1
        svg.circle.__init__(self, cx=x, cy=y, r=pointsize*sf, style={"stroke":colour, "stroke-width":1, "fill":colour, "vector-effect":"non-scaling-stroke"})
        self._XY = None
        self.XY = Point(XY)
        if objid: self.id = objid

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
    def __init__(self, sidecount=0, centre=None, radius=None, startpoint=None, sidelength=None, offsetangle=0, linecolour="black", linewidth=1, fillcolour="yellow", objid=None):
        pointlist = []
        if sidecount>0:
            angle = 2*pi/sidecount
            radoffset = offsetangle*pi/180
            if not radius: radius = sidelength/(2*sin(pi/sidecount))
            if not centre:
                (x, y) = startpoint
                centre = (x-radius*sin(radoffset), y+radius*cos(radoffset))
            (cx, cy) = centre
            for i in range(sidecount):
                t = radoffset+i*angle
                pointlist.append(Point((cx+radius*sin(t), cy-radius*cos(t))))
        PolygonObject.__init__(self, pointlist, linecolour, linewidth, fillcolour, objid)

class GroupObject(svg.g, ObjectMixin):
    '''Wrapper for SVG g element. Parameters:
    objlist: list of the objects to include in the group
    objid: (optional) id to identify the element in the DOM'''
    def __init__(self, objlist=[], objid=None):
        svg.g.__init__(self)
        if not isinstance(objlist, list): objlist = [objlist]
        self.objectList = []
        self._canvas = None
        for obj in objlist:
            self.addObject(obj)
        if objid: self.id = objid

    def addObject(self, svgobject, objid=None):
        canvas = self.canvas
        if canvas is not None: canvas.addObject(svgobject, objid)
        if objid: svgobject.id = objid
        self <= svgobject
        svgobject.group = self
        self.objectList.append(svgobject)

    def addObjects(self, objectlist):
        canvas = self.canvas
        for obj in objectlist:
            if canvas is not None: canvas.addObject(obj)
            self <= obj
            obj.group = self
            self.objectList.append(obj)

    def update(self):
        pass

    def removeObject(self, svgobject):
        '''Remove an object from the group'''
        if not self.contains(svgobject): return
        self.removeChild(svgobject)
        self.objectList.remove(svgobject)
        svgobject.group = None
        try: #If the group is on the canvas, the object needs removing from the canvas's objectDict
            del self.canvas.objectDict[svgobject.id]
        except (AttributeError, KeyError):
            pass

    def deleteAll(self):
        if self.canvas:
            for obj in self.objectList: del self.canvas.objectDict[obj.id]
        while self.firstChild: self.removeChild(self.firstChild)
        self.objectList = []

    def setStyle(self, attribute, value):
        for obj in self.objectList:
            obj.setStyle(attribute, value)

    @property
    def canvas(self):
        return self._canvas

    @canvas.setter
    def canvas(self, canvas):
        self._canvas = canvas
        for obj in self.objectList: obj.canvas = canvas

    @property
    def fixed(self):
        return self._fixed

    @fixed.setter
    def fixed(self, fixedvalue):
        self._fixed = fixedvalue
        for obj in self.objectList: obj.fixed = fixedvalue

class Button(GroupObject):
    '''A clickable button with (multiline) text on it. If fontsize is not specified, the text will be scaled to fit
    the height (but not width) of the button. The onclick parameter is the function which handles the event.'''
    def __init__(self, position, size, text, onclick, fontsize=None, fillcolour="lightgrey", canvas=None, objid=None):
        GroupObject.__init__(self)
        if objid: self.id = objid
        (x, y), (width, height) = position, size
        self.button = RectangleObject([(x,y),(x+width, y+height)], fillcolour=fillcolour)
        self.button.attrs["rx"] = height/3
        rowcount = text.count("\n") + 1
        if not fontsize: fontsize = height*0.75/rowcount
        self.label = TextObject(text,(x+width/2,y+height/2-fontsize/6),anchorposition=5, fontsize=fontsize)
        self.addObjects([self.button, self.label])
        self.fixed = True
        self.bind("mousedown", self.onMouseDown)
        self.bind("mouseup", self.onMouseUp)
        self.bind("click", onclick)
        self.bind("touchstart", onclick)
        self.attrs["cursor"] = "pointer"

    def onMouseDown(self, event):
        event.stopPropagation()

    def onMouseUp(self, event):
        event.stopPropagation()

    def setBackgroundColour(self, colour):
        self.button.style.fill = colour

class ImageButton(GroupObject):
    '''A clickable button with an SVG image on it. The centre of the image should be at (0,0).
    If the canvas is specified, the image will be scaled to fit inside the button.
    The onclick parameter is the function which handles the event.'''
    def __init__(self, position, size, image, onclick, fontsize=None, fillcolour="lightgrey", canvas=None, objid=None):
        GroupObject.__init__(self)
        if objid: self.id = objid
        (x, y), (width, height) = position, size
        self.button = RectangleObject([(x,y),(x+width, y+height)], fillcolour=fillcolour)
        self.button.attrs["rx"] = height/3
        image.style.transform = f"translate({x+width/2}px,{y+height/2}px)"
        if canvas:
            canvas <= image
            bbox = image.getBBox()
            canvas.removeChild(image)
            scalefactor = min(width/bbox.width, height/bbox.height)*0.7
            image.style.transform += f" scale({scalefactor})"
        self.addObjects([self.button, image])
        self.fixed = True
        self.bind("mousedown", self.onMouseDown)
        self.bind("click", onclick)
        self.bind("touchstart", onclick)
        self.attrs["cursor"] = "pointer"

    def onMouseDown(self, event):
        event.stopPropagation()

    def setBackgroundColour(self, colour):
        self.button.style.fill = colour

class Definitions(svg.defs):
    def __init__(self, objlist=[], filename=None):
        svg.defs.__init__(self)
        if filename:
            self.innerHTML = open(filename).read()
        for obj in objlist: self <= obj

class CanvasObject(svg.svg):
    '''Wrapper for SVG svg element.  Parameters:
    width, height: NB these are the CSS properties, so can be given as percentages, or vh, vw units etc.
                    (to set the SVG attributes which are in pixels, call canvas.setDimensions() after creating the object.)
    colour: the background colour
    objid: the DOM id

    To add objects to the canvas, use canvas.addObject.
    Objects are stored in canvas.objectDict using their id as the dictionary key. (if not supplied, ids are made up.)
    After creation, there are various attributes which control how the canvas responds to mouse actions:

    canvas.mouseMode = MouseMode.PAN
        Dragging the canvas pans the viewport.

    canvas.mouseMode = MouseMode.DRAG
        Objects can be dragged around on the canvas.
        canvas.vertexSnap and canvas.snapDistance: If vertexSnap is set to True, then after a drag, if a vertex of the
        dragged object is within snapDistance (default is 10) pixels of a vertex of another object in the canvas's objectDict,
        the dragged object is snapped so that the vertices coincide.
        (If more than one pair of vertices are below the snap threshold, the closest pair are used.)

    canvas.mouseMode = MouseMode.TRANSFORM
        ***To enable this mode, use import transformcanvas, import polygoncanvas or import fullcanvas instead of import dragcanvas***
        Objects can be dragged around on the canvas.  In addition, clicking on an object shows a bounding box
        and a number of handles (which ones can be controlled by setting canvas.transformTypes to the list of transforms
        required. By default, canvas.transformTypes includes:
        [TransformType.TRANSLATE, TransformType.ROTATE, TransformType.XSTRETCH, TransformType.YSTRETCH, TransformType.ENLARGE]

    canvas.mouseMode = MouseMode.DRAW
        ***To enable this mode, use import drawcanvas or import fullcanvas instead of import dragcanvas***
        Shapes can be drawn on the canvas by clicking, moving, clicking again...
        A shape is completed by double-clicking, which also switches the canvas to MouseMode.EDIT (see below).
        The shape which will be drawn is chosen by setting canvas.tool, which can be:
        line, polygon, polyline, rectangle, ellipse, circle, bezier, closedbezier, smoothbezier, smoothclosedbezier
        The stroke, stroke-width and fill of the shape are set by canvas.penColour, canvas.penWidth, and canvas.fillColour.

    canvas.mouseMode = MouseMode.EDIT
        ***To enable this mode, use import drawcanvas or import fullcanvas instead of import dragcanvas***
        Clicking on a shape causes "handles" to be displayed, which can be used to edit the shape.
        (For Bezier shapes clicking on a handle causes "control handles" to be displayed, to control the curvature.)
        While a shape is selected, pressing the DEL key on the keyboard will delete the shape.
        Clicking elsewhere on the canvas deselects the shape.

    canvas.mouseMode = MouseMode.NONE
        No user interaction with the canvas.
    '''

    def __init__(self, width=None, height=None, colour="white", objid=None):
        svg.svg.__init__(self, style={"backgroundColor":colour})
        if width: self.style.width = width
        if height: self.style.height = height
        self.id = objid if objid else f"canvas{id(self)}"
        self.objectDict = {} # See above
        #Attributes intended to be read/write for users - see above for usage
        self.mouseMode = MouseMode.NONE
        self.transformTypes = TransformType
        self.vertexSnap = False
        self.snapDistance = 10
        self.edgeSnap = False
        self.snapAngle = 10
        self.tool = "select"
        self.penColour = "black"
        self.fillColour  = "yellow"
        self.penWidth = 3
        self.lineWidthScaling = True #If False, line thicknesses do not change when zooming in

        #Attributes intended to be read-only for users
        self.scaleFactor = 1 #Multiply by this to convert CSS pixels to SVG units
        self.mouseDetected = False #If false, indicates a touchscreen device
        self.mouseOwner = None #The object (shape or handle) durrently being dragged
        self.selectedObject = None #The shape which was last clicked on or dragged

        #Attributes not intended to be used by end-users
        self.panning = False
        self.nextid = 0
        self.objectDict = {}
        self.hittargets = []
        self.handles = None
        self.controlhandles  = None
        self.transformHandles = []
        self.selectedhandle = None
        self.transformorigin = None
        self.transformBBox = RectangleObject(linecolour="blue", fillcolour="none")
        self.transformBBox.style.vectorEffect = "non-scaling-stroke"
        self.rotateLine = LineObject(linecolour="blue")
        self.rotateLine.style.vectorEffect = "non-scaling-stroke"

        self.bind("mousedown", self.onMouseDown)
        self.bind("mousemove", self.onMouseMove)
        self.bind("mouseup", self.onLeftUp)
        self.bind("touchstart", self.onTouchStart)
        self.bind("touchmove", self.onMouseMove)
        self.bind("touchend", self.onLeftUp)
        self.bind("dragstart", self.onDragStart)
        self.bind("dblclick", self.onDoubleClick)
        document.bind("keydown", self.onKeyDown)
        self.bind("click", self.onClick)
        self.bind("touchstart", self.onClick)

    def setViewBox(self, pointlist):
        '''Should be done after the canvas has been added to the page.
        pointlist is the coordinates of the desired top-left and bottom-right of the canvas
        Returns the SVG coords of the actual top-left and bottom right of the canvas
        (which will usually be different dues to the need to preserve the aspect ratio).'''
        ((x1, y1), (x2, y2)) = pointlist
        self.attrs["viewBox"] = f"{x1} {y1} {x2-x1} {y2-y1}"
        self.viewBoxRect = [Point((x1, y1)), Point((x2, y2))]
        self.centre = Point(((x1+x2)/2, (y1+y2)/2))
        self.scaleFactor = self.getScaleFactor()
        bcr = self.getBoundingClientRect()
        pt = self.createSVGPoint()
        (pt.x, pt.y) = (bcr.left, bcr.top)
        SVGpt =  pt.matrixTransform(self.getScreenCTM().inverse())
        (x1, y1) = (SVGpt.x, SVGpt.y)
        (pt.x, pt.y) = (bcr.left+bcr.width, bcr.top+bcr.height)
        SVGpt =  pt.matrixTransform(self.getScreenCTM().inverse())
        (x2, y2) = (SVGpt.x, SVGpt.y)
        self.viewWindow = [Point((x1, y1)), Point((x2, y2))]
        return self.viewWindow

    def setDimensions(self):
        '''If the canvas was created using non-pixel dimensions (eg percentages),
        call this after adding to the page to set the SVG width and height attributes.'''
        bcr = self.getBoundingClientRect()
        self.attrs["width"] = bcr.width
        self.attrs["height"] = bcr.height
        return bcr.width, bcr.height

    def fitContents(self):
        '''Scales the canvas so that all the objects on it are visible. Returns the coords of the top-left and bottom-right.'''
        bbox = self.getBBox()
        wmargin, hmargin = bbox.width/50, bbox.height/50
        rectpointlist = self.setViewBox(((bbox.x-wmargin, bbox.y-hmargin), (bbox.x+bbox.width+wmargin, bbox.y+bbox.height+hmargin)))
        #self.attrs["preserveAspectRatio"] = "none"
        return rectpointlist

    def getScaleFactor(self):
        '''Recalculates self.scaleFactor. This is called automatically by setViewBox or fitContents(),
        but should be called manually after zooming in or out of the canvas in some other way.'''
        width, height = self.setDimensions()
        vbleft, vbtop, vbwidth, vbheight = [float(x) for x in self.attrs["viewBox"].split()]
        return max(vbwidth/width, vbheight/height)

    def getSVGcoords(self, event):
        '''Converts mouse event coordinates to SVG coordinates'''
        x = event.changedTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.changedTouches[0].clientY if "touch" in event.type else event.clientY
        pt = self.createSVGPoint()
        (pt.x, pt.y) = (x, y)
        SVGpt =  pt.matrixTransform(self.getScreenCTM().inverse())
        return Point((SVGpt.x, SVGpt.y))

    def addObject(self, svgobject, objid=None, fixed=fixeddefault):
        '''Adds an object to the canvas, and also adds it to the canvas's objectDict so that it can be referenced
        using canvas.objectDict[id]. This is also needed for the object to be capable of being snapped to.
        If the object should not be capable of being dragged or transformed with mouse actions, set `fixed` to True.
        (Note that referencing using document[id] will only give the SVG element, not the Python object.)
        If it is not desired that an object should be in the objectDict, just add it to the canvas using Brython's <= method.'''
        def AddToDict(svgobj):
            if not svgobj.id:
                svgobj.id = f"{self.id}_id{self.nextid}"
                self.nextid += 1
            self.objectDict[svgobj.id] = svgobj
            if not getattr(svgobj.style, "vectorEffect", None): #If object already has vectorEffect set, leave it alone
                if self.lineWidthScaling is False: svgobj.style.vectorEffect = "non-scaling-stroke" #Only set property if necessary
            if isinstance(svgobj, GroupObject):
                for obj in svgobj.objectList:
                    AddToDict(obj)
        if objid: svgobject.id = objid
        if not hasattr(svgobject, "fixed"): svgobject.fixed = fixed
        self <= svgobject
        AddToDict(svgobject)
        svgobject.canvas = self
        if isinstance(svgobject, UseObject):
            svgobject.getPointList()
            svgobject.update()
        return svgobject

    def deleteObject(self, svgobject):
        '''Delete an object from the canvas'''
        def deletefromdict(svgobj):
            if isinstance(svgobj, GroupObject):
                for obj in svgobj.objectList:
                    deletefromdict(obj)
            if svgobj.id in self.objectDict: del self.objectDict[svgobj.id]

        if not self.contains(svgobject): return
        self.removeChild(svgobject)
        deletefromdict(svgobject)

    def deleteAll(self, event=None):
        '''Clear all elements from the canvas'''
        while self.firstChild:
            self.removeChild(self.firstChild)
        self.objectDict = {}

    def deleteSelection(self):
        '''Delete the currently selected object'''
        if self.selectedObject:
            if self.handles: self.deleteObject(self.handles)
            if self.controlhandles: self.deleteObject(self.controlhandles)
            hittarget = getattr(self.selectedObject, "hitTarget", None)
            if hittarget: self.deleteObject(hittarget)
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

    def scaleElement(self, element, xscale, yscale=None):
        '''Enlarge or stretch an element by scale factors xscale and yscale, with centre (0, 0).
        If yscale is not given, it is equal to xscale, ie the element is enlarged without stretching.'''
        if not yscale: yscale = xscale
        t = svgbase.createSVGTransform()
        t.setScale(xscale, yscale)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def translateElement(self, element, vector):
        '''Translate an element by vector.'''
        t = svgbase.createSVGTransform()
        t.setTranslate(*vector)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def translateObject(self, svgobject, offset):
        '''Translate an svgobject by offset.  Unlike translateElement, this will also preserve the extra
        functionality provided by this module - ie the shape will still be able to be selected, dragged, etc.'''
        offset = Point(offset)
        if isinstance(svgobject, GroupObject):
            for obj in svgobject.objectList:
                self.translateObject(obj, offset)
            boundary = getattr(svgobject, "boundary", None)
            if boundary: self.translateObject(boundary, offset)
        elif isinstance(svgobject, PointObject):
            svgobject.XY += offset
        else:
            svgobject.pointList = [point+offset for point in svgobject.pointList]
            if isinstance(svgobject, BezierObject):
                svgobject.pointsetList = [(p1+offset,p2+offset,p3+offset) for (p1,p2,p3) in svgobject.pointsetList]
            if isinstance(svgobject, UseObject):
                svgobject.origin += offset
            svgobject.update()
            svgobject.updatehittarget()
            if isinstance(svgobject, PolygonObject): svgobject._segments = None

    #The methods below are not intended to be called by end-users.
    @property
    def mouseMode(self):
        return self._mouseMode

    @mouseMode.setter
    def mouseMode(self, mm):
        currentmm = getattr(self, "_mouseMode", None)
        if currentmm == mm: return
        if currentmm == MouseMode.TRANSFORM: self.hideTransformHandles()
        elif currentmm == MouseMode.EDIT: self.deselectObject()
        self._mouseMode = mm
        self.tool = "select"
        if mm in [MouseMode.DRAG, MouseMode.EDIT, MouseMode.TRANSFORM]:
            try:
                self.createEditHitTargets()
            except AttributeError:
                self.createHitTargets()

    @property
    def lineWidthScaling(self):
        return self._lineWidthScaling

    @lineWidthScaling.setter
    def lineWidthScaling(self, lws):
        currentlws = getattr(self, "_lineWidthScaling", None)
        if currentlws == lws: return
        self._lineWidthScaling = lws
        for objid in self.objectDict:
            objectDict[objid].style.vectorEffect = "none" if lws else "non-scaling-stroke"

    def createHitTargets(self):
        objlist = list(self.objectDict.values())
        for obj in objlist:
            if isinstance(obj, GroupObject): continue
            if hasattr(obj, "hitTarget"): continue
            if hasattr(obj, "reference"): continue # A hitTarget doesn't need its own hitTarget
            if isinstance(obj, UseObject):
                newobj = RectangleObject(obj.pointList, obj.angle)
            elif obj.style.fill != "none" or obj.fixed:
                continue
            else:
                newobj = obj.cloneObject()
            newobj.style.strokeWidth = 10*self.scaleFactor if self.mouseDetected else 25*self.scaleFactor
            newobj.style.opacity = 0
            newobj.reference = obj
            obj.hitTarget = newobj
            self.hittargets.append(newobj)
            self.addObject(newobj)

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
            for obj in self.objectDict.values():
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
        elif self.mouseMode == MouseMode.PAN:
            self.preparePan(event)

    def onMouseMove(self, event):
        event.preventDefault()
        if self.mouseMode == MouseMode.PAN:
            if self.panning: self.doPan(event)
            return
        if not self.mouseOwner: return
        if self.mouseMode == MouseMode.DRAG:
            self.doDrag(event)
        else:
            self.movePoint(event)

    def onLeftUp(self, event):
        if event.type == "mouseup" and event.button > 0: return
        if self.mouseMode == MouseMode.PAN:
            self.endPan(event)
            return
        if not self.mouseOwner: return
        if self.mouseMode == MouseMode.DRAG:
            self.endDrag(event)
        elif self.mouseMode == MouseMode.TRANSFORM:
            self.endTransform(event)
            self.mouseOwner = None
        elif self.mouseMode == MouseMode.EDIT:
            self.endEdit(event)

    def onClick(self, event):
        obj = self.getSelectedObject(event.target.id)
        if obj and hasattr(obj, "hitTarget"):
            obj.dispatchEvent(window.MouseEvent.new("click"))

    def onDoubleClick(self, event):
        if self.mouseMode == MouseMode.DRAW: self.endDraw(event)

    def onKeyDown(self, event):
        if event.keyCode == 46: self.deleteSelection()

    def prepareDrag(self, event):
        self.selectedObject = self.getSelectedObject(event.target.id)
        if self.selectedObject and not self.selectedObject.fixed:
            self.mouseOwner = self.selectedObject
            self <= self.mouseOwner
            if (hittarget := getattr(self.mouseOwner, "hitTarget", None)): self <= hittarget
            self.StartPoint = self.getSVGcoords(event)
            self.startx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
            self.starty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY

    def doDrag(self, event):
        x = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        dx, dy = (x-self.startx)*self.scaleFactor, (y-self.starty)*self.scaleFactor
        self.mouseOwner.style.transform = f"translate({dx}px,{dy}px)"
        if isinstance(self.mouseOwner, [EllipseObject, RectangleObject, UseObject]):
            self.mouseOwner.style.transform += self.mouseOwner.rotatestring

    def endDrag(self, event):
        self.mouseOwner.style.transform = "translate(0px,0px)"
        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.StartPoint
        self.translateObject(self.mouseOwner, offset)
        if self.edgeSnap: self.doEdgeSnap(self.mouseOwner)
        elif self.vertexSnap: self.doVertexSnap(self.mouseOwner)
        self.mouseOwner = None

    def preparePan(self, event):
        x = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        self.startPoint = Point((x, y))
        self.startCentre = self.centre
        self.panStart = self.viewBoxRect
        self.panning = True

    def doPan(self, event):
        x = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        delta = (Point((x, y)) - self.startPoint)*self.scaleFactor
        #self.centre = self.startCentre - delta
        newviewbox = [point-delta for point in self.panStart]
        self.setViewBox(newviewbox)

    def endPan(self, event):
        self.panning = False
        print(f"pan: new centre {self.centre}, new viewbox {self.viewBoxRect}")

    def getSelectedObject(self, objectid, getGroup = True):
        try:
            svgobj = self.objectDict[objectid]
        except KeyError:
            return
        try:
            svgobj = svgobj.reference
        except AttributeError:
            pass
        if getGroup:
            while getattr(svgobj, "group", None):
                svgobj = svgobj.group
        return svgobj

    def doVertexSnap(self, svgobject, checkpoints=None):
        if not hasattr(svgobject, "pointList"): return
        snapd = self.snapDistance
        bestdx = bestdy = bestd = None
        bbox = svgobject.getBBox()
        L, R, T, B = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height

        if checkpoints is None:
            checkpoints = []
            for objid in self.objectDict:
                if objid == svgobject.id: continue
                obj = self.objectDict[objid]
                if not hasattr(obj, "pointList"): continue
                if obj.style.visibility == "hidden": continue
                if objgroup := getattr(obj, "group", None) and hasattr(objgroup, "pointList") : continue
                bbox = obj.getBBox()
                L1, R1, T1, B1 = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
                if L1-R > snapd or R1-L < -snapd or T1-B > snapd or B1-T < -snapd: continue
                checkpoints.extend(obj.pointList)
        if not checkpoints: return
        checkpoints.sort(key=lambda p:p.coords) #all points which could possibly be snapped to
        objpoints = sorted(svgobject.pointList, key=lambda p:p.coords)

        checkstart = 0
        for i, point1 in enumerate(objpoints): #vertical sweepline stops at each x-coord of object to be snapped
            checkpoints = checkpoints[checkstart:] #remove points too far to the left of sweepline
            if not checkpoints: break
            try:
                (tonextx, y) = objpoints[i+1] - point1 #find distance between current and next position of sweepline
            except IndexError:
                tonextx = 0
            checkstart = 0
            for point2 in checkpoints: #start checking
                (dx, dy) = point2 - point1
                if abs(dx) < snapd and abs(dy) < snapd:
                    d = hypot(dx, dy)
                    if bestd is None or d < bestd: (bestd, bestdx, bestdy) = (d, dx, dy)
                if tonextx - dx > snapd: checkstart += 1 #point just checked will be too far to the left when sweepline moves on
                if dx > snapd: break #point just checked is too far to the right of sweepline - time to move sweepline on
        if bestd: self.translateObject(svgobject, (bestdx, bestdy))
        #print("Done vertexSnap", time.time()-tt)

class Point(object):
    '''Class to represent coordinates and also give some vector functionality'''
    def __init__(self, coords):
        self.coords = list(coords.coords) if isinstance(coords, Point) else list(coords)

    def __repr__(self):
        return str(tuple(self.coords))

    def __eq__(self, other):
        return (self.coords == other.coords)

    def __lt__(self, other):
        return self.coords < other.coords

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

    def __hash__(self):
        return hash(tuple(self.coords))

    def __round__(self, n):
        (x, y) = self.coords
        return Point((round(float(x), n), round(float(y), n)))

    def __len__(self):
        return len(self.coords)

    def length(self):
        (x, y) = self.coords
        return hypot(x, y)

    def angle(self):
        return atan2(self.coords[1], self.coords[0])

    def anglefrom(self, other):
        dot = other*self
        cross = other.cross(self)
        if cross == 0: cross = -0.0
        angle = atan2(cross, dot)
        return angle

    def cross(self, other):
        x1, y1 = self.coords
        x2, y2 = other.coords
        return x1*y2 - y1*x2

    def roundsf(self, sf):
        x, y = self.coords
        return Point((roundsf(x, sf), roundsf(y, sf)))

class Matrix(object):
    def __init__(self, rows):
        self.rows = rows
        self.cols = [Point([self.rows[i][j] for i in range(len(self.rows))]) for j in range(len(self.rows[0]))]

    def __str__(self):
        return str("\n".join(str(row) for row in self.rows))

    def __rmul__(self, other):
        if isinstance(other, (list, tuple)):
            return [Point([p*col for col in self.cols]) for p in other]
        else:
            return Point([other*col for col in self.cols])

def roundsf(x, sf=3):
    if x == 0: return 0
    return round(x, sf-int(floor(log10(abs(x))))-1)

shapetypes = {"line":LineObject, "polygon":PolygonObject, "polyline":PolylineObject,
"rectangle":RectangleObject, "ellipse":EllipseObject, "circle":CircleObject,
"bezier":BezierObject, "closedbezier":ClosedBezierObject, "smoothbezier":SmoothBezierObject, "smoothclosedbezier":SmoothClosedBezierObject}
