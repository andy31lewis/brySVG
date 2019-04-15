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
from browser import document
import browser.svg as svg
from math import sin, cos, atan2, pi, hypot
svgbase = svg.svg()

class Enum(list):
    def __init__(self, name, string):
        values = string.split()
        for i, value in enumerate(values):
            setattr(self, value, i)
            self.append(i)

MouseMode = Enum('MouseMode', 'NONE TRANSFORM DRAW EDIT')
TransformType = Enum('TransformType', 'NONE TRANSLATE ROTATE XSTRETCH YSTRETCH ENLARGE')
Position = Enum ('Position', 'CONTAINS INSIDE OVERLAPS EQUAL DISJOINT')

def delete(element):
    element.parentNode.removeChild(element)
    del element

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
                newobject.AddObject(newobj)
        elif isinstance(self, PointObject):
            newobject.XY = self.XY
        elif isinstance(self, BezierMixin):
            newobject.SetPointsets(self.PointsetList)
        else:
            newobject.SetPoints(self.PointList)
        for (key, value) in self.attrs.items():
            newobject.attrs[key] = value
        return newobject

    def transformedPoint(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        (pt.x, pt.y) = self.XY
        pt =  pt.matrixTransform(matrix)
        return Point((pt.x, pt.y))

    def transformedPointList(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        newpointlist = []
        for point in self.PointList:
            (pt.x, pt.y) = point
            pt =  pt.matrixTransform(matrix)
            newpointlist.append(Point((pt.x, pt.y)))
        return newpointlist

    def transformedPointsetList(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        newpointsetlist = []
        for pointset in self.PointsetList:
            newpointset = []
            for point in pointset:
                if point is None:
                    newpointset.append(None)
                else:
                    (pt.x, pt.y) = point
                    pt = pt.matrixTransform(matrix)
                    newpointset.append(Point((pt.x, pt.y)))
            newpointsetlist.append(newpointset)
        return newpointsetlist

    def matrixTransform(self, matrix):
        '''Transform object using a SVGmatrix'''
        if isinstance(self, PointObject):
            self.XY = self.transformedPoint(matrix)
        elif isinstance(self, (BezierObject, ClosedBezierObject)):
            self.PointsetList = self.transformedPointsetList(matrix)
        else:
            self.PointList = self.transformedPointList(matrix)
        self.Update()

    def translate(self, vector):
        '''Translate object by vector'''
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.translate(vector)
        else:
            t = svgbase.createSVGTransform()
            t.setTranslate(*vector)
            self.matrixTransform(t.matrix)

    def rotate(self, angle, centre=None):
        '''Rotate object clockwise by angle degrees around centre.
        If centre is not given, it is the centre of the object's bounding box.'''
        if not centre:
            bbox = self.getBBox()
            centre = (bbox.x+bbox.width/2, bbox.y+bbox.height/2)
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.rotate(angle, centre)
        else:
            if isinstance(self, (EllipseObject, RectangleObject)):
                self.angle += angle
            t = svgbase.createSVGTransform()
            t.setRotate(angle, *centre)
            self.matrixTransform(t.matrix)

    def rotateByVectors(self, vec1, vec2, centre=(0, 0)):
        '''Rotate object clockwise by the angle between vec1 and vec2 around centre.
        If centre is not given, it is the origin.'''
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.rotateByVectors(vec1, vec2, centre)
        else:
            (cx, cy) = centre
            (x1, y1) = vec1
            (x2, y2) = vec2
            (x3, y3) = (x1*x2+y1*y2, x1*y2-x2*y1)
            angle = atan2(y3, x3)*180/pi
            if isinstance(self, (EllipseObject, RectangleObject)):
                self.angle += angle
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix = matrix.rotateFromVector(x3, y3)
            matrix = matrix.translate(-cx, -cy)
            self.matrixTransform(matrix)

    def xstretch(self, xscale, cx=0):
        '''Stretch object in the x-direction by scale factor xscale, with invariant line x = cx.
        If cx is not given, the invariant line is the y-axis.'''
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.xstretch(xscale, cx)
        else:
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(cx, 0)
            matrix.a = xscale
            matrix = matrix.translate(-cx, 0)
            self.matrixTransform(matrix)

    def ystretch(self, yscale, cy=0):
        '''Stretch object in the y-direction by scale factor yscale, with invariant line y = cy.
        If cy is not given, the invariant line is the x-axis.'''
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.ystretch(yscale, cy)
        else:
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(0, cy)
            matrix.d = yscale
            matrix = matrix.translate(0, -cy)
            self.matrixTransform(matrix)

    def enlarge(self, scalefactor, centre):
        '''Enlarge object by scale factor scalefactor, from centre.
        If cx and cy are not given, the centre is the origin.'''
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.enlarge(scalefactor, centre)
        else:
            (cx, cy) = centre
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix = matrix.scale(scalefactor)
            matrix = matrix.translate(-cx, -cy)
            self.matrixTransform(matrix)

class NonBezierMixin(object):
    '''Methods for LineObject, PolylineObject, PolygonObject, CircleObject, EllipseObject and RectangleObject'''
    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.Update()

    def SetPoints(self, pointlist):
        self.PointList = pointlist
        self.Update()

    def movePoint(self, coords):
       self.SetPoint(-1, coords)

    def SelectShape(self):
        if self.Canvas.Tool != "select": return
        if self.Canvas.SelectedShape:
            self.Canvas.DeSelectShape()
        self.Canvas.SelectedShape = self
        self.Handles = GroupObject([Handle(self, i, coords) for i, coords in enumerate(self.PointList)], "handles")
        self.Canvas <= self.Handles

class PolyshapeMixin(object):
    '''Methods for PolylineObject and PolygonObject.'''
    def AppendPoint(self, point):
        self.PointList.append(point)
        self.Update()

    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.Update()

class BezierMixin(object):
    '''Methods for BezierObject and ClosedBezierObject.'''
    def SetPointset(self, i, pointset):
        self.PointsetList[i] = pointset
        self.Update()

    def SetPointsets(self, pointsetlist):
        self.PointsetList = pointsetlist
        self.Update()

    def SelectShape(self):
        if self.Canvas.Tool != "select": return
        if self.Canvas.SelectedShape:
            self.Canvas.DeSelectShape()
        self.Canvas.SelectedShape = self
        pointlist = [pointset[1] for pointset in self.PointsetList]
        self.Handles = GroupObject([Handle(self, i, coords) for i, coords in enumerate(pointlist)], "handles")
        self.Canvas <= self.Handles

        controlhandles = []
        for i, (point0, point1, point2) in enumerate(self.PointsetList):
            if point0 is None: controlhandles.append((ControlHandle(self, i, 2, point2), ))
            elif point2 is None: controlhandles.append((ControlHandle(self, i, 0, point0), ))
            else: controlhandles.append((ControlHandle(self, i, 0, point0), ControlHandle(self, i, 2, point2)))
        self.ControlHandles = controlhandles
        self.ControlHandlesGroup = GroupObject([ch for chset in controlhandles for ch in chset], "controlhandles")
        self.Canvas <= self.ControlHandlesGroup

class SmoothBezierMixin(object):
    '''Methods for SmoothBezierObject and SmoothClosedBezierObject.'''
    def SetPointset(self, i, pointset):
        self.PointList[i] = pointset[1]
        self.PointsetList[i] = pointset
        self.Update()

    def SetPointsets(self, pointsetlist):
        self.PointList = [pointset[1] for pointset in pointsetlist]
        self.PointsetList = pointsetlist
        self.Update()

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

    def SetPoints(self, pointlist):
        self.PointList = pointlist
        self.PointsetList = self.getpointsetlist(pointlist)
        self.Update()

    def AppendPoint(self, point):
        self.PointList.append(point)
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

    def movePoint(self, coords):
       self.SetPoint(-1, coords)

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
        self.PointList = [Point(coords) for coords in pointlist]

    def Update(self):
        [(x1, y1), (x2, y2)] = self.PointList
        self.attrs["x1"] = x1
        self.attrs["y1"] = y1
        self.attrs["x2"] = x2
        self.attrs["y2"] = y2

class TextObject(svg.text):
    def __init__(self, canvas, string, anchorpoint, anchorposition=1, fontsize=12, style="normal", ignorescaling=False):
        (x, y) = anchorpoint
        stringlist = string.split("\n")
        rowcount = len(stringlist)
        if anchorposition in [3, 6, 9]:
            horizpos = "end"
        elif anchorposition in [2, 5, 8]:
            horizpos = "middle"
        else:
            horizpos = "start"
        if ignorescaling and "viewBox" in canvas.attrs:
            bcr = canvas.getBoundingClientRect()
            viewboxsize = [float(x) for x in canvas.attrs["viewBox"].split()[-2:]]
            xscaling, yscaling = viewboxsize[0]/bcr.width, viewboxsize[1]/bcr.height
            fontsize = fontsize*xscaling if xscaling>yscaling else fontsize*yscaling
        if anchorposition in [1, 2, 3]:
            yoffset = fontsize
        elif anchorposition in [4, 5, 6]:
            yoffset = fontsize*(1-rowcount/2)
        else:
            yoffset = fontsize*(1-rowcount)

        svg.text.__init__(self, stringlist[0], x=x, y=y+yoffset, font_size=fontsize, text_anchor=horizpos)
        for s in stringlist[1:]:
            self <= svg.tspan(s, x=x, dy=fontsize)

class WrappingTextObject(svg.text):
    def __init__(self, canvas, string, anchorpoint, width, anchorposition=1, fontsize=12, style="normal", ignorescaling=False):
        (x, y) = anchorpoint
        if ignorescaling and "viewBox" in canvas.attrs:
            bcr = canvas.getBoundingClientRect()
            viewboxsize = [float(x) for x in canvas.attrs["viewBox"].split()[-2:]]
            xscaling, yscaling = viewboxsize[0]/bcr.width, viewboxsize[1]/bcr.height
            fontsize = fontsize*xscaling if xscaling>yscaling else fontsize*yscaling

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
        """
        if ignorescaling and "viewBox" in canvas.attrs:
            bcr = canvas.getBoundingClientRect()
            viewboxsize = [float(x) for x in canvas.attrs["viewBox"].split()[-2:]]
            xscaling, yscaling = viewboxsize[0]/bcr.width, viewboxsize[1]/bcr.height
            fontsize = fontsize*xscaling if xscaling>yscaling else fontsize*yscaling
        """
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
        svg.polyline.__init__(self, fill="none", style={"stroke":linecolour, "strokeWidth":linewidth})
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def Update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

class PolygonObject(svg.polygon, TransformMixin, NonBezierMixin, PolyshapeMixin):
    '''Wrapper for SVG polygon. Parameter:
    pointlist: a list of coordinates for the vertices'''
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.polygon.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def Update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

    def containsPoint(self, point):
        '''Returns "interior" if point is inside the polygon, "edge" if it is on an edge, or False otherwise'''
        (x, y) = point
        length = len(self.PointList)
        counter = 0
        (x1, y1) = self.PointList[0]
        for i in range(1, length+1):
            (x2, y2) = self.PointList[i%length]
            if y1 == y2:
                if y == y1 and min(x1,x2)<=x<=max(x1,x2): return "edge"
            elif min(y1,y2)<y<=max(y1,y2) and x<max(x1, x2):
                xcheck = x1 + (y-y1)*(x2-x1)/(y2-y1)
                if x == xcheck: return "edge"
                elif x < xcheck:
                    counter += 1
            (x1, y1) = (x2, y2)
        return "interior" if counter%2 == 1 else False

    def area(self):
        '''Returns the area of the polygon'''
        return self._area(self.PointList)

    def isEqual(self, other):
        '''Returns True if the polygon is identical to other, False otherwise.
        other is another PolygonObject'''
        return self._equalPolys(self.PointList, other.Pointlist)

    def getBoundingBox(self):
        return self._getboundingbox(self.PointList)

    def positionRelativeTo(self, other, dp=1):
        '''Returns an Enum value: Position.CONTAINS, Position.INSIDE, Position.OVERLAPS, Position.DISJOINT or Position.EQUAL.
        other is another PolygonObject.'''
        ABOVE, BELOW, CONTAINS, ABOVEORCONTAINS, BELOWORCONTAINS = 0, 1, 2, 3, 4
        ENDING, ONGOING, STARTING = 0, 1, 2
        START, END = 0, 1

        def makeregion(ID, bounds, status):
            return {"ID":ID, "bounds":bounds, "status":status, "position":{}}

        def getintervals(poly, x):
            '''Returns the intervals which are the intersection between poly and a vertical
             line at x, as a list of tuples'''
            yvalues = [] #Will contain the y-values of the intersections of the edges of poly and the vertical line at x
            L = len(poly)
            i = 0
            while i < L:
                (x1, y1) = poly[i]
                (x2, y2) = poly[(i+1)%L]
                if (x1 < x and x2 > x) or (x1 > x and x2 < x): #The vertical line intersects this edge,
                    yvalues.append((round(y1 + (x-x1)*(y2-y1)/(x2-x1), dp), "N")) #so calculate the intersection point and add it to the list.
                elif x1 == x and x2 == x: #This edge lies on the vertical line
                    (x0, y0) = poly[(i-1)%L]
                    (x3, y3) = poly[(i+2)%L]
                    t1 = "L" if x0<x else "R"
                    t2 = "L" if x3<x else "R"
                    if t1 == t2:
                        yvalues.extend([(round(y1, dp), t1), (round(y2, dp), t2)])
                    else:
                        yvalues.append(([round(y1, dp), round(y2, dp)], t1+t2))
                    i += 1
                    if i == L: del yvalues[0]
                elif x1 == x: #This vertex lies on the vertical line
                    vertex = round(y1, dp)
                    (x0, y0) = poly[(i-1)%L]
                    t = "L" if (x0 < x and x2 < x) else "R" if (x0 > x and x2 > x) else "N"
                    yvalues.append((vertex, t)) # so add it to the list
                    if t in ["L", "R"]: #The vertex is a local extremity,
                        yvalues.append((vertex, t))  #so add the y-value a second time.
                i += 1

            yvalues.sort(key=lambda x: [x[0]] if not isinstance(x[0], list) else x[0])
            intervals = []
            for i in range(0, len(yvalues), 2): # There must be an even number of y-values to be grouped in pairs
                y0 = yvalues[i]
                y1 = yvalues[i+1]
                if isinstance(y0, list):
                    if not (i>0 and y0==intervals[-1]): intervals.append(y0)
                    if isinstance(y1, list):
                        if y1 != y0: intervals.append(y1)
                    else:
                        intervals.append((y0[1], y1))
                elif isinstance(y1, list):
                    intervals.extend([(y0, y1[0]), y1])
                else:
                    intervals.append((y0, y1))
            return intervals

        def getregions(intervals, rlist, nextrlabel):
            #nonlocal nextrlabel
            rlist = [region for region in rlist if region["status"] != ENDING]
            rcount = len(rlist)
            rindex = 0
            newrlist = []
            for (y1, t1), (y2, t2) in intervals:
                startregion = False
                oldy1 = y1[0] if t1=="LR" else y1[1] if t1=="RL" else y1
                newy1 = y1[0] if t1=="RL" else y1[1] if t1=="LR" else y1
                oldy2 = y2[0] if t2=="LR" else y2[1] if t2=="RL" else y2
                newy2 = y2[0] if t2=="RL" else y2[1] if t2=="LR" else y2
                if t1=="R" and t2=="R" and (rindex>=rcount or newy2 < rlist[rindex]["bounds"][START]):
                    startregion = True
                    rlist.append(makeregion(chr(nextrlabel), [newy1, newy2], STARTING))
                    nextrlabel += 1
                elif t1=="L" and t2=="L":
                    rlist[rindex]["bounds"] = [oldy1, oldy2]
                    rlist[rindex]["status"] = ENDING
                elif t1=="N":
                    rlist[rindex]["bounds"][START] = oldy1
                    if rlist[rindex]["status"]==STARTING: rlist[rindex]["status"] = ONGOING
                elif t1 in ["RL", "LR"]:
                    rlist[rindex]["bounds"][START] = oldy1
                    rlist[rindex]["status"] = ENDING
                    newrlist.append(makeregion(chr(nextrlabel), [newy1, None], STARTING))
                    nextrlabel += 1
                elif t1=="R":
                    newrlist.append(makeregion(chr(nextrlabel), [newy1, None], STARTING))
                    nextrlabel += 1
                elif t1=="L":
                    rlist[rindex]["bounds"][START] = oldy1
                    rlist[rindex]["status"] = ENDING
                if t2=="N":
                    rlist[rindex]["bounds"][END] = oldy2
                    if rlist[rindex]["status"] == STARTING: rlist[rindex]["status"] = ONGOING
                    if newrlist: newrlist[-1]["bounds"][END] = newy2

                elif t2 in ["RL", "LR"]:
                    rlist[rindex]["bounds"][END] = oldy2
                    rlist[rindex]["status"] = ENDING
                    if newrlist:
                        newrlist[-1]["bounds"][END] = newy2
                    else:
                        newrlist.append(makeregion(chr(nextrlabel), [newy1, newy2], STARTING))
                        nextrlabel += 1
                elif t2=="R" and not startregion:
                    rlist[rindex]["status"] = ENDING
                    if not newrlist:
                        newrlist.append(makeregion(chr(nextrlabel), [newy1, newy2], STARTING))
                        nextrlabel += 1
                    else:
                        newrlist[-1]["bounds"][END] = newy2
                elif t2=="L" and t1!="L":
                    rlist[rindex]["bounds"][END] = oldy2
                    rlist[rindex]["status"] = ENDING
                    if not newrlist:
                        newrlist.append(makeregion(chr(nextrlabel), [newy1, None], STARTING))
                        nextrlabel += 1

                if t2 != "R": rindex += 1
                if t2 != "L":
                    if newrlist:
                        rlist.extend(newrlist)
                        newrlist = []

            rlist.sort(key=lambda x: x["bounds"])
            return rlist, nextrlabel

        def compareintervals(currentoutcome, rlist1, rlist2):
            for inner in rlist2: #For each "inner?" interval
                if not rlist1:
                    if currentoutcome == Position.CONTAINS: return Position.OVERLAPS
                    currentoutcome = Position.DISJOINT

                (start2, end2) = inner["bounds"]
                alldisjoint = True
                for outer in rlist1: #Check each "outer?" interval
                    if (inner["status"], outer["status"]) in [(STARTING, ENDING), (ENDING, STARTING)]: continue
                    (start1, end1) = outer["bounds"]
                    try:
                        position = inner["position"][outer["ID"]]
                        if position == ABOVE and end1 > start2: return Position.OVERLAPS
                        elif position == BELOW and start1 < end2: return Position.OVERLAPS
                        elif position == CONTAINS:
                            if (start1 > start2 or end1 < end2): return Position.OVERLAPS
                            if outer["status"] == ENDING and inner["status"] != ENDING: continue
                            alldisjoint = False
                        elif position == ABOVEORCONTAINS:
                            if end1 <= start2:
                                if currentoutcome == Position.CONTAINS: return Position.OVERLAPS
                                inner["position"][outer["ID"]] = ABOVE
                            elif start1 <= start2 and end1 >= end2:
                                if currentoutcome == Position.DISJOINT: return Position.OVERLAPS
                                inner["position"][outer["ID"]] = CONTAINS
                                alldisjoint = False
                                currentoutcome = Position.CONTAINS
                            else: return Position.OVERLAPS
                        elif position == BELOWORCONTAINS:
                            if start1 >= end2:
                                if currentoutcome == Position.CONTAINS: return Position.OVERLAPS
                                inner["position"][outer["ID"]] = BELOW
                            elif start1 <= start2 and end1 >= end2:
                                if currentoutcome == Position.DISJOINT: return Position.OVERLAPS
                                inner["position"][outer["ID"]] = CONTAINS
                                alldisjoint = False
                                currentoutcome = Position.CONTAINS
                            else: return Position.OVERLAPS

                    except KeyError:
                        if start2 == end2 == start1 == end1:
                            alldisjoint = False
                        elif start2 == end2 == end1:
                            inner["position"][outer["ID"]] = ABOVEORCONTAINS
                            alldisjoint = False
                        elif start2 == end2 == start1:
                            inner["position"][outer["ID"]] = BELOWORCONTAINS
                            alldisjoint = False
                        elif end1 <= start2:
                            inner["position"][outer["ID"]] = ABOVE
                        elif start1 >= end2:
                            inner["position"][outer["ID"]] = BELOW
                        elif start1 <= start2 and end1>=end2:
                            if currentoutcome == Position.DISJOINT: return Position.OVERLAPS #If there is a previous contradictory outcome, we have an overlap
                            inner["position"][outer["ID"]] = CONTAINS
                            currentoutcome = Position.CONTAINS #Otherwise, outer interval contains inner one
                            if outer["status"] == ENDING and inner["status"] != ENDING: continue
                            alldisjoint = False
                        else: #start1 < end2 and end1 > start2 and (start1 > start2 or end1 < end2)
                            return Position.OVERLAPS #since part of the "inner?" interval is outside the "outer" interval
                if alldisjoint:
                    if currentoutcome == Position.CONTAINS: return Position.OVERLAPS
                    currentoutcome = Position.DISJOINT
            return currentoutcome #Checked all "inner" intervals

        dp1 = dp+2
        poly1 = [(round(x,dp1), round(y,dp1)) for (x, y) in self.PointList]
        poly2 = [(round(x,dp1), round(y,dp1)) for (x, y) in other.PointList]
        transposed = False

        bboxresult = self._compareboundingboxes(poly1, poly2)
        if bboxresult == Position.DISJOINT: return Position.DISJOINT
        if bboxresult == Position.EQUAL:
            if self._equalPolys(poly1, poly2): return Position.EQUAL
            elif self._area(poly2) > self._area(poly1):
                poly1, poly2 = poly2, poly1
                transposed = True
        if bboxresult == Position.INSIDE:
            poly1, poly2 = poly2, poly1
            transposed = True

        xvalues = sorted(set(x for (x, y) in poly1+poly2))
        rlist1 = []
        rlist2 = []
        rdict = {}
        nextrlabel1 = 65
        nextrlabel2 = 97
        currentoutcome = None
        for i, x in enumerate(xvalues): #Vertical sweepline stops at each vertex of either polygon
            intervals1 = getintervals(poly1, x)
            #print (x)
            rlist1, nextrlabel1 = getregions(intervals1, rlist1, nextrlabel1)
            #print (rlist1)
            intervals2 = getintervals(poly2, x)
            rlist2, nextrlabel2 = getregions(intervals2, rlist2, nextrlabel2)
            #print (rlist2)

            currentoutcome = compareintervals(currentoutcome, rlist1, rlist2)
            #print ("currentoutcome", currentoutcome, "\n")
            if currentoutcome == Position.OVERLAPS: return currentoutcome
        if currentoutcome == Position.CONTAINS and transposed: currentoutcome = Position.INSIDE
        return currentoutcome

    @staticmethod
    def _getboundingbox(poly):
        xcoords = [x for (x,y) in poly]
        left = min(xcoords)
        right = max(xcoords)
        ycoords = [y for (x,y) in poly]
        top = min(ycoords)
        bottom = max(ycoords)
        return (left, top), (right, bottom)

    @staticmethod
    def _compareboundingboxes(poly1, poly2):
        ((left1, top1), (right1, bottom1)) = PolygonObject._getboundingbox(poly1)
        ((left2, top2), (right2, bottom2)) = PolygonObject._getboundingbox(poly2)
        if right1 <= left2 or right2 <= left1 or bottom1 <= top2 or bottom2 <= top1: return Position.DISJOINT
        if left1 < left2:
            if right1 < right2: return Position.OVERLAPS
            else: xresult = Position.CONTAINS
        elif left1 == left2:
            xresult = Position.INSIDE if right1 < right2 else Position.EQUAL if right1 == right2 else Position.CONTAINS
        else: #left1 > left2
            if right1 > right2: return Position.OVERLAPS
            else: xresult = Position.INSIDE

        if top1 < top2:
            if bottom1 < bottom2: return Position.OVERLAPS
            else: return Position.OVERLAPS if xresult == Position.INSIDE else Position.CONTAINS
        elif top1 == top2:
            if bottom1 < bottom2: return Position.OVERLAPS if xresult == Position.CONTAINS else Position.INSIDE
            elif bottom1 == bottom2: return xresult
            else: return Position.OVERLAPS if xresult == Position.INSIDE else Position.CONTAINS
        else: #top1 > top2
            if bottom1 > bottom2: return Position.OVERLAPS
            else: return Position.OVERLAPS if xresult == Position.CONTAINS else Position.INSIDE

    @staticmethod
    def _area(poly):
        area = 0
        (x0, y0) = poly[-1]
        for (x1, y1) in poly:
            area += x1*y0 - x0*y1
            (x0, y0) = (x1, y1)
        return abs(area/2)

    @staticmethod
    def _equalPolys(poly1, poly2):
        '''Returns True if poly1 is identical to poly2, False otherwise.
        poly1 and poly2 are lists of vertex coordinates.'''
        start1 = poly1.index(min(poly1))
        poly1 =  poly1[start1+1:]+poly1[:start1]
        start2 = poly2.index(min(poly2))
        poly2 =  poly2[start2+1:]+poly2[:start2]
        return poly1 == poly2 or poly1 == poly2[::-1]

class RectangleObject(svg.rect, TransformMixin, NonBezierMixin):
    '''Wrapper for SVG rect.  Parameters:
    pointlist: a list of coordinates for two opposite vertices
    angle: an optional angle of rotation (clockwise, in degrees).'''
    def __init__(self, pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.rect.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.Update()

    def Update(self):
        [(x1, y1), (x2, y2)] = self.PointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        t = svgbase.createSVGTransform()
        t.setRotate(self.angle, cx, cy)
        self.transform.baseVal.initialize(t)

        basepointlist = self.transformedPointList(t.matrix.inverse())
        [(x1, y1), (x2, y2)] = basepointlist
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
        self.PointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.Update()

    def Update(self):
        [(x1, y1), (x2, y2)] = self.PointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        t = svgbase.createSVGTransform()
        t.setRotate(self.angle, cx, cy)
        self.transform.baseVal.initialize(t)

        basepointlist = self.transformedPointList(t.matrix.inverse())
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
            self.PointList = [Point(coords) for coords in pointlist]
        else:
            (x, y) = centre
            self.PointList = [Point((x, y)), Point((x+radius, y))]
        svg.circle.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.Update()

    def Update(self):
        [(x1, y1), (x2, y2)] = self.PointList
        self.attrs["cx"]=x1
        self.attrs["cy"]=y1
        self.attrs["r"]=hypot(x2-x1, y2-y1)

class BezierObject(svg.path, BezierMixin, TransformMixin):
    '''Wrapper for svg path element.  Parameter:
    pointsetlist: a list of tuples, each tuple consisting of three points:
    (previous-control-point, vertex, next-control-point).
    For the first vertex, the previous-control-point must be None,
    and for the last vertex, the next-control-point must be None.'''
    def __init__(self, pointsetlist=[(None, (0,0), (0,0)), ((0,0), (0,0), None)], linecolour="black", linewidth=1, fillcolour=None):
        def toPoint(coords):
            return None if coords is None else Point(coords)
        svg.path.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":None})
        self.PointsetList = [[toPoint(coords) for coords in pointset] for pointset in pointsetlist]
        self.Update()

    def Update(self):
        (dummy, (x1, y1), (c1x, c1y)) = self.PointsetList[0]
        ((c2x, c2y), (x2, y2), dummy) = self.PointsetList[-1]
        plist = ["M", x1, y1, "C", c1x, c1y]+[x for p in self.PointsetList[1:-1] for c in p for x in c]+[c2x, c2y, x2, y2]
        self.attrs["d"] = " ".join(str(x) for x in plist)

class ClosedBezierObject(svg.path, BezierMixin, TransformMixin):
    '''Wrapper for svg path element.  Parameter:
    pointsetlist: a list of tuples, each tuple consisting of three points:
    (previous-control-point, vertex, next-control-point).
    The path will be closed (the first vertex does not need to be repeated).'''
    def __init__(self, pointsetlist=[((0,0), (0,0), (0,0))], linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.path.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointsetList = [[Point(coords) for coords in pointset] for pointset in pointsetlist]
        self.Update()

    def Update(self):
        ((c1x, c1y), (x, y), (c2x, c2y)) = self.PointsetList[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in self.PointsetList[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))

class SmoothBezierObject(SmoothBezierMixin, BezierObject):
    '''Wrapper for svg path element.  Parameter:
    pointlist: a list of vertices.
    Control points will be calculated automatically so that the curve is smooth at each vertex.'''
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour=None):
        self.PointList = [Point(coords) for coords in pointlist]
        pointsetlist = self.getpointsetlist(self.PointList)
        BezierObject.__init__(self, pointsetlist, linecolour, linewidth, fillcolour)

    def getpointsetlist(self, pointlist):
        if len(pointlist) == 2: return[[None]+pointlist, pointlist+[None]]
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            if i == 1:
                (x1, y1) = pointlist[0]
                (x2, y2) = c1
                pointsetlist = [(None, pointlist[0], Point(((x1+x2)/2, (y1+y2)/2)))]
            pointsetlist.append((c1, pointlist[i], c2))
        (x1, y1) = pointlist[-1]
        (x2, y2) = c2
        pointsetlist.append((Point(((x1+x2)/2, (y1+y2)/2)), pointlist[-1], None))
        return pointsetlist

class SmoothClosedBezierObject(SmoothBezierMixin, ClosedBezierObject):
    '''Wrapper for svg path element.  Parameter:
    pointlist: a list of vertices.
    The path will be closed (the first vertex does not need to be repeated).
    Control points will be calculated automatically so that the curve is smooth at each vertex.'''
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        self.PointList = [Point(coords) for coords in pointlist]
        pointsetlist = self.getpointsetlist(self.PointList)
        ClosedBezierObject.__init__(self, pointsetlist, linecolour, linewidth, fillcolour)

    def getpointsetlist(self, pointlist):
        pointlist = [pointlist[-1]]+pointlist[:]+[pointlist[0]]
        pointsetlist = []
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            pointsetlist.append((c1, pointlist[i], c2))
        return pointsetlist

class PointObject(svg.circle, TransformMixin):
    '''A point (small circle) on a diagram. Parameters:
    XY: the coordinates of the point,
    pointsize: (optional) the radius of the point.'''
    def __init__(self, XY=(0,0), colour="black", pointsize=2):
        (x, y) = XY
        svg.circle.__init__(self, cx=x, cy=y, r=pointsize, style={"stroke":colour, "strokeWidth":1, "fill":colour})
        self._XY = None
        self.XY = Point(XY)

    def Update(self):
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
        self.PointList = []
        for i in range(sidecount):
            t = radoffset+i*angle
            self.PointList.append(Point((cx+radius*sin(t), cy-radius*cos(t))))
        PolygonObject.__init__(self, self.PointList, linecolour, linewidth, fillcolour)

class GroupObject(svg.g, TransformMixin):
    '''Wrapper for SVG g element. Parameters:
    objlist: list of the objects to include in the group
    id: (optional) id to indetify the element in the DOM'''
    def __init__(self, objlist=[], objid=None):
        svg.g.__init__(self)
        if objid: self.attrs["id"] = objid
        if not isinstance(objlist, list): objlist = [objlist]
        self.ObjectList = []
        for obj in objlist:
            self.AddObject(obj)
        self._Canvas = None
        self.Group = None

    def AddObject(self, svgobject):
        self <= svgobject
        svgobject.Group = self
        self.ObjectList.append(svgobject)

    def ClearAll(self):
        while self.firstChild:
            self.removeChild(self.firstChild)
        self.ObjectList = []

    @property
    def Canvas(self):
        return self._Canvas

    @Canvas.setter
    def Canvas(self, canvas):
        self._Canvas = canvas
        for obj in self.ObjectList:
            obj.Canvas = canvas

class CanvasObject(svg.svg):
    '''Wrapper for SVG svg element.  Parameters:
    width, height: NB these are the CSS properties, so can be given as percentages, or vh, vw units etc.
                    (to set the SVG attributes which are in pixels, call canvas.setDimensions() after creating the object.)
    colour: the background colour
    id: the DOM id

    After creation, there are various attributes which control how the canvas responds to mouse actions:

    canvas.MouseMode = MouseMode.TRANSFORM
        Clicking on an object and dragging carries out the transformation
        which has been set using canvas.setMouseTransformType().  This can be:
        TransformType.NONE, TransformType.TRANSLATE, TransformType.ROTATE, TransformType.XSTRETCH, TransformType.YSTRETCH, TransformType.ENLARGE
        canvas.Snap: set to a number of pixels. After a transform, if a vertex of the transformed object is within
            this many pixels of a vertex of another object in the canvas's ObjectDict, the transformed object is snapped
            so that the vertices coincide. (If more than one pair of vertices are below the snap threshold, the closest pair are used.
            If canvas.Snap is set to None (the default), no snapping will be done.
        canvas.RotateSnap: set to a number of degrees. After a transform, if a snap is to be done, and the edges
            of the two shapes at the vertex to be snapped are within this many degrees of each other,
            the transformed shape will be rotated so that the edges coincide.
            If canvas.RotateSnap is set to None (the default), no rotating will be done.

    canvas.MouseMode = MouseMode.DRAW
        Shapes can be drawn on the canvas by clicking, moving, clicking again...
        A shape is completed by double-clicking.
        The shape which will be drawn is chosen by setting canvas.Tool, which can be:
        line, polygon, polyline, rectangle, ellipse, circle, bezier, closedbezier
        (NB the bezier shapes will be smooth.)
        The stroke, stroke-width and fill of the shape are set by canvas.PenColour, canvas.PenWidth, and canvas.FillColour

    canvas.MouseMode = MouseMode.EDIT
        Clicking on a shape causes "handles" to be displayed, which can be used to edit the shape.
        (For Bezier shapes there are also "control handles" to control the curvature.)
        In this mode, canvas.Tool will normally be set to "select".
        While a shape is selected, pressing the DEL key on the keyboard will delete the shape.
        canvas.SelectedShape is the shape curently being edited.
        Use canvas.DeSelectShape to stop editing a shape and hide the handles.

    canvas.MouseMode = MouseMode.NONE
        No user interaction with the canvas.
    '''


    def __init__(self, width, height, colour="white", id=None):
        svg.svg.__init__(self, style={"width":width, "height":height, "backgroundColor":colour})
        if id: self.id = id
        self.ShapeTypes = {"line":LineObject, "polygon":PolygonObject, "polyline":PolylineObject, "rectangle":RectangleObject, "ellipse":EllipseObject, "circle":CircleObject, "bezier":SmoothBezierObject, "closedbezier":SmoothClosedBezierObject}
        self.Cursors = ["auto", "move", "url(brySVG/rotate.png), auto", "col-resize", "row-resize", "url(brySVG/enlarge.png), auto"]
        #for tt in TransformType: self.setMouseTransformType(tt)
        self.ObjectDict = {}
        self.MouseMode = MouseMode.TRANSFORM
        self.setMouseTransformType(TransformType.NONE)
        self.MouseOwner = None
        self.LastMouseOwner = None
        self.SelectedShape = None
        self.TransformOrigin = None
        self.Snap = None
        self.RotateSnap = None
        self.Tool = "select"
        self.PenColour = "black"
        self.FillColour  = "yellow"
        self.PenWidth = 5
        self.bind("mousedown", self.onLeftDown)
        self.bind("mousemove", self.onMouseMove)
        self.bind("mouseup", self.onLeftUp)
        self.bind("dragstart", self.onDragStart)
        self.bind("dblclick", self.onDoubleClick)
        document.bind("keydown", self.DeleteSelection)

    def setDimensions(self):
        '''If the canvas was created using non-pixel dimensions (eg percentages),
        call this after creation to set the SVG width and height attributes.'''
        bbox = self.getBoundingClientRect()
        self.attrs["width"] = bbox.width
        self.attrs["height"] = bbox.height

    def fitContents(self):
        '''Scales the canvas so that all the objects on it are visible.'''
        bbox = self.getBBox()
        bboxstring = str(bbox.x-10)+" "+str(bbox.y-10)+" "+str(bbox.width+20)+" "+str(bbox.height+20)
        self.attrs["viewBox"] = bboxstring
        #self.attrs["preserveAspectRatio"] = "none"

    def getSVGcoords(self, event):
        '''Converts mouse event coordinates to SVG coordinates'''
        pt = self.createSVGPoint()
        (pt.x, pt.y) = (event.clientX, event.clientY)
        SVGpt =  pt.matrixTransform(self.getScreenCTM().inverse())
        return Point((SVGpt.x, SVGpt.y))

    def AddObject(self, svgobject, objid=None, fixed=False):
        '''Adds an object to the canvas, and also adds it to the canvas's ObjectDict so that it can be referenced
        using canvas.ObjectDict[id]. This is also needed for the object to be capable of being snapped to.
        (Note that referencing using document[id] will only give the SVG element, not the Python object.)
        If it is not desired that an object should be in the ObjectDict, just add it to the canvas using Brython's <= method.'''
        def AddToDict(svgobj):
            if not svgobj.id: svgobj.id = "id"+str(len(self.ObjectDict))
            self.ObjectDict[svgobj.id] = svgobj
            svgobj.Fixed = fixed
            if isinstance(svgobj, GroupObject):
                for obj in svgobj.ObjectList:
                    AddToDict(obj)
        if objid: svgobject.id = objid
        self <= svgobject
        AddToDict(svgobject)
        svgobject.Canvas = self
        return svgobject

    def ClearAll(self):
        '''Clear all elements from the canvas'''
        while self.firstChild:
            self.removeChild(self.firstChild)
        self.ObjectDict = {}

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

    def setMouseTransformType(self, mtt):
        '''Set canvas.MouseTransformType and show the appropriate cursor.'''
        self.MouseTransformType = mtt
        self.style.cursor = self.Cursors[mtt]

    def onRightClick(self, event):
        event.preventDefault()

    def onDragStart(self, event):
        event.preventDefault()

    def onLeftDown(self, event):
        if event.button > 0: return
        if self.MouseMode == MouseMode.TRANSFORM:
            if self.MouseTransformType == TransformType.NONE or event.target.id not in self.ObjectDict: return
            self.prepareMouseTransform(event)

        elif self.MouseMode == MouseMode.DRAW:
            if self.MouseOwner:
                if self.MouseOwner.ShapeType in ("polygon", "polyline", "bezier", "closedbezier"):
                    coords = self.getSVGcoords(event)
                    self.MouseOwner.AppendPoint(coords)
            elif self.Tool in self.ShapeTypes:
                coords = self.getSVGcoords(event)
                self.createObject(coords)

        elif self.MouseMode == MouseMode.EDIT:
            if event.target.id in self.ObjectDict:
                self.ObjectDict[event.target.id].SelectShape()
            else:
                if self.SelectedShape:
                    self.DeSelectShape()

    def onMouseMove(self, event):
        if self.MouseMode == MouseMode.TRANSFORM:
            if not self.MouseOwner or self.MouseTransformType == TransformType.NONE: return
            self.doMouseTransform(event)
        else:
            if self.MouseOwner:
                coords = self.getSVGcoords(event)
                self.MouseOwner.movePoint(coords)

    def onLeftUp(self, event):
        if event.button > 0: return
        if self.MouseMode == MouseMode.TRANSFORM:
            if self.MouseTransformType == TransformType.NONE: return
            self.endMouseTransform(event)
        elif self.MouseMode == MouseMode.EDIT:
            try:
                self.MouseOwner.onLeftUp()
            except AttributeError:
                pass
            self.LastMouseOwner = self.MouseOwner
            self.MouseOwner = None

    def onDoubleClick(self,event):
        if event.button > 0 or self.MouseMode != MouseMode.DRAW: return
        if self.MouseOwner:
            if self.Tool in ["polygon", "polyline", "bezier", "closedbezier"]:
                self.MouseOwner.DeletePoints(-2, None)
            self.LastMouseOwner = self.MouseOwner
            self.MouseOwner = None

    def createObject(self, coords):
        self.MouseOwner = self.ShapeTypes[self.Tool](pointlist=[coords, coords], linecolour=self.PenColour, linewidth=self.PenWidth, fillcolour=self.FillColour)
        self.AddObject(self.MouseOwner)
        self.MouseOwner.ShapeType = self.Tool

    def prepareMouseTransform(self, event):
        svgobj = self.ObjectDict[event.target.id]
        if svgobj.Fixed: return
        while getattr(svgobj, "Group", None):
            svgobj = svgobj.Group
        self <= svgobj
        self.MouseOwner = svgobj
        bbox = self.MouseOwner.getBBox()
        (cx, cy) = self.MouseOwnerCentre = Point((bbox.x+bbox.width/2, bbox.y+bbox.height/2))
        self.StartPoint = self.getSVGcoords(event)
        if self.MouseTransformType in [TransformType.NONE, TransformType.TRANSLATE]: return
        if self.MouseTransformType in [TransformType.ROTATE, TransformType.ENLARGE]:
            self.TransformOrigin = PointObject(self.MouseOwnerCentre, colour="blue", pointsize=3)
        elif self.MouseTransformType == TransformType.XSTRETCH:
            self.TransformOrigin = LineObject([(cx, bbox.y), (cx, bbox.y+bbox.height)], linecolour="blue", linewidth=2)
        elif self.MouseTransformType == TransformType.YSTRETCH:
            self.TransformOrigin = LineObject([(bbox.x, cy), (bbox.x+bbox.width, cy)], linecolour="blue", linewidth=2)
        self <= self.TransformOrigin

    def doMouseTransform(self, event):
        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.StartPoint
        if offset.coords == [0, 0]: return
        (cx, cy) = self.MouseOwnerCentre
        vec1 = (x1, y1) = self.StartPoint - self.MouseOwnerCentre
        vec2 = (x2, y2) = currentcoords - self.MouseOwnerCentre
        self.StartPoint = currentcoords
        if self.MouseTransformType == TransformType.TRANSLATE:
            self.MouseOwner.translate(offset)
        elif self.MouseTransformType == TransformType.ROTATE:
            self.MouseOwner.rotateByVectors(vec1, vec2, (cx, cy))
        elif self.MouseTransformType == TransformType.XSTRETCH:
            self.MouseOwner.xstretch(x2/x1, cx)
        elif self.MouseTransformType == TransformType.YSTRETCH:
            self.MouseOwner.ystretch(y2/y1, cy)
        elif self.MouseTransformType == TransformType.ENLARGE:
            self.MouseOwner.enlarge(hypot(x2, y2)/hypot(x1, y1), (cx, cy))

    def endMouseTransform(self, event):
        if self.TransformOrigin:
            delete(self.TransformOrigin)
            self.TransformOrigin = None
        if getattr(self.MouseOwner, "PointList", None) and self.Snap:
            if self.RotateSnap: self.doRotateSnap()
            else: self.doSnap()
        self.LastMouseOwner = self.MouseOwner
        self.MouseOwner = None

    def doRotateSnap(self):
        svgobject = self.MouseOwner
        if not hasattr(svgobject, "PointList"): return
        bbox = svgobject.getBBox()
        L, R, T, B = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
        bestdx = bestdy = None
        for objid in self.ObjectDict:
            if objid == svgobject.id: continue
            obj = self.ObjectDict[objid]
            if not hasattr(obj, "PointList"): continue
            bbox = obj.getBBox()
            L1, R1, T1, B1 = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
            if L1-R > self.Snap or R1-L < -self.Snap or T1-B > self.Snap or B1-T < -self.Snap: continue
            for point1 in obj.PointList:
                for point2 in svgobject.PointList:
                    (dx, dy) = point1 - point2
                    if abs(dx) < self.Snap and abs(dy) < self.Snap:
                        pl1 = self.ObjectDict[objid].PointList
                        L = len(pl1)
                        i = pl1.index(point1)
                        vec1a = pl1[(i+1)%L] - point1
                        vec1b = pl1[(i-1)%L] - point1
                        angles1 = [vec1a.angle(), vec1b.angle()]
                        pl2 = svgobject.PointList
                        L = len(pl2)
                        j = pl2.index(point2)
                        vec2a = pl2[(j+1)%L] - point2
                        vec2b = pl2[(j-1)%L] - point2
                        angles2 = [vec2a.angle(), vec2b.angle()]
                        for a1 in angles1:
                            for a2 in angles2:
                                diff = a1-a2
                                absdiff = abs(diff)
                                testdiff = absdiff if absdiff < pi else 2*pi-absdiff

                                if testdiff < self.RotateSnap*pi/180:
                                    svgobject.rotate(diff*180/pi)
                                    (dx, dy) = self.ObjectDict[objid].PointList[i] - svgobject.PointList[j]
                                    svgobject.translate((dx, dy))
                                    print("rotatesnap", time.time()-tt)
                                    return
                        if not bestdx or hypot(dx, dy) < hypot(bestdx, bestdy): (bestdx, bestdy) = (dx, dy)
        if bestdx or bestdy:
            svgobject.translate((bestdx, bestdy))

    def doSnap(self):
        svgobject = self.MouseOwner
        if not hasattr(svgobject, "PointList"): return
        bbox = svgobject.getBBox()
        L, R, T, B = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
        bestdx = bestdy = None
        for objid in self.ObjectDict:
            if objid == svgobject.id: continue
            obj = self.ObjectDict[objid]
            if not hasattr(obj, "PointList"): continue
            bbox = obj.getBBox()
            L1, R1, T1, B1 = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
            if L1-R > self.Snap or R1-L < -self.Snap or T1-B > self.Snap or B1-T < -self.Snap: continue
            for point1 in obj.PointList:
                for point2 in svgobject.PointList:
                    (dx, dy) = point1 - point2
                    if abs(dx) < self.Snap and abs(dy) < self.Snap:
                        if not bestdx or hypot(dx, dy) < hypot(bestdx, bestdy):
                            (bestdx, bestdy) = (dx, dy)
        if bestdx or bestdy:
            svgobject.translate((bestdx, bestdy))

    def DeSelectShape(self):
        if self.SelectedShape:
            delete(self.SelectedShape.Handles)
            if isinstance(self.SelectedShape, BezierMixin):
                delete(self.SelectedShape.ControlHandlesGroup)
                del self.SelectedShape.ControlHandles
            self.MouseOwner = self.SelectedShape = None

    def DeleteSelection(self,event):
        #print (event.target, event.currentTarget)
        if event.keyCode == 46:
            if self.SelectedShape:
                delete(self.SelectedShape.Handles)
                if isinstance(self.SelectedShape, BezierMixin):
                    delete(self.SelectedShape.ControlHandlesGroup)
                    del self.SelectedShape.ControlHandles
                delete(self.SelectedShape)
                del self.ObjectDict[self.SelectedShape.id]
                self.SelectedShape = None

class Handle(PointObject):
    def __init__(self, owner, index, coords):
        PointObject.__init__(self, coords, "red", 5)
        self.owner = owner
        self.index = index
        self.bind("mousedown", self.Select)

    def Select(self, event):
        event.stopPropagation()
        if self.owner.Canvas.MouseOwner == None:
            self.owner.Canvas.MouseOwner = self

    def movePoint(self, coords):
        offset = coords - self.XY
        self.XY = coords
        if isinstance(self.owner, BezierMixin):
            pointset = [None, self.XY, None]
            for ch in self.owner.ControlHandles[self.index]:
                ch.XY = ch.XY + offset
                pointset[ch.subindex] = ch.XY
            self.owner.SetPointset(self.index, pointset)
        else:
            self.owner.SetPoint(self.index, self.XY)

class ControlHandle(PointObject):
    def __init__(self, owner, index, subindex, coords):
        PointObject.__init__(self, coords, "green", 5)
        self.owner = owner
        self.index = index
        self.subindex = subindex
        self.bind("mousedown", self.Select)

    def Select(self, event):
        event.stopPropagation()
        if self.owner.Canvas.MouseOwner == None:
            self.owner.Canvas.MouseOwner = self

    def movePoint(self, newcoords):
        self.XY = newcoords

        pointset = list(self.owner.PointsetList[self.index])
        if isinstance(self.owner, SmoothBezierMixin) and None not in pointset:
            point = pointset[1]
            thisoffset = newcoords - point
            otheroffset = pointset[2-self.subindex] - point
            newoffset = thisoffset*(otheroffset.length()/thisoffset.length())
            newothercoords = point-newoffset
            pointset[2-self.subindex] = newothercoords
            otherindex = 0 if self.subindex==2 else 1
            self.owner.ControlHandles[self.index][otherindex].XY = newothercoords
        pointset[self.subindex] = newcoords
        self.owner.SetPointset(self.index, tuple(pointset))

class Point(object):
    '''Class to represent coordinates and also give some vector functionality'''
    def __init__(self, coords):
        self.coords = coords.coords if isinstance(coords, Point) else list(coords)

    def __str__(self):
        return str(tuple(self.coords))

    def __add__(self, other):
        if isinstance(other, (list, tuple)):
            return Point([xi+yi for (xi, yi) in zip(self.coords, other)])
        else:
            return Point([xi+yi for (xi, yi) in zip(self.coords, other.coords)])

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
        return (sum(xi*xi for xi in self.coords))**0.5

    def angle(self):
        return atan2(self.coords[1], self.coords[0])

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
