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

from math import sin, cos, atan2, pi, log10, floor, inf
from .transformcanvas import *
import time

class Enum(list):
    def __init__(self, name, string):
        values = string.split()
        for i, value in enumerate(values):
            setattr(self, value, i)
            self.append(i)

Position = Enum ('Position', 'CONTAINS INSIDE OVERLAPS EQUAL DISJOINT TOUCHING')
dp = 2

class ListDict(dict):
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            self[key] = []
            return self[key]

class SetDict(dict):
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            self[key] = set()
            return self[key]

class Segment(object):
    def __init__(self, startpoint, endpoint, poly, index):
        if endpoint < startpoint:
            self.leftpoint, self.rightpoint = endpoint, startpoint
            self.leftindex, self.rightindex = reversed(index)
        else:
            self.leftpoint, self.rightpoint = startpoint, endpoint
            self.leftindex, self.rightindex = index

        self.leftx, self.lefty = self.leftpoint
        self.rightx, self.righty = self.rightpoint
        (self.top, self.bottom) = (self.righty, self.lefty) if self.righty<self.lefty else (self.lefty, self.righty)
        self.poly = poly
        self.index = index
        self.dx, self.dy = self.rightx-self.leftx, self.righty-self.lefty
        self.gradient = inf if self.dx == 0 else self.dy/self.dx
        self.angle = atan2(self.dy, self.dx)-pi/2+pi*(self.dy<0)
        self.y = self.lefty
        self.xpos = "L"

    def __repr__(self):
        return f"{self.poly}{self.index}: [{self.leftpoint}, {self.rightpoint}]; currenty: {self.y}, xpos: {self.xpos}, gradient: {self.gradient}"

class Intersection(object):
    def __init__(self, poly1, index1, poly2, index2, point=None):
        self.polyrefs = {(poly1, index1), (poly2, index2)}
        self.poly1 = poly1
        self.index1 = index1
        self.poly2 = poly2
        self.index2 = index2
        self.point = point if point is not None else Point((0, 0))

    def __repr__(self):
        s = f"{round(self.point,1)} \n"
        refs = sorted(self.polyrefs, key = lambda ref: ref[0].id)
        for (poly, index) in refs:
            if isinstance(index, int):
                s += f"at vertex {index} on polygon {poly}\n"
            else:
                i1, i2 = index
                s += f"between vertices {i1} and {i2} on polygon {poly}\n"
        return s

class PolygonMixin(object):
    def containspoint(self, point, dp=1):
        '''Returns "interior" if point is inside the polygon, "edge" if it is on an edge,
        "vertex" if it is at a vertex, or False otherwise.
        dp is the precision to which the coordinates of the vertices are used.'''
        poly = getattr(poly, "pointList", poly)
        poly = [(round(x,dp), round(y,dp)) for (x, y) in poly]
        point = getattr(point, "XY", point)
        (x, y) = (round(point[0],dp), round(point[1],dp))
        if (x, y) in poly: return "vertex"
        length = len(poly)
        counter = 0
        (x1, y1) = poly[0]
        for i in range(1, length+1):
            (x2, y2) = poly[i%length]
            if x1 == x2 == x and min(y1,y2)<=y<=max(y1,y2): return "edge"
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
        '''Returns the area of the PolygonObject'''
        return _area(self.pointList)

    def isEqual(self, other):
        '''Returns True if poly1 is identical to poly2, False otherwise.'''
        return _equalpolygons(self.pointList, other.pointList)

    def positionRelativeTo(self, other):
        '''Returns an Enum value: Position.CONTAINS, Position.INSIDE, Position.OVERLAPS, Position.DISJOINT or Position.EQUAL.
        other is another PolygonObject.'''
        return relativeposition(self, other)

    def getIntersections(self, other):
        '''Returns a list of Intersection objects. Each Intersection has 3 attributes:
        .point: a Point whose coordinates are the intersection
        .selfindex: if this is an integer i, the intersection is at a vertex of self, namely self.pointList[i]
                    if this is a tuple (i-1, i), the intersection is between self.pointList[i-1] and self.pointList[i]
        .otherindex: same as selfindex but describes the location of the intersection on the other polygon.
        '''
        return findintersections([self, other])

    def merge(self, other):
        return boundary([self, other])

