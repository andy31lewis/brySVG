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

import browser.svg as svg
from browser import document
from math import sin, cos, atan2, pi, hypot
svgbase = svg.svg()
#t = svgbase.createSVGTransform()

def delete(element):
    element.parentNode.removeChild(element)
    del element

class MouseMode(object):
    NONE, TRANSFORM, DRAW, EDIT = range(4)

class TransformType(object):
    NONE, TRANSLATE, ROTATE, XSTRETCH, YSTRETCH, ENLARGE = range(6)

class TransformMixin(object):
    def cloneObject(self):
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
        pt = svgbase.createSVGPoint()
        (pt.x, pt.y) = self.XY
        pt =  pt.matrixTransform(matrix)
        return Point((pt.x, pt.y))
        
    def transformedPointList(self, matrix):
        pt = svgbase.createSVGPoint()
        newpointlist = []
        for point in self.PointList:
            (pt.x, pt.y) = point
            pt =  pt.matrixTransform(matrix)
            newpointlist.append(Point((pt.x, pt.y)))
        return newpointlist
        
    def transformedPointsetList(self, matrix):
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

    def transformPoints(self, matrix):
        if isinstance(self, PointObject):
            self.XY = self.transformedPoint(matrix)
        elif isinstance(self, (BezierObject, ClosedBezierObject)):
            self.PointsetList = self.transformedPointsetList(matrix)
        else:
            self.PointList = self.transformedPointList(matrix)
            
    def translate(self, vector):
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.translate(vector)
        else:
            t = svgbase.createSVGTransform()
            t.setTranslate(*vector)
            self.transformPoints(t.matrix)
            self.Update()
    
    def rotate(self, angle, centre=None):
        if not centre: 
            bbox = self.getBBox()
            centre = (bbox.x+bbox.width/2, bbox.y+bbox.height/2)
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.rotate(angle, centre)
        else:
            t = svgbase.createSVGTransform()
            t.setRotate(angle, *centre)
            self.transformPoints(t.matrix)
            if isinstance(self, (EllipseObject, RectangleObject)):
                self.angle += angle
            self.Update()

    def rotateByVectors(self, vec1, vec2, centre=(0, 0)):
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.rotateByVectors(vec1, vec2, centre)
        else:
            (cx, cy) = centre
            (x1, y1) = vec1
            (x2, y2) = vec2
            (x3, y3) = (x1*x2+y1*y2, x1*y2-x2*y1)
            angle = atan2(y3, x3)*180/pi
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix = matrix.rotateFromVector(x3, y3)
            matrix = matrix.translate(-cx, -cy)
            self.transformPoints(matrix)
            if isinstance(self, (EllipseObject, RectangleObject)):
                self.angle += angle
            self.Update()

    def xstretch(self, xscale, cx=0):
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.xstretch(xscale, cx)
        else:
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(cx, 0)
            matrix.a = xscale
            matrix = matrix.translate(-cx, 0)
            self.transformPoints(matrix)
            self.Update()

    def ystretch(self, yscale, cy=0):
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.ystretch(yscale, cy)
        else:
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(0, cy)
            matrix.d = yscale
            matrix = matrix.translate(0, -cy)
            self.transformPoints(matrix)
            self.Update()

    def enlarge(self, scalefactor, cx=0, cy=0):
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.enlarge(scalefactor, cx, cy)
        else:
            matrix = svgbase.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix = matrix.scale(scalefactor)
            matrix = matrix.translate(-cx, -cy)
            self.transformPoints(matrix)
            self.Update()

class NonBezierMixin(object):
    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.Update()

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
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
    def AppendPoint(self, point):
        self.PointList.append(point)
        self.Update()

    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.Update()

class BezierMixin(object):
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
        self.PointList = [Point(coords) for coords in pointlist]
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
        return (c1, c2)

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
    def __init__(self, string, point, anchorpos=1, style="normal"):
        (x, y) = point
        if anchorpos in [3, 4, 5]:
            horizpos = "end"
        elif anchorpos in [2, 6, 9]:
            horizpos = "middle"
        else:
            horizpos = "end"
        if anchorpos in [5, 6, 7]:
            yoffset = "0pt"
        elif anchorpos in [4, 8, 9]:
            yoffset = "6pt"
        else:
            yoffset = "12pt"

        svg.text.__init__(self, string, x=x, y=y, font_size=12, dy=yoffset, text_anchor=horizpos)

class PolylineObject(svg.polyline, TransformMixin, NonBezierMixin, PolyshapeMixin):
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour=None):
        svg.polyline.__init__(self, fill="none", style={"stroke":linecolour, "strokeWidth":linewidth})
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def Update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

