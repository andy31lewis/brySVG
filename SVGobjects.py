#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Andy Lewis                                               #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License version 2 as published by #
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,     #
# MA 02111-1307 USA                                                           #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY. See the GNU General Public License for more details.          #

import browser.svg as svg
from browser import alert
svgbase = svg.svg()

class SVGMixin(object):
    def cloneObject(self):
        newobject = self.__class__()
        if isinstance(newobject, GroupObject):
            newobject.ObjectList = []
            for obj in self.ObjectList:
                newobj = obj.cloneObject()
                newobject <= newobj
                newobject.ObjectList.append(newobj)
        for (key, value) in self.attrs.items():
            newobject.attrs[key] = value
        return newobject

    def translate(self, vector):
        t = svgbase.createSVGTransform()
        t.setTranslate(*vector)
        self.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix
        
    def rotate(self, angle, centre=(0,0)):
        t = svgbase.createSVGTransform()
        t.setRotate(angle, *centre)
        self.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

    def scale(self, xscale, yscale):
        t = svgbase.createSVGTransform()
        t.setScale(xscale, yscale)
        self.transform.baseVal.insertItemBefore(t, 0)
        return t.matrix

class LineObject(svg.line):
    def __init__(self, point1, point2, style="solid"):
        (x1, y1) = point1
        (x2, y2) = point2
                
        if style == "faintdash1":
            dasharray = "10,5"
            colour = "grey"
        elif style == "faintdash2":
            dasharray = "2,2"
            colour = "lightgrey"
        else:
            dasharray = None
            colour = "black"

        svg.line.__init__(self, x1=x1, y1=y1, x2=x2, y2=y2, stroke=colour, stroke_dasharray=dasharray, stroke_width="1")

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

class PolylineObject(svg.polyline):
    def __init__(self, pointlist, linecolour="black", linewidth=1, fillcolour=None):
        plist = " ".join([str(point[0])+","+str(point[1]) for point in pointlist])
        svg.polyline.__init__(self, points=plist, fill="none", style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = pointlist[:]

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in pointlist])

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

    def AppendPoint(self, point):
        self.PointList.append(point)
        print (self.PointList)
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

class PolygonObject(svg.polygon, SVGMixin):
    def __init__(self, pointlist=[(0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        plist = " ".join([str(point[0])+","+str(point[1]) for point in pointlist])
        svg.polygon.__init__(self, points=plist, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList = pointlist[:]

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in pointlist])

    def SetPoint(self, i, point):
        self.PointList[i] = point
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])

    def AppendPoint(self, point):
        self.PointList.append(point)
        #print (self.PointList)
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])
    
    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        self.attrs["points"] = " ".join([str(point[0])+","+str(point[1]) for point in self.PointList])
        

class RectangleObject(svg.rect):
    def __init__(self, point1, point2, linecolour="black", linewidth=1, fillcolour="yellow"):
        (x1, y1) = point1
        (x2, y2) = point2
        svg.rect.__init__(self, x=x1, y=y1, width=x2-x1, height=y2-y1, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})

class EllipseObject(svg.ellipse, SVGMixin):
    def __init__(self, pointlist=[(0,0), (0,0)], linecolour="black", linewidth=1, fillcolour="yellow"):
        [(x1, y1), (x2, y2)] = pointlist
        svg.ellipse.__init__(self, cx=(x1+x2)/2, cy=(y1+y2)/2, rx=abs(x2-x1)/2, ry=abs(y2-y1)/2, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        self.PointList=pointlist[:]
    
    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        (x1, y1) = self.PointList[0]; (x2, y2) = self.PointList[1]
        self.attrs["cx"]=(x1+x2)/2
        self.attrs["cy"]=(y1+y2)/2
        self.attrs["rx"]=abs(x2-x1)/2
        self.attrs["ry"]=abs(y2-y1)/2

    def SetPoint(self, i, point):
        self.PointList[i] = point
        (x1, y1) = self.PointList[0]; (x2, y2) = self.PointList[1]
        self.attrs["cx"]=(x1+x2)/2
        self.attrs["cy"]=(y1+y2)/2
        self.attrs["rx"]=abs(x2-x1)/2
        self.attrs["ry"]=abs(y2-y1)/2

class CircleObject(svg.circle):
    def __init__(self, centre, radius, linecolour="black", linewidth=1, fillcolour="yellow"):
        (x, y) = centre
        svg.circle.__init__(self, cx=x, cy=y, r=radius, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})