class PolygonGroup(GroupObject, PolygonMixin):
    def __init__(self, objlist=[]):
        self.boundary = None
        self.update()
        super().__init__(objlist)

    def __repr__(self):
        return f"group {self.id}" if self.id else f"group {id(self)}"

    def __str__(self):
        return self.__repr__()

    def addObject(self, svgobject, objid=None):
        if not isinstance(svgobject, (PolygonObject, PolygonGroup)): return False
        if self.objectList == []:
            self.boundary = PolygonObject(svgobject.pointList)
        else:
            newboundary = self.boundary.merge(svgobject)
            if newboundary is False:
                return False
            elif newboundary is None:
                return None
            else:
                self.boundary = newboundary

        super().addObject(svgobject, objid)
        self.update()
        return True

    def addObjects(self, polylist):
        if polylist == []: return None
        if self.boundary: polylist.append(self.boundary)
        newboundary = boundary(polylist)
        if newboundary is False:
            return False
        elif newboundary is None:
            return None
        else:
            self.boundary = newboundary
        super().addObjects(polylist)
        self.update()
        return True

    def removeObject(self, svgobject):
        if not self.contains(svgobject): return
        groupcopy = self.objectList[:]
        groupcopy.remove(svgobject)
        newboundary = boundary(groupcopy)
        if newboundary is False:
            return False
        elif newboundary is None:
            return None
        else:
            self.boundary = newboundary
        super().removeObject(svgobject)
        self.update()
        return True

    def deleteAll(self):
        self.boundary = None
        self.update()
        super().deleteAll()

    def update(self):
        self.pointList = [] if self.boundary is None else self.boundary.pointList

    def matrixTransform(self, matrix):
        self.boundary.matrixTransform(matrix)
        super().matrixTransform(matrix)
        #print("Pointlist after drag/rotate", self.pointList)

    def cloneObject(self):
        newobject = super().cloneObject()
        newobject.boundary = self.boundary.cloneObject()
        newobject.update()
        return newobject