class PolygonObject(svg.polygon, TransformMixin, NonBezierMixin, PolyshapeMixin):
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.polygon.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def Update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

    def containsPoint(self, point):
        (x, y) = point
        length = len(self.PointList)
        counter = 0
        (x1, y1) = self.PointList[0]
        for i in range(1, length+1):
            (x2, y2) = self.PointList[i%length]
            if y>min(y1, y2) and y<=max(y1,y2) and y1!=y2 and x<max(x1, x2):
                if x1==x2 or x <= x1 + (y-y1)*(x2-x1)/(y2-y1):
                    print ((x1,y1), (x2,y2))
                    counter += 1
            (x1, y1) = (x2, y2)
        return (counter)
        
class RectangleObject(svg.rect, TransformMixin, NonBezierMixin):
    def __init__(self, pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.rect.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.Update()

    def Update(self):
        [(x1, y1), (x2, y2)] = self.PointList
        centre = (cx, cy) = Point(((x1+x2)/2, (y1+y2)/2))
        t = svgbase.createSVGTransform()
        t.setRotate(self.angle, cx, cy)
        self.transform.baseVal.initialize(t)
        
        basepointlist = self.transformedPointList(t.matrix.inverse())
        [(x1, y1), (x2, y2)] = basepointlist
        self.attrs["x"] = x1
        self.attrs["y"] = y1
        self.attrs["width"] = abs(x2-x1)
        self.attrs["height"] = abs(y2-y1)
        
class EllipseObject(svg.ellipse, TransformMixin, NonBezierMixin):
    def __init__(self, pointlist=[(0,0), (0,0)], angle=0, linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.ellipse.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]
        self.angle = angle
        self.Update()
    
    def Update(self):
        [(x1, y1), (x2, y2)] = self.PointList
        centre = (cx, cy) = Point(((x1+x2)/2, (y1+y2)/2))
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
    def __init__(self, pointsetlist=[((0,0), (0,0), (0,0))], linecolour="black", linewidth=1, fillcolour="yellow"):
        svg.path.__init__(self, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointsetList = [[Point(coords) for coords in pointset] for pointset in pointsetlist]
        self.Update()

    def Update(self):
        ((c1x, c1y), (x, y), (c2x, c2y)) = self.PointsetList[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in self.PointsetList[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))

class SmoothBezierObject(SmoothBezierMixin, BezierObject):
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour=None):
        pointsetlist = self.getpointsetlist(pointlist)
        BezierObject.__init__(self, pointsetlist, linecolour, linewidth, fillcolour)
        self.PointList = [Point(coords) for coords in pointlist]
            
    def getpointsetlist(self, pointlist):
        if len(pointlist) == 2: return[[None]+pointlist, pointlist+[None]]
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            if i == 1:
                (x1, y1) = pointlist[0]
                (x2, y2) = c1
                pointsetlist = [(None, pointlist[0], ((x1+x2)/2, (y1+y2)/2))]
            pointsetlist.append((c1, pointlist[i], c2))
        (x1, y1) = pointlist[-1]
        (x2, y2) = c2
        pointsetlist.append((((x1+x2)/2, (y1+y2)/2), pointlist[-1], None))
        return pointsetlist

class SmoothClosedBezierObject(SmoothBezierMixin, ClosedBezierObject):
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        pointsetlist = self.getpointsetlist(pointlist)
        ClosedBezierObject.__init__(self, pointsetlist, linecolour, linewidth, fillcolour)
        self.PointList = [Point(coords) for coords in pointlist]
            
    def getpointsetlist(self, pointlist):
        pointlist = [pointlist[-1]]+pointlist[:]+[pointlist[0]]
        pointsetlist = []
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            pointsetlist.append((c1, pointlist[i], c2))
        #print (pointsetlist)
        return pointsetlist

class PointObject(svg.circle, TransformMixin):
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
    def __init__(self, objlist=[], id=None):
        svg.g.__init__(self)
        if id: self.attrs["id"] = id
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
    def __init__(self, width, height, colour="white", id=None):
        svg.svg.__init__(self, style={"width":width, "height":height, "backgroundColor":colour})
        if id: self.id = id
        self.ShapeTypes = {"line":LineObject, "polygon":PolygonObject, "polyline":PolylineObject, "rectangle":RectangleObject, "ellipse":EllipseObject, "circle":CircleObject, "bezier":SmoothBezierObject, "closedbezier":SmoothClosedBezierObject}
        self.Cursors = ["auto", "move", "url(brySVG/rotatearrows.png), auto", "col-resize", "row-resize", "url(brySVG/enlarge.png), auto"]
        self.ObjectDict = {}
        self.MouseMode = MouseMode.TRANSFORM
        self.MouseTransformType = TransformType.NONE
        self.MouseOwner = None
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
        bbox = self.getBoundingClientRect()
        self.attrs["width"] = bbox.width
        self.attrs["height"] = bbox.height

    def fitContents(self):
        bbox = self.getBBox()
        bboxstring = str(bbox.x-10)+" "+str(bbox.y-10)+" "+str(bbox.width+20)+" "+str(bbox.height+20)
        self.attrs["viewBox"] = bboxstring
        #self.attrs["preserveAspectRatio"] = "none"

    def getSVGcoords(self, event):
        pt = self.createSVGPoint()
        (pt.x, pt.y) = (event.clientX, event.clientY)
        SVGpt =  pt.matrixTransform(self.getScreenCTM().inverse())
        return Point((SVGpt.x, SVGpt.y))

    def AddObject(self, svgobject):
        def AddToDict(svgobj):
            if not svgobj.id: svgobj.id = "id"+str(len(self.ObjectDict))
            self.ObjectDict[svgobj.id] = svgobj
            if isinstance(svgobj, GroupObject):
                for obj in svgobj.ObjectList:
                    AddToDict(obj)
        self <= svgobject
        AddToDict(svgobject)
        svgobject.Canvas = self
        return svgobject
    
    def ClearAll(self):
        while self.firstChild:
            self.removeChild(self.firstChild)

    def rotateElement(self, element, angle, centre=None):
        if not centre: 
            bbox = element.getBBox()
            centre = (bbox.x+bbox.width/2, bbox.y+bbox.height/2)
        t = svgbase.createSVGTransform()
        t.setRotate(angle, *centre)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def translateElement(self, element, vector):
        t = svgbase.createSVGTransform()
        t.setTranslate(*vector)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def scaleElement(self, element, xscale, yscale):
        t = svgbase.createSVGTransform()
        t.setScale(xscale, yscale)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def setMouseTransformType(self, n):
        self.MouseTransformType = n
        self.style.cursor = self.Cursors[n]

    def onRightClick(self, event):
        event.preventDefault()

    def onDragStart(self, event):
        event.preventDefault()

    def onLeftDown(self, event):
        if event.button > 0: return
        if self.MouseMode == MouseMode.TRANSFORM:
            if self.MouseTransformType == 0 or event.target.id not in self.ObjectDict: return
            self.prepareMouseTransform(event)

        elif self.MouseMode == MouseMode.DRAW:
            #print (self.Tool)
            if self.MouseOwner:
                if self.MouseOwner.ShapeType in ("polygon", "polyline", "bezier", "closedbezier"):
                    coords = self.getSVGcoords(event)
                    self.MouseOwner.AppendPoint(coords)
            elif self.Tool in self.ShapeTypes:
                coords = self.getSVGcoords(event)
                self.createObject(coords)

        elif self.MouseMode == MouseMode.EDIT:
            #print (event.target.id)
            if event.target.id in self.ObjectDict:
                self.ObjectDict[event.target.id].SelectShape()
            else:
                if self.SelectedShape:
                    self.DeSelectShape()

    def onMouseMove(self, event):
        if self.MouseMode == MouseMode.TRANSFORM:
            if not self.MouseOwner or self.MouseTransformType == 0: return
            self.doMouseTransform(event)
        else:
            #print (self.MouseOwner)
            if self.MouseOwner:
                coords = self.getSVGcoords(event)
                self.MouseOwner.movePoint(coords)

    def onLeftUp(self, event):
        if event.button > 0: return
        if self.MouseMode == MouseMode.TRANSFORM:
            #print (self.MouseTransformType, event.button, event.target, event.target.id)
            if self.MouseTransformType == 0: return
            self.endMouseTransform(event)
        elif self.MouseMode == MouseMode.EDIT:
            try:
                self.MouseOwner.onLeftUp()
            except AttributeError:
                pass
            self.MouseOwner = None

    def onDoubleClick(self,event):
        if event.button > 0 or self.MouseMode != MouseMode.DRAW: return
        if self.MouseOwner:
            if self.Tool in ["polygon", "polyline", "bezier", "closedbezier"]:
                self.MouseOwner.DeletePoints(-2, None)
            self.MouseOwner = None

    def createObject(self, coords):
        #print (coords)
        self.MouseOwner = self.ShapeTypes[self.Tool](pointlist=[coords, coords], linecolour=self.PenColour, linewidth=self.PenWidth, fillcolour=self.FillColour)
        self.AddObject(self.MouseOwner)
        self.MouseOwner.ShapeType = self.Tool

    def prepareMouseTransform(self, event):
        svgobj = self.ObjectDict[event.target.id]
        while getattr(svgobj, "Group", None):
            svgobj = svgobj.Group
        self <= svgobj
        self.MouseOwner = svgobj
        bbox = self.MouseOwner.getBBox()
        (cx, cy) = self.MouseOwnerCentre = Point((bbox.x+bbox.width/2, bbox.y+bbox.height/2))
        #print ((bbox.x, bbox.y), (cx, cy), (bbox.x+bbox.width, bbox.y+bbox.height))
        self.StartPoint = self.getSVGcoords(event)
        if self.MouseTransformType == 1: return
        if self.MouseTransformType in [2, 5]:
            self.TransformOrigin = PointObject(self.MouseOwnerCentre, colour="blue", pointsize=3)
        elif self.MouseTransformType == 3:
            self.TransformOrigin = LineObject([(cx, bbox.y), (cx, bbox.y+bbox.height)], linecolour="blue", linewidth=2)
        elif self.MouseTransformType == 4:
            self.TransformOrigin = LineObject([(bbox.x, cy), (bbox.x+bbox.width, cy)], linecolour="blue", linewidth=2)
        self <= self.TransformOrigin

    def doMouseTransform(self, event):
        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.StartPoint
        if offset.coords == [0, 0]: return
        (cx, cy) = self.MouseOwnerCentre
        vec1 = (x1, y1) = self.StartPoint - self.MouseOwnerCentre
        vec2 = (x2, y2) = currentcoords - self.MouseOwnerCentre
        #print (event.clientX, event.clientY, self.StartPoint, currentcoords)
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
            self.MouseOwner.enlarge(hypot(x2, y2)/hypot(x1, y1), cx, cy)

    def endMouseTransform(self, event):
        if self.TransformOrigin:
            delete(self.TransformOrigin)
            self.TransformOrigin = None
        if getattr(self.MouseOwner, "PointList", None) and self.Snap:
            if self.RotateSnap: self.doRotateSnap()
            else: self.doSnap()
        self.MouseOwner = None

    def doRotateSnap(self):
        bestdx = bestdy = None
        for objid in self.ObjectDict:
            if objid == self.MouseOwner.id: continue
            if not getattr(self.ObjectDict[objid], "PointList", None): continue
            for point1 in self.ObjectDict[objid].PointList:
                for point2 in self.MouseOwner.PointList:
                    (dx, dy) = point1 - point2
                    if abs(dx) < self.Snap and abs(dy) < self.Snap:
                        pl1 = self.ObjectDict[objid].PointList
                        L = len(pl1)
                        i = pl1.index(point1)
                        vec1a = pl1[(i+1)%L] - point1
                        vec1b = pl1[(i-1)%L] - point1
                        angles1 = [vec1a.angle(), vec1b.angle()]
                        pl2 = self.MouseOwner.PointList
                        L = len(pl2)
                        j = pl2.index(point2)
                        vec2a = pl2[(j+1)%L] - point2
                        vec2b = pl2[(j-1)%L] - point2
                        angles2 = [vec2a.angle(), vec2b.angle()]
                        print (angles1, angles2)
                        for a1 in angles1:
                            for a2 in angles2:
                                diff = a1-a2
                                absdiff = abs(diff)
                                testdiff = absdiff if absdiff < pi else 2*pi-absdiff

                                if testdiff < self.RotateSnap*pi/180:
                                    #print (pl1[i], pl2[j], g1, g2, diff)
                                    self.MouseOwner.rotate(diff*180/pi)
                                    print (self.ObjectDict[objid].PointList[i], self.MouseOwner.PointList[j])
                                    (dx, dy) = self.ObjectDict[objid].PointList[i] - self.MouseOwner.PointList[j]
                                    print (dx, dy)
                                    self.MouseOwner.translate((dx, dy))
                                    return
                        if not bestdx or hypot(dx, dy) < hypot(bestdx, bestdy): (bestdx, bestdy) = (dx, dy)
        if bestdx:
            self.MouseOwner.translate((bestdx, bestdy))
        self.MouseOwner = None

    def doSnap(self):
        for objid in self.ObjectDict:
            if objid == self.MouseOwner.id: continue
            if not getattr(self.ObjectDict[objid], "PointList", None): continue
            for point1 in self.ObjectDict[objid].PointList:
                for point2 in self.MouseOwner.PointList:
                    (dx, dy) = point1 - point2
                    if abs(dx) < self.Snap and abs(dy) < self.Snap:
                        self.MouseOwner.translate((dx, dy))
                        return

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
        #if len(pointset) == 3:
        if isinstance(self.owner, SmoothBezierMixin) and None not in pointset:
            point = Point(pointset[1])
            thisoffset = newcoords - point
            otheroffset = Point(pointset[2-self.subindex]) - point
            newoffset = thisoffset*(otheroffset.length()/thisoffset.length())
            newothercoords = point-newoffset
            pointset[2-self.subindex] = newothercoords.coords
            otherindex = 0 if self.subindex==2 else 1
            self.owner.ControlHandles[self.index][otherindex].XY = newothercoords
        pointset[self.subindex] = newcoords.coords
        self.owner.SetPointset(self.index, tuple(pointset))

class Point(object):
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