class BezierObject(svg.path):
    def __init__(self, fullpointlist, linecolour="black", linewidth=1, fillcolour=None):
        ((x, y), (cx, cy)) = fullpointlist[0]
        plist = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)
        svg.path.__init__(self, d=plist, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        
class ClosedBezierObject(svg.path):
    def __init__(self, fullpointlist, linecolour="black", linewidth=1, fillcolour="yellow"):
        ((c1x, c1y), (x, y), (c2x, c2y)) = fullpointlist[0]
        plist = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        svg.path.__init__(self, d=plist, style={"stroke":linecolour, "strokeWidth":linewidth, "fill":fillcolour})
        
class SmoothBezierObject(BezierObject):
    def __init__(self, pointlist, linecolour="black", linewidth=1, fillcolour=None):
        fullpointlist = self.getfullpointlist(pointlist)
        BezierObject.__init__(self, fullpointlist, linecolour, linewidth, fillcolour)
        self.PointList = pointlist[:]
        self.FullPointList = fullpointlist
            
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
        
    def getfullpointlist(self, pointlist):
        if len(pointlist) == 2: return[pointlist, pointlist]
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            if i == 1:
                (x1, y1) = pointlist[0]
                (x2, y2) = c1
                fullpointlist = [(pointlist[0], ((x1+x2)/2, (y1+y2)/2))]
            fullpointlist.append((c1, pointlist[i], c2))
        (x1, y1) = pointlist[-1]
        (x2, y2) = c2
        fullpointlist.append((((x1+x2)/2, (y1+y2)/2), pointlist[-1]))
        #print (fullpointlist)
        return fullpointlist

    def SetPointset(self, i, pointset):
        self.PointList[i] = pointset[0] if i==0 else pointset[1]
        self.FullPointList[i] = pointset
        ((x, y), (cx, cy)) = self.FullPointList[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in self.FullPointList[1:] for c in p for x in c)

    def SetPoint(self, i, point):
        self.PointList[i] = point
        fullpointlist = self.getfullpointlist(self.PointList)
        ((x, y), (cx, cy)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)
        self.FullPointList = fullpointlist

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        fullpointlist = self.getfullpointlist(self.PointList)
        ((x, y), (cx, cy)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)
        self.FullPointList = fullpointlist

    def SetFullPoints(self, fullpointlist):
        self.PointList = [pset[1] for pset in fullpointlist]
        self.PointList[0] = fullpointlist[0][0]
        ((x, y), (cx, cy)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)
        self.FullPointList = fullpointlist        

    def AppendPoint(self, point):
        self.PointList.append(point)
        fullpointlist = self.getfullpointlist(self.PointList)
        ((x, y), (cx, cy)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)
        self.FullPointList = fullpointlist
    
    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        fullpointlist = self.getfullpointlist(self.PointList)
        ((x, y), (cx, cy)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(cx)+" "+str(cy)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)
        self.FullPointList = fullpointlist

class SmoothClosedBezierObject(ClosedBezierObject):
    def __init__(self, pointlist, linecolour="black", linewidth=1, fillcolour="yellow"):
        fullpointlist = self.getfullpointlist(pointlist)
        ClosedBezierObject.__init__(self, fullpointlist, linecolour, linewidth, fillcolour)
        self.PointList = pointlist[:]
        self.FullPointList = fullpointlist
            
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
        
    def getfullpointlist(self, pointlist):
        pointlist = [pointlist[-1]]+pointlist[:]+[pointlist[0]]
        #print (pointlist)
        #if len(pointlist) == 2: return[pointlist, pointlist]
        fullpointlist = []
        for i in range(1, len(pointlist)-1):
            (c1, c2) = self.calculatecontrolpoints(pointlist[i-1:i+2])
            fullpointlist.append((c1, pointlist[i], c2))
        #print (fullpointlist)
        return fullpointlist

    def SetPointset(self, i, pointset):
        self.PointList[i] = pointset[1]
        self.FullPointList[i] = pointset
        ((c1x, c1y), (x, y), (c2x, c2y)) = self.FullPointList[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in self.FullPointList[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))

    def SetPoint(self, i, point):
        self.PointList[i] = point
        fullpointlist = self.getfullpointlist(self.PointList)
        ((c1x, c1y), (x, y), (c2x, c2y)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        self.FullPointList = fullpointlist

    def SetPoints(self, pointlist):
        self.PointList = [Point(coords) for coords in pointlist]
        fullpointlist = self.getfullpointlist(self.PointList)
        ((c1x, c1y), (x, y), (c2x, c2y)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        self.FullPointList = fullpointlist

    def SetFullPoints(self, fullpointlist):
        self.PointList = [pset[1] for pset in fullpointlist]
        ((c1x, c1y), (x, y), (c2x, c2y)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        self.FullPointList = fullpointlist        

    def AppendPoint(self, point):
        self.PointList.append(point)
        fullpointlist = self.getfullpointlist(self.PointList)
        ((c1x, c1y), (x, y), (c2x, c2y)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        self.FullPointList = fullpointlist
    
    def DeletePoints(self, start, end):
        del self.PointList[slice(start, end)]
        fullpointlist = self.getfullpointlist(self.PointList)
        ((c1x, c1y), (x, y), (c2x, c2y)) = fullpointlist[0]
        self.attrs["d"] = "M"+str(x)+" "+str(y)+" C"+str(c2x)+" "+str(c2y)+" "+" ".join(str(x) for p in fullpointlist[1:] for c in p for x in c)+" "+" ".join(str(x) for x in (c1x, c1y, x, y))
        self.FullPointList = fullpointlist

class PointObject(svg.circle):
    def __init__(self, XY, colour="black", pointsize=2):
        (x, y) = XY
        svg.circle.__init__(self, cx=x, cy=y, r=pointsize, style={"stroke":colour, "strokeWidth":1, "fill":colour})
        self._XY = None
        self.XY = Point(XY)

    @property
    def XY(self):
        return self._XY

    @XY.setter
    def XY(self, XY):
        self._XY = Point(XY)
        self.attrs["cx"] = self._XY[0]
        self.attrs["cy"] = self._XY[1]

class GroupObject(svg.g, SVGMixin):
    def __init__(self, objlist=[], id=None):
        svg.g.__init__(self)
        if id: self.attrs["id"] = id
        for obj in objlist:
            self <= obj
        self.ObjectList = objlist

    def AddObject(self, svgobject):
        self <= svgobject
        self.ObjectList.append(svgobject)

    def ClearAll(self):
        while self.firstChild:
            self.removeChild(self.firstChild)
        self.ObjectList = []

class CanvasObject(svg.svg):
    def __init__(self, width, height, colour="white"):
        svg.svg.__init__(self, width=width, height=height, style={"backgroundColor":colour})
    
    def AddObject(self, SVGObject):
        self <= SVGObject
        return SVGObject
    
    def ClearAll(self):
        while self.firstChild:
            self.removeChild(self.firstChild)

class Point(object):
    def __init__(self, coords):
        self.coords = coords.coords if isinstance(coords, Point) else coords

    def __str__(self):
        return str(tuple(self.coords))

    def __add__(self, other):
        return Point([xi+yi for (xi, yi) in zip(self.coords, other.coords)])

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