class PolygonCanvasMixin(object):
    def doEdgeSnap(self, svgobject):
        tt = time.time()
        #try:
        #    self.deleteObject(self.objectDict["centre"])
        #except KeyError:
        #    pass
        if not hasattr(svgobject, "pointList"): return
        bbox = svgobject.getBBox()
        L, R, T, B = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
        snapangle = self.snapAngle*pi/180
        snapd = self.snapDistance
        bestangle = None
        L = len(svgobject.pointList)
        objsegments = [Segment(svgobject.pointList[i-1], svgobject.pointList[i], svgobject, ((i-1)%L, i)) for i in range(L)]
        objsegs = sorted(objsegments, key = lambda seg: seg.angle)
        for seg in objsegs:
            if seg.angle > snapangle - pi/2: break
            newseg = Segment(seg.leftpoint, seg.rightpoint, seg.poly, seg.index)
            newseg.angle = seg.angle + pi
            objsegs.append(newseg)
        checksegs = []
        for objid in self.objectDict:
            if objid == svgobject.id: continue
            obj = self.objectDict[objid]
            if getattr(obj, "group", None): continue
            if not isinstance(obj, (PolygonObject, PolygonGroup)): continue
            bbox = obj.getBBox()
            L1, R1, T1, B1 = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
            if L1-R > snapd or R1-L < -snapd or T1-B > snapd or B1-T < -snapd: continue
            L = len(obj.pointList)
            objsegments = [Segment(obj.pointList[i-1], obj.pointList[i], obj, ((i-1)%L, i)) for i in range(L)]
            checksegs.extend(objsegments)
        checksegs.sort(key = lambda seg: seg.angle)
        #print("objsegs")
        #for seg in objsegs:
            #print(seg)
        #print("checksegs")
        #for seg in checksegs:
            #print(seg)
        checkstart = 0
        piby4 = pi/4
        found = False
        for i, seg1 in enumerate(objsegs):
            angle1 = seg1.angle
            #print("\nChecking:", angle1)
            checksegs = checksegs[checkstart:]
            if not checksegs: break
            #print("check angles", [seg.angle for seg  in checksegs])
            try:
                tonextangle = objsegs[i+1].angle - angle1
            except IndexError:
                tonextangle = 0
            #print("tonextangle", tonextangle)
            checkstart = 0
            for seg2 in checksegs:
                angle2 = seg2.angle
                #print("Against:", angle2)
                angled = angle2 - angle1
                #print("Current best angle", bestangle)
                #print("angled", angled)
                absangle = abs(angled)
                if (bestangle is None and absangle < snapangle) or (bestangle is not None and absangle < bestangle):
                    #print("Angles close enough")
                    (objleft, objright) = (seg1.leftx, seg1.rightx)
                    (objtop, objbottom) = (seg1.top, seg1.bottom)
                    (checkleft, checkright) = (seg2.leftx-snapd, seg2.rightx+snapd)
                    (checktop, checkbottom) = (seg2.top-snapd, seg2.bottom+snapd)
                    if not (objleft > checkright or objright < checkleft or objtop > checkbottom or objbottom < checktop):
                        objp, objq = seg1.leftpoint, seg1.rightpoint
                        checkp, checkq = seg2.leftpoint, seg2.rightpoint
                        #print("Not disjoint segments")
                        #print("obj:", seg1)
                        #print("check:", seg2)
                        objv, checkv = objq-objp, checkq-checkp
                        diff, product = checkp - objp, objv.cross(checkv)
                        (t, u) = (diff.cross(objv)/product, diff.cross(checkv)/product) if product != 0 else (inf, inf)
                        #print("t and u", t, u)
                        if 0<=t<=1 and 0<=u<=1:
                            (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, objp + u*objv, (0, 0), seg1, seg2)
                        else:
                            bestd = None
                            (objx1, objy1), (objx2, objy2) = objp, objq
                            (checkx1, checky1), (checkx2, checky2) = checkp, checkq
                            if abs(angle2) < piby4:
                                if checktop <= objy1 <= checkbottom:
                                    checkx = checkx1 + (objy1-checky1)/(checky2-checky1)*(checkx2-checkx1)
                                    diff = checkx-objx1
                                    #print("Checking objx1", objx1, checkx, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (objx1, objy1), (diff, 0), seg1, seg2)
                                if checktop <= objy2 <= checkbottom:
                                    checkx = checkx1 + (objy2-checky1)/(checky2-checky1)*(checkx2-checkx1)
                                    diff = checkx-objx2
                                    #print("Checking objx2", objx2, checkx, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (objx2, objy2), (diff, 0), seg1, seg2)
                            else:
                                if checkleft <= objx1 <= checkright:
                                    checky = checky1 + (objx1-checkx1)/(checkx2-checkx1)*(checky2-checky1)
                                    diff = checky-objy1
                                    #print("Checking objy1", objy1, checky, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (objx1, objy1), (0, diff), seg1, seg2)
                                if checkleft <= objx2 <= checkright:
                                    checky = checky1 + (objx2-checkx1)/(checkx2-checkx1)*(checky2-checky1)
                                    diff = checky-objy2
                                    #print("Checking objy2", objy2, checky, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (objx2, objy2), (0, diff), seg1, seg2)
                            if abs(angle1) < piby4:
                                if objtop <= checky1 <= objbottom:
                                    objx = objx1 + (checky1-objy1)/(objy2-objy1)*(objx2-objx1)
                                    diff = checkx1-objx
                                    #print("Checking checkx1", checkx1, objx, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (objx, checky1), (diff, 0), seg1, seg2)
                                if objtop <= checky2 <= objbottom:
                                    objx = objx1 + (checky2-objy1)/(objy2-objy1)*(objx2-objx1)
                                    diff = checkx2-objx
                                    #print("Checking checkx2", checkx2, objx, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (objx, checky2), (diff, 0), seg1, seg2)
                            else:
                                if objleft <= checkx1 <= objright:
                                    objy = objy1 + (checkx1-objx1)/(objx2-objx1)*(objy2-objy1)
                                    diff = checky1-objy
                                    #print("Checking checky1", checky1, objy, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (checkx1, objy), (0, diff), seg1, seg2)
                                if objleft <= checkx2 <= objright:
                                    objy = objy1 + (checkx2-objx1)/(objx2-objx1)*(objy2-objy1)
                                    diff = checky2-objy
                                    #print("Checking checky2", checky2, objy, diff)
                                    if (bestd is None and abs(diff) <= snapd) or (bestd is not None and abs(diff) < bestd):
                                        (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, (checkx2, objy), (0, diff), seg1, seg2)
                #if bestangle: print("Current best angle and vector", angled, vector)
                if tonextangle - angled > snapangle:
                    checkstart += 1
                    #print("New checkstart", checkstart)
                if angled > snapangle:
                    #print("Finished checking", angle1)
                    break
                if bestangle == 0:
                    found = True
                    break
            if found: break

        if bestangle is not None:
            #print("Angle, centre, vector", angle*180/pi, centre, vector)
            if not (angle ==0 and vector == (0, 0)): svgobject.rotateandtranslate(angle*180/pi, centre, vector)
            if not self.vertexSnap: return
            #transformmemo.clear()
            objpoints = [svgobject.pointList[objseg.leftindex], svgobject.pointList[objseg.rightindex]]
            checkpoints = [checkseg.leftpoint, checkseg.rightpoint]
            pointpairs = [(p1, p2) for p1 in objpoints for p2 in checkpoints]
            for (point1, point2) in pointpairs:
                (dx, dy) = point2 - point1
                if abs(dx) < snapd and abs(dy) < snapd:
                    #print(f"Snap {point1} to {point2}")
                    svgobject.translate((dx, dy))
                    break
        elif self.vertexSnap:
            self.doVertexSnap(svgobject)
        print("rotatesnap", time.time()-tt)

