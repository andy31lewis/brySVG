#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014-2018 Andy Lewis                                               #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License version 2 as published by #
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,     #
# MA 02111-1307 USA                                                           #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY. See the GNU General Public License for more details.          #

import browser.svg as svg
from math import sin, cos, atan2, pi, hypot
svgbase = svg.svg()

def delete(element):
    element.parentNode.removeChild(element)
    del element

class SVGMixin(object):
    def cloneObject(self):
        newobject = self.__class__()
        if isinstance(newobject, GroupObject):
            newobject.ObjectList = []
            for obj in self.ObjectList:
                newobj = obj.cloneObject()
                newobject.AddObject(newobj)
        elif isinstance(self, PointObject):
            newobject.XY = self.XY
        elif isinstance(self, (BezierObject, ClosedBezierObject)):
            newobject.PointsetList = self.PointsetList
        else:
            newobject.PointList = self.PointList
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
            
    def translate2(self, vector):
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
                self.transform.baseVal.insertItemBefore(t, 0)
                self.matrix = self.transform.baseVal.consolidate().matrix
            else:
                self.Update()

    def scale(self, xscale, yscale):
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.scale(xscale, yscale)
        else:
            t = svgbase.createSVGTransform()
            t.setScale(xscale, yscale)
            self.transformPoints(t.matrix)
            self.Update()

    def matrixtransform(self, matrix):
        if isinstance(self, GroupObject):
            for obj in self.ObjectList:
                obj.matrixtransform(matrix)
        else:
            self.transformPoints(matrix)
            if isinstance(self, (EllipseObject, RectangleObject)):
                print (self.matrix.a, self.matrix.b, self.matrix.c, self.matrix.d, self.matrix.e, self.matrix.f)
                self.matrix = matrix.multiply(self.matrix)
                print (self.matrix.a, self.matrix.b, self.matrix.c, self.matrix.d, self.matrix.e, self.matrix.f)
                t = svgbase.createSVGTransform()
                t.setMatrix(self.matrix)
                self.transform.baseVal.initialize(t)
            else:
                self.Update()

class LineObject(svg.line, SVGMixin):
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
        
    def translate(self, vector):
        for i in range(len(self.PointList)):
            self.PointList[i] += vector
        self.Update()
        
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

class PolylineObject(svg.polyline, SVGMixin):
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour=None):
        plist = " ".join([str(point[0])+","+str(point[1]) for point in pointlist])
        svg.polyline.__init__(self, points=plist, fill="none", style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]

    def Update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

    def translate(self, vector):
        for i in range(len(self.PointList)):
            self.PointList[i] += vector
        self.Update()
        
    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.Update()

    def AppendPoint(self, point):
        self.PointList.append(point)
        self.Update()

    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.Update()

class PolygonObject(svg.polygon, SVGMixin):
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        plist = " ".join([str(point[0])+","+str(point[1]) for point in pointlist])
        svg.polygon.__init__(self, points=plist, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]

    def Update(self):
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

    def translate(self, vector):
        for i in range(len(self.PointList)):
            self.PointList[i] += vector
        self.Update()
        
    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.Update()

    def AppendPoint(self, point):
        self.PointList.append(point)
        self.Update()
    
    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.Update()

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
        
class RectangleObject(svg.rect, SVGMixin):
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        [(x1, y1), (x2, y2)] = pointlist
        svg.rect.__init__(self, x=x1, y=y1, width=abs(x2-x1), height=abs(y2-y1), style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]
        self.matrix = None

    def Update(self):
        basepointlist = self.transformedPointList(self.matrix.inverse()) if self.matrix else self.PointList
        [(x1, y1), (x2, y2)] = basepointlist
        self.attrs["x"] = x1
        self.attrs["y"] = y1
        self.attrs["width"] = abs(x2-x1)
        self.attrs["height"] = abs(y2-y1)
        
    def translate(self, vector):
        for i in range(len(self.PointList)):
            self.PointList[i] += vector
        self.Update()
        