def _compareboundingboxes(poly1, poly2, xdp=None, ydp=None):
    def getboundingbox(poly):
        xcoords = [round(x, xdp) for (x,y) in poly] if xdp else [x for (x,y) in poly]
        left = min(xcoords)
        right = max(xcoords)
        ycoords = [round(y, ydp) for (x,y) in poly] if ydp else [y for (x,y) in poly]
        top = min(ycoords)
        bottom = max(ycoords)
        return (left, top), (right, bottom)

    if xdp and not ydp: ydp = xdp
    ((left1, top1), (right1, bottom1)) = getboundingbox(poly1)
    ((left2, top2), (right2, bottom2)) = getboundingbox(poly2)
    if right1 < left2 or right2 < left1 or bottom1 < top2 or bottom2 < top1: return Position.DISJOINT
    if right1 == left2 or right2 == left1 or bottom1 == top2 or bottom2 == top1: return Position.TOUCHING
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

def _area(poly):
    '''Returns the area of a polygon given as a list of coordinates'''
    area = 0
    (x0, y0) = poly[-1]
    for (x1, y1) in poly:
        area += x1*y0 - x0*y1
        (x0, y0) = (x1, y1)
    return abs(area/2)

def _equalpolygons(poly1, poly2):
    '''Returns True if poly1 is identical to poly2, False otherwise.
    poly1 and poly2 are lists of vertex coordinates.'''
    start1 = poly1.index(min(poly1))
    poly1 =  poly1[start1+1:]+poly1[:start1]
    start2 = poly2.index(min(poly2))
    poly2 =  poly2[start2+1:]+poly2[:start2]
    return poly1 == poly2 or poly1 == poly2[::-1]

def _getrotatedcoords(polylist, xdp):
    def getbestangle(polylist):
        anglesfromvertical = []
        for poly in polylist:
            vecs = [poly.pointList[i] - poly.pointList[i-1] for i in range(len(poly.pointList))]
            anglesfromvertical.extend([abs(atan2(dy, dx)-pi/2+pi*(dy<0)) for (dx, dy) in vecs])
        if 0 not in anglesfromvertical: return 0
        positiveangles = [a for a in anglesfromvertical if a>0.1]
        return min(positiveangles)/2

    a = getbestangle(polylist)
    cosa, sina = cos(a), sin(a)
    #print("Best angle", a*180/pi)
    dp1 = xdp+1
    #print(f"Before rotation:\nPoly1: {self.pointList}\nPoly2: {other.pointList}")
    coordslists = []
    for poly in polylist:
        polyrounded = [(round(x, dp1), round(y, dp1)) for (x, y) in poly.pointList]
        #print(f"After rounding before rotation:\nPoly1: {poly1}\nPoly2: {poly2}")
        polyrotated = poly.pointList if a == 0 else [(x*cosa-y*sina, x*sina+y*cosa) for (x, y) in polyrounded]
        #print(f"After rotation:\nPoly1: {poly1rotated}\nPoly2: {poly2rotated}")

        coords = [(round(x, xdp), y) for (x, y) in polyrotated]
        coordslists.append(coords)
        #print(f"After rotation and rounding:\nPoly1: {coords1}\nPoly2: {coords2}")
    return coordslists

def _getsortedsegments(polylist, coordslists):
    segments = []
    for poly, coordslist in zip(polylist, coordslists):
        L = len(coordslist)
        segments.extend([Segment(coordslist[i-1], coordslist[i], poly, ((i-1)%L, i)) for i in range(L)])
    segments.sort(key = lambda seg: (seg.leftx, round(seg.lefty, dp), seg.gradient))
    return segments

def mergelists(list1,list2):
    if not list1:  return list(list2)
    if not list2:  return list(list1)

    list1iter, list2iter = iter(list1), iter(list2)
    item1 = next(list1iter)
    item2 = next(list2iter)
    result = []

    while item1:
        while item2 and (item2.y < item1.y or (item2.y == item1.y and item1.xpos != "R" and item2.gradient < item1.gradient)):
            result.append(item2)
            item2 = next(list2iter, None)
        result.append(item1)
        item1 = next(list1iter, None)
    if item2:
        result.append(item2)
        result.extend(list2iter)
    return result