class EllipseObject(svg.ellipse, SVGMixin):
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        [(x1, y1), (x2, y2)] = pointlist
        svg.ellipse.__init__(self, cx=(x1+x2)/2, cy=(y1+y2)/2, rx=abs(x2-x1)/2, ry=abs(y2-y1)/2, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [Point(coords) for coords in pointlist]
        self.matrix = None
        #self.bind("mousedown", self.onLeftDown)
    
    def Update(self):
        basepointlist = self.transformedPointList(self.matrix.inverse()) if self.matrix else self.PointList
        [(x1, y1), (x2, y2)] = basepointlist
        self.attrs["cx"]=(x1+x2)/2
        self.attrs["cy"]=(y1+y2)/2
        self.attrs["rx"]=abs(x2-x1)/2
        self.attrs["ry"]=abs(y2-y1)/2

    def translate(self, vector):
        for i in range(len(self.PointList)):
            self.PointList[i] += vector
        self.Update()

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.Update()
    """
    def onLeftDown(self, event):
        self.Canvas.MouseOwner = self
        self.Canvas.StartPoint = self.Canvas.getSVGcoords(event)
    """
class CircleObject(svg.circle, SVGMixin):
    def __init__(self, centre=(0,0), radius=0, linecolour="black", linewidth=1, fillcolour="yellow"):
        (x, y) = centre
        svg.circle.__init__(self, cx=x, cy=y, r=radius, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = [(x, y), (x+radius, y)]
        self.Group = None

    def Update(self):
        [(x1, y1), (x2, y2)] = self.PointList
        self.attrs["cx"]=x1
        self.attrs["cy"]=y1
        self.attrs["r"]=((x2-x1)**2 + (y2-y1)**2)**0.5

    def translate(self, vector):
        for i in range(len(self.PointList)):
            self.PointList[i] += vector
        self.Update()

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        self.Update()

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.Update()

class BezierObject(svg.path, SVGMixin):
    def __init__(self, pointsetlist=[((0,0), (0,0))], linecolour="black", linewidth=1, fillcolour=None):
        ((x, y), (cx, cy)) = pointsetlist[0]
        plist = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in pointsetlist[1:] for c in p for x in c)
        svg.path.__init__(self, d=plist, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointsetList = [[Point(coords) for coords in pointset] for pointset in pointsetlist]
        self.PointList = [pointset[1] for pointset in self.PointsetList]
        self.PointList[0] = self.PointsetList[0][0]

    def Update(self):
        ((x, y), (cx, cy)) = self.PointsetList[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in self.PointsetList[1:] for c in p for x in c)
        self.PointList = [pointset[1] for pointset in self.PointsetList]
        self.PointList[0] = self.PointsetList[0][0]

    def translate(self, vector):
        for i in range(len(self.PointsetList)):
            for j in range(len(self.PointsetList[i])):
                self.PointsetList[i][j] += vector
        self.Update()
        
class ClosedBezierObject(svg.path, SVGMixin):
    def __init__(self, pointsetlist=[((0,0), (0,0), (0,0))], linecolour="black", linewidth=1, fillcolour="yellow"):
        ((c1x, c1y), (x, y), (c2x, c2y)) = pointsetlist[0]
        plist = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in pointsetlist[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        svg.path.__init__(self, d=plist, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointsetList = [[Point(coords) for coords in pointset] for pointset in pointsetlist]
        self.PointList = [pointset[1] for pointset in self.PointsetList]

    def Update(self):
        ((c1x, c1y), (x, y), (c2x, c2y)) = self.PointsetList[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in self.PointsetList[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        self.PointList = [pointset[1] for pointset in self.PointsetList]

    def translate(self, vector):
        for i in range(len(self.PointsetList)):
            for j in range(len(self.PointsetList[i])):
                self.PointsetList[i][j] += vector
        self.Update()

class SmoothBezierObject(BezierObject):
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour=None):
        pointsetlist = self.getpointsetlist(pointlist)
        BezierObject.__init__(self, pointsetlist, linecolour, linewidth, fillcolour)
        #self.PointList = [Point(coords) for coords in pointlist]
            
    def calculatecontrolpoints(self, points):
        [(x1, y1), (x2, y2), (x3, y3)] = points
        (dx1, dy1) = ((x2-x1), (y2-y1))
        (dx3, dy3) = ((x2-x3), (y2-y3))
        d1 = (dx1**2 + dy1**2)**0.5
        d2 = (dx3**2 + dy3**2)**0.5
        if d1 == 0 or d2 == 0: return ((x2, y2), (x2, y2))
        cos1, sin1 = dx1/d1, dy1/d1
        cos2, sin2 = dx3/d2, dy3/d2
        
        (c1x, c1y) = (x2 - d1*(cos1-cos2)/2, y2 - d1*(sin1-sin2)/2)
        (c2x, c2y) = (x2 + d2*(cos1-cos2)/2, y2 + d2*(sin1-sin2)/2)
        c1 = ((c1x+x2)/2, (c1y+y2)/2)
        c2 = ((c2x+x2)/2, (c2y+y2)/2)        
        return (c1, c2)
        
    def getpointsetlist(self, pointlist):
        if len(pointlist) == 2: return[pointlist, pointlist]
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            if i == 1:
                (x1, y1) = pointlist[0]
                (x2, y2) = c1
                pointsetlist = [(pointlist[0], ((x1+x2)/2, (y1+y2)/2))]
            pointsetlist.append((c1, pointlist[i], c2))
        (x1, y1) = pointlist[-1]
        (x2, y2) = c2
        pointsetlist.append((((x1+x2)/2, (y1+y2)/2), pointlist[-1]))
        #print (pointsetlist)
        return pointsetlist

    def SetPointset(self, i, pointset):
        self.PointList[i] = pointset[0] if i==0 else pointset[1]
        self.PointsetList[i] = pointset
        self.Update()

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

    def SetPoints(self, pointlist):
        #self.PointList = [Point(coords) for coords in pointlist]
        self.PointsetList = self.getpointsetlist(pointlist)
        self.Update()

    def SetFullPoints(self, pointsetlist):
        #self.PointList = [pset[1] for pset in pointsetlist]
        #self.PointList[0] = pointsetlist[0][0]
        self.PointsetList = pointsetlist        
        self.Update()

    def AppendPoint(self, point):
        self.PointList.append(point)
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()
   
    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

class SmoothClosedBezierObject(ClosedBezierObject):
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        pointsetlist = self.getpointsetlist(pointlist)
        ClosedBezierObject.__init__(self, pointsetlist, linecolour, linewidth, fillcolour)
        self.PointList = [Point(coords) for coords in pointlist]
            
    def calculatecontrolpoints(self, points):
        [(x1, y1), (x2, y2), (x3, y3)] = points
        (dx1, dy1) = ((x2-x1), (y2-y1))
        (dx3, dy3) = ((x2-x3), (y2-y3))
        d1 = (dx1**2 + dy1**2)**0.5
        d2 = (dx3**2 + dy3**2)**0.5
        if d1 == 0 or d2 == 0: return ((x2, y2), (x2, y2))
        cos1, sin1 = dx1/d1, dy1/d1
        cos2, sin2 = dx3/d2, dy3/d2
        
        (c1x, c1y) = (x2 - d1*(cos1-cos2)/2, y2 - d1*(sin1-sin2)/2)
        (c2x, c2y) = (x2 + d2*(cos1-cos2)/2, y2 + d2*(sin1-sin2)/2)
        c1 = ((c1x+x2)/2, (c1y+y2)/2)
        c2 = ((c2x+x2)/2, (c2y+y2)/2)        
        return (c1, c2)
        
    def getpointsetlist(self, pointlist):
        pointlist = [pointlist[-1]]+pointlist[:]+[pointlist[0]]
        #print (pointlist)
        #if len(pointlist) == 2: return[pointlist, pointlist]
        pointsetlist = []
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            pointsetlist.append((c1, pointlist[i], c2))
        #print (pointsetlist)
        return pointsetlist

    def SetPointset(self, i, pointset):
        self.PointList[i] = pointset[1]
        self.PointsetList[i] = pointset
        self.Update()

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

    def SetFullPoints(self, pointsetlist):
        self.PointList = [pset[1] for pset in pointsetlist]
        self.PointsetList = pointsetlist        
        self.Update()

    def AppendPoint(self, point):
        self.PointList.append(point)
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()
    
    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.PointsetList = self.getpointsetlist(self.PointList)
        self.Update()

class PointObject(svg.circle, SVGMixin):
    def __init__(self, XY=(0,0), colour="black", pointsize=2):
        (x, y) = XY
        svg.circle.__init__(self, cx=x, cy=y, r=pointsize, style={"stroke":colour, "strokeWidth":1, "fill":colour})
        self._XY = None
        self.XY = Point(XY)

    def Update(self):
        pass

    def translate(self, vector):
        self.XY = self.XY+vector

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

class GroupObject(svg.g, SVGMixin):
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

    def translate(self, vector):
        for obj in self.ObjectList:
            obj.translate(vector)

    @property
    def Canvas(self):
        return self._Canvas

    @Canvas.setter
    def Canvas(self, canvas):
        self._Canvas = canvas
        for obj in self.ObjectList:
            obj.Canvas = canvas

class CanvasObject(svg.svg):
    def __init__(self, width, height, colour="white"):
        svg.svg.__init__(self, style={"width":width, "height":height, "backgroundColor":colour})
        self.MouseOwner = None
        self.MouseAction = 0
        self.ObjectDict = {}
        self.Cursors = ["auto", "move", "url(brySVG/rotate.png), auto", "col-resize", "row-resize", "url(brySVG/enlarge.png), auto"]
        self.TransformOrigin = None
        self.Snap = None
        self.RotateSnap = None
        self.bind("mousedown", self.onLeftDown)
        self.bind("mousemove", self.onMouseMove)
        self.bind("mouseup", self.onLeftUp)
        self.bind("dragstart", self.onDragStart)

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

    def setMouseAction(self, n):
        self.MouseAction = n
        self.style.cursor = self.Cursors[n]
    
    def onRightClick(self, event):
        event.preventDefault()
        self.setMouseAction((self.MouseAction+1)%6)

    def onDragStart(self, event):
        event.preventDefault()        
    
    def onMouseMove(self, event):
        if not self.MouseOwner or self.MouseAction == 0: return
        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.StartPoint
        (cx, cy) = self.MouseOwnerCentre
        (x1, y1) = currentcoords - self.MouseOwnerCentre
        (x2, y2) = self.StartPoint - self.MouseOwnerCentre
        self.StartPoint = currentcoords
        if self.MouseAction == 1:
            self.MouseOwner.translate(offset)
        elif self.MouseAction == 2:
            matrix = self.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix = matrix.rotateFromVector(x1*x2+y1*y2, x2*y1-x1*y2)
            matrix = matrix.translate(-cx, -cy)
            self.MouseOwner.matrixtransform(matrix)
        elif self.MouseAction == 3:
            matrix = self.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix.a = x1/x2
            matrix = matrix.translate(-cx, -cy)
            self.MouseOwner.matrixtransform(matrix)
        elif self.MouseAction == 4:
            matrix = self.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix.d = y1/y2
            matrix = matrix.translate(-cx, -cy)
            self.MouseOwner.matrixtransform(matrix)
        elif self.MouseAction == 5:
            matrix = self.createSVGMatrix()
            matrix = matrix.translate(cx, cy)
            matrix = matrix.scale((x1**2+y1**2)**0.5/(x2**2+y2**2)**0.5)
            matrix = matrix.translate(-cx, -cy)
            print (matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f)
            self.MouseOwner.matrixtransform(matrix)

    def onLeftDown(self, event):
        print (self.MouseAction, event.button, event.target, event.target.id)
        if self.MouseAction == 0 or event.button > 0 or event.target.id == "": return
        svgobj = self.ObjectDict[event.target.id]
        self <= svgobj
        while getattr(svgobj, "Group", None):
            svgobj = svgobj.Group 
        self.MouseOwner = svgobj
        bbox = self.MouseOwner.getBBox()
        (cx, cy) = self.MouseOwnerCentre = Point((bbox.x+bbox.width/2, bbox.y+bbox.height/2))
        self.StartPoint = self.getSVGcoords(event)
        if self.MouseAction == 1: return
        if self.MouseAction in [2, 5]:
            self.TransformOrigin = PointObject(self.MouseOwnerCentre, colour="blue", pointsize=3)
        elif self.MouseAction == 3:
            self.TransformOrigin = LineObject([(cx, bbox.y), (cx, bbox.y+bbox.height)], linecolour="blue", linewidth=2)
        elif self.MouseAction == 4:
            self.TransformOrigin = LineObject([(bbox.x, cy), (bbox.x+bbox.width, cy)], linecolour="blue", linewidth=2)
        self <= self.TransformOrigin
            
    def onLeftUp(self, event):
        print (self.MouseAction, event.button, event.target, event.target.id)
        if self.MouseAction == 0 or event.button > 0: return
        if self.TransformOrigin:
            delete(self.TransformOrigin)
            self.TransformOrigin = None
        if not (getattr(self.MouseOwner, "PointList", None) and self.Snap):
            self.MouseOwner = None
            return
        if self.RotateSnap:
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
                                        matrix = self.createSVGMatrix()
                                        matrix = matrix.rotate(diff*180/pi)
                                        self.MouseOwner.matrixtransform(matrix)
                                        print (self.ObjectDict[objid].PointList[i], self.MouseOwner.PointList[j])
                                        (dx, dy) = self.ObjectDict[objid].PointList[i] - self.MouseOwner.PointList[j]
                                        print (dx, dy)
                                        self.MouseOwner.translate((dx, dy))
                                        self.MouseOwner = None
                                        return
                            if not bestdx or hypot(dx, dy) < hypot(bestdx, bestdy): (bestdx, bestdy) = (dx, dy)
            if bestdx: 
                self.MouseOwner.translate((bestdx, bestdy))
            self.MouseOwner = None
            return

        elif self.Snap:
            for objid in self.ObjectDict:
                if objid == self.MouseOwner.id: continue
                if not getattr(self.ObjectDict[objid], "PointList", None): continue
                for point1 in self.ObjectDict[objid].PointList:
                    for point2 in self.MouseOwner.PointList:
                        (dx, dy) = point1 - point2
                        if abs(dx) < self.Snap and abs(dy) < self.Snap:
                            self.MouseOwner.translate((dx, dy))
                            self.MouseOwner = None
                            return
            self.MouseOwner = None
                
                

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

    def rotate(self, element, angle, centre=None):
        if not centre: 
            bbox = element.getBBox()
            centre = (bbox.x+bbox.width/2, bbox.y+bbox.height/2)
        t = svgbase.createSVGTransform()
        t.setRotate(angle, *centre)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def translate(self, element, vector):
        t = svgbase.createSVGTransform()
        t.setTranslate(*vector)
        element.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix
        
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