def relativeposition(self, other):
    '''Returns an Enum value: Position.CONTAINS, Position.INSIDE, Position.OVERLAPS, Position.DISJOINT or Position.EQUAL.
    other is another PolygonObject.'''
    def sweeppast(x, latestoutcome, livesegments):
        #print("\nXvalue", x, "\nLive segments:\n", "\n".join(str(seg) for seg in livesegments), "\nCurrent Outcome", latestoutcome)
        for seg in livesegments:
            if seg.rightx == x:
                seg.y = round(seg.righty, dp2)
            else:
                seg.y = round(seg.lefty + (x-seg.leftx)*seg.gradient, dp2)

        for i, seg in enumerate(livesegments):
            for seg2 in livesegments[i+1:]:
                #print("Comparing", seg, "with", seg2)
                if seg.y == inf or seg2.y == inf: continue
                if seg.y > seg2.y and seg.poly != seg2.poly:
                    #print("Found Intersection:", seg, seg.y, seg2, seg2.y)
                    return Position.OVERLAPS, None
        livesegments = [seg for seg in livesegments if seg.rightx > x]

        while unusedsegments and unusedsegments[0].leftx == x:
            newseg = unusedsegments.pop(0)
            newseg.y = round(newseg.lefty, dp2)
            livesegments.append(newseg)
        livesegments.sort(key=lambda seg: (seg.y, seg.gradient))
        #print("Updated live segments:\n", "\n".join(str(seg) for seg in livesegments))

        yvaluesA = [seg.y for seg in livesegments if seg.poly == polyA]
        intervalsA = list(zip(yvaluesA[::2], yvaluesA[1::2]))
        yvaluesB = [seg.y for seg in livesegments if seg.poly == polyB]
        intervalsB = list(zip(yvaluesB[::2], yvaluesB[1::2]))

        for (startB, endB) in intervalsB: #For each "inner?" interval
            for (startA, endA) in intervalsA: #Check each "outer?" interval
                if startB == endB and (startA == startB or endA == endB): break
                if startA <= startB and endA >= endB:
                    if latestoutcome == Position.DISJOINT: return Position.OVERLAPS, None
                    latestoutcome = Position.CONTAINS
                    break
                elif startB < startA < endB or startB < endA < endB:
                    return Position.OVERLAPS, None
            else:
                if latestoutcome == Position.CONTAINS: return Position.OVERLAPS, None
                latestoutcome = Position.DISJOINT
        return latestoutcome, livesegments

    coordslist1, coordslist2 = _getrotatedcoords([self, other], xdp=dp)

    transposed = False
    polyA, polyB = self, other
    bboxresult = _compareboundingboxes(coordslist1, coordslist2, ydp=dp)
    #print("Bboxresult:", bboxresult)
    if bboxresult in {Position.DISJOINT, Position.TOUCHING}: return Position.DISJOINT
    if bboxresult == Position.EQUAL:
        if _equalpolygons(coordslist1, coordslist2): return Position.EQUAL
        elif _area(coordslist2) > _area(coordslist1):
            coordslist1, coordslist2 = coordslist2, coordslist1
            polyA, polyB = other, self
            transposed = True
    if bboxresult == Position.INSIDE:
        coordslist1, coordslist2 = coordslist2, coordslist1
        polyA, polyB = other, self
        transposed = True

    #print("Transposed", transposed)
    unusedsegments = _getsortedsegments([polyA, polyB], [coordslist1, coordslist2])
    #print("segments", time.time()-tt)
    #print("\nSegments at start:")
    #for seg in unusedsegments:
        #print(seg)
    livesegments = []
    currentoutcome = None
    dp2 = dp-2
    xvalues = sorted(set(x for (x, y) in coordslist1+coordslist2))
    #print("\nxValues", xvalues)
    for x in xvalues: #Vertical sweepline stops at each vertex of either polygon
        #print ("\nx =", x)
        currentoutcome, livesegments = sweeppast(x, currentoutcome, livesegments)
        #print ("currentoutcome", currentoutcome, "\n")
        if currentoutcome == Position.OVERLAPS: return currentoutcome
    #print("sweeping", time.time()-tt)
    if currentoutcome == Position.CONTAINS and transposed: currentoutcome = Position.INSIDE
    return currentoutcome



def findintersections(polylist):
    '''Returns an Enum value: Position.CONTAINS, Position.INSIDE, Position.OVERLAPS, Position.DISJOINT or Position.EQUAL.
    other is another PolygonObject.'''
    def calculatepoint(ix):
        (i1a, i1b), (i2a, i2b) = ix.index1, ix.index2
        p1, p2 = ix.poly1.pointList[i1a], ix.poly2.pointList[i2a]
        v1, v2 = ix.poly1.pointList[i1b] - p1, ix.poly2.pointList[i2b] - p2
        #print("Poly1", p1, v1, "Poly2", p2, v2)
        #print("indexes", ix.index1, ix.index2)
        #print("cross of vectors", v1.cross(v2))
        if v1.cross(v2) == 0: return Point((0,0))
        t = (p2-p1).cross(v2)/v1.cross(v2)
        point = p1+t*v1
        return point

    def sweeppast(x, livesegments):
        for seg in livesegments:
            if seg.rightx == x:
                seg.y = round(seg.righty, dp2)
                seg.xpos = "R"
                seg.currentindex = seg.rightindex
            else:
                seg.y = round(seg.lefty + (x-seg.leftx)*seg.gradient, dp2)
                seg.xpos = "M"
                seg.currentindex = seg.index
        #print("\nXvalue", x)
        #print("\nLive segments (start of sweeppast):")
        #for seg in livesegments: print(seg)

        for i, seg in enumerate(livesegments):
            for seg2 in livesegments[i+1:]:
                #print(f"Comparing:\n{seg}\nwith\n{seg2}")
                #if (seg.y, seg.gradient) > (seg2.y, seg2.gradient) and seg.poly != seg2.poly:
                if seg.y == inf or seg2.y == inf: continue
                if seg.y > seg2.y and seg.poly != seg2.poly:
                    #print("Found intersection")
                    intersections.append(Intersection(seg.poly, seg.index, seg2.poly, seg2.index))

        newsegments = []
        while unusedsegments and unusedsegments[0].leftx == x:
            newseg = unusedsegments.pop(0)
            newseg.y = round(newseg.lefty, dp2)
            newseg.xpos = "L"
            newseg.currentindex = newseg.leftindex
            newsegments.append(newseg)

        livesegments.sort(key=lambda seg: seg.y)
        livesegments = mergelists(livesegments, newsegments)
        #print("\nLive segments (with new added):")
        #for seg in livesegments: print(seg)

        segiter = iter(livesegments)
        seg = next(segiter, None)
        while seg is not None:
            prevseg = seg
            seg = next(segiter, None)
            if seg is None: break
            #print("\nPrevseg:", prevseg, "\nSeg:", seg)
            #if (x, seg.y) in usedpoints: continue
            if seg.y == prevseg.y and seg.poly != prevseg.poly:
                #if seg.xpos in {"L","R"} or prevseg.xpos in {"L","R"} or round(seg.gradient, dp2) != round(prevseg.gradient, dp2):
                if seg.xpos in {"L","R"} or prevseg.xpos in {"L","R"}:
                    #print("found intersection")
                    intersections.append(Intersection(seg.poly, seg.currentindex, prevseg.poly, prevseg.currentindex))
                    #usedpoints.add((x, seg.y))
                    #while seg and seg.y == prevseg.y:
                    #    seg = next(segiter, None)

        livesegments = [seg for seg in livesegments if seg.xpos != "R"]
        return livesegments

    #print("polylist:")
    #for poly in polylist: print(poly, poly.pointList)

    coordslists = _getrotatedcoords(polylist, xdp=dp)

    intersections = []
    usedpoints = set()
    unusedsegments = _getsortedsegments(polylist, coordslists)
    #print("\nSegments at start:")
    #for seg in unusedsegments: print(seg)
    livesegments = []
    dp2 = dp-2
    xvalues = sorted(set(x for coordslist in coordslists for (x, y) in coordslist))
    #print("\nxValues", xvalues)
    for x in xvalues: #Vertical sweepline stops at each vertex of either polygon
        livesegments = sweeppast(x, livesegments)

    ixpoints = {}
    for ix in intersections:
        if isinstance(ix.index1, int):
            ix.point = ix.poly1.pointList[ix.index1]
        elif isinstance(ix.index2, int):
            ix.point = ix.poly2.pointList[ix.index2]
        else:
            ix.point = calculatepoint(ix)
        #print(ix)
        if ix.point in ixpoints:
            #print("combining with", ixpoints[ix.point])
            ixpoints[ix.point].polyrefs.update(ix.polyrefs)
        else:
            ixpoints[ix.point] = ix
        #print("ixpoints so far:", ixpoints)
        if ix.poly1 == polylist[0]:
            ix.selfindex, ix.otherindex = ix.index1, ix.index2
        else:
            ix.selfindex, ix.otherindex = ix.index2, ix.index1

    #print("ixpoints", ixpoints)
    return list(ixpoints.values())

def boundary(polylist):
    tt = time.time()
    ixlist = findintersections(polylist)
    #print("find intersections", time.time()-tt)
    if ixlist == []:
        maxarea = 0
        for poly in polylist:
            polyarea = poly.area()
            if polyarea > maxarea: (maxarea, maxpoly) = (polyarea, poly)
        for poly in polylist:
            if poly is maxpoly: continue
            if maxpoly.positionRelativeTo(poly) != Position.CONTAINS: return None
        return PolygonObject(maxpoly.pointList)

    ixlist.sort(key = lambda ix:ix.point)
    pointlists = []
    for i, poly in enumerate(polylist):
        poly.listindex = i
        pointlists.append(poly.pointList)
    pointlists.append([ix.point for ix in ixlist])

    L = len(polylist)
    reflists = [[(j, i) for i in range(len(pointlists[j]))] for j in range(L)]

    ixdicts = [ListDict() for j in range(L)]
    regions = []
    for i, ix in enumerate(ixlist):
        #print("intersection", i, "at", ix.point, "has polyrefs", ix.polyrefs)
        for (poly, index) in ix.polyrefs:
            #print(poly, "has listindex", poly.listindex)
            j = poly.listindex
            if isinstance(index, tuple):
                #print("Adding point to ixdict for", poly)
                ixdicts[j][index].append((L,i))
            else:
                #print("Replacing point", index, "in poly", poly)
                reflists[j][index] = (L, i)
        polyset = {poly for (poly, index) in ix.polyrefs}
        for region in regions:
            if polyset & region:
                region.update(polyset)
                break
        else:
            regions.append(polyset)

    polyregions = []
    while regions:
        #print("regions", regions)
        mainregion = regions.pop(0)
        for region in regions[:]:
            if region & mainregion:
                mainregion.update(region)
                regions.remove(region)
        polyregions.append(mainregion)
    #print("polyregions", polyregions)

    #print("ixdicts", ixdicts)

    for j in range(L):
        offset = 1
        for index in sorted(ixdicts[j]):
            (i, k) = index
            insert = ixdicts[j][index]
            pl = pointlists[j]
            if pl[k] < pl[i]: insert.reverse()
            #if pointlists[j][k] < pointlists[j][i]: insert.reverse()
            reflists[j][i+offset:i+offset] = insert
            offset += len(insert)

    vertexdict = SetDict()
    for j in range(L):
        last = len(reflists[j]) - 1
        for i in range(last+1): vertexdict[reflists[j][i]].update({reflists[j][i-1], reflists[j][(i+1) if i<last else 0]})
    #print("make vertexdict", time.time()-tt)
    #print("vertexdict")
    #for point in vertexdict:
    #    (j, i) = point
    #    print(point, pointlists[j][i], vertexdict[point])

    minp = Point((inf, inf))
    for (j, i) in vertexdict:
        p = pointlists[j][i]
        if p < minp: minp, minref = p, (j, i)
    currentref = minref
    currentp = start = minp
    newpointlist = [currentp]
    v1 = Point((0,1))
    usedrefs ={(minref, v1)}
    (j, i) = minref
    startpoly = next(iter(ixlist[i].polyrefs))[0] if j == L else polylist[j]
    for region in polyregions:
        if startpoly in region:
            boundaryregion = region
            break
    else:
        boundaryregion = {startpoly}

    #print("currentref, currentp, v1", currentref, currentp, v1)
    while True:
        #print("Polys used so far", usedpolys)
        maxangle = -pi
        for (j, i) in vertexdict[currentref]:
            p = pointlists[j][i]
            v2 = p-currentp
            angle = v2.anglefrom(v1)
            #print("startvec", v1,"point",p, "pvec", v2, "angle", angle*180/pi)
            if angle > maxangle: (maxangle, bestp, bestref) = (angle, p, (j, i))
        if [currentp, bestp] == newpointlist[:2]: break
        currentref = bestref
        newpointlist.append(bestp)
        v1 = bestp - currentp
        currentp = bestp
        #print("New currentref, currentp, v1", currentref, currentp, v1)
        if (currentref, v1) in usedrefs: break
        usedrefs.add((currentref, v1))
        (j, i) = currentref
    #print("New pointlist", newpointlist)
    #print("construct boundary", time.time()-tt)

    if currentp != start: return False
    boundary = PolygonObject(newpointlist[:-1])
    if not (len(polyregions) == 1 and len(boundaryregion) == L):
        for poly in polylist:
            if poly not in boundaryregion:
                #print(f"{poly} not in boundaryregion")
                if boundary.positionRelativeTo(poly) != Position.CONTAINS: return None
    #print("check unused polys", time.time()-tt)

    return boundary

PolygonObject.__bases__ = PolygonObject.__bases__ + (PolygonMixin,)
CanvasObject.__bases__ = CanvasObject.__bases__ + (PolygonCanvasMixin,)
class RegularPolygon(RegularPolygon, PolygonObject):
    pass
