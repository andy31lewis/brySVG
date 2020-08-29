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
dp1 = dp-1
dp2 = dp-2

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
        return f"{self.poly}{self.index}: [{self.leftpoint}, {self.rightpoint}]; currenty: {self.y}, xpos: {self.xpos}, gradient: {self.gradient}, angle: {self.angle}"

class Intersection(object):
    def __init__(self, polyrefs, point=None):
        (poly1, index1), (poly2, index2) = polyrefs
        self.polyrefs = {poly1:index1, poly2:index2}
        self.point = point if point is not None else Point((0, 0))

    def __repr__(self):
        s = f"{self.point} \n"
        polys = sorted(self.polyrefs, key = lambda poly: poly.id)
        for poly in polys:
            index = self.polyrefs[poly]
            if isinstance(index, int):
                s += f"at vertex {index} on polygon {poly}\n"
            else:
                i1, i2 = index
                s += f"between vertices {i1} and {i2} on polygon {poly}\n"
        return s

class PolygonMixin(object):
    @property
    def segments(self):
        if isinstance(self, PolygonGroup): return self.boundary.segments
        if getattr(self, "_segments", None) is None:
            #print(f"calculating segments for {self}")
            L = len(self.pointList)
            self._segments = [Segment(self.pointList[i-1], self.pointList[i], self, ((i-1)%L, i)) for i in range(L)]
        return self._segments

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

    def getBoundingBox(self):
        '''Returns bounding box based strictly on coords.
        And can be used before polygon is on the canvas (unlike built-in getBBox).'''
        return _getboundingbox(self.pointList)

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
        ixlist = findintersections([self, other])
        for ix in ixlist:
            polyrefs = ix.polyrefs
            ix.selfindex, ix.otherindex = polyrefs[self], polyrefs[other]
        return ixlist

    def merge(self, other):
        return boundary([self, other])

class PolygonGroup(GroupObject, PolygonMixin):
    def __init__(self, objlist=[]):
        self.boundary = None
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

    def addObjects(self, polylist, listboundary=None):
        if polylist == []: return None
        blist = [self.boundary] if self.boundary else []
        if listboundary:
            blist.append(listboundary)
        else:
            blist.extend(polylist)
        newboundary = listboundary if len(blist) == 1 else boundary(blist)
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

    @property
    def pointList(self):
        return [] if self.boundary is None else self.boundary.pointList

    @pointList.setter
    def pointList(self, pointlist):
        pass

    @property
    def points(self):
        return None if self.boundary is None else self.boundary.points

    def matrixTransform(self, matrix):
        def addalltopointslist(group):
            for obj in group.objectList:
                if isinstance(obj, PolygonGroup):
                    addalltopointslist(obj)
                else:
                    pointslist.append(obj.points)
                    obj._pointList = None
                    obj._segments = None
            pointslist.append(group.boundary.points)
            group.boundary._pointList = None
            group.boundary._segments = None

        pointslist = []
        addalltopointslist(self)
        #window.transformpoints(pointslist, matrix)
        self.transformpoints(pointslist, matrix)

    def transformpoints(self, pointslist, matrix):
        for points in pointslist:
            L = points.numberOfItems
            for i in range(L):
                pt = points.getItem(i)
                newpt =  pt.matrixTransform(matrix)
                points.replaceItem(newpt, i)

    def cloneObject(self):
        newobject = super().cloneObject()
        newobject.boundary = self.boundary.cloneObject()
        newobject.update()
        return newobject

class PolygonCanvasMixin(object):
    def doEdgeSnap(self, svgobject):
        tt = time.time()
        if not isinstance(svgobject, (PolygonObject, PolygonGroup)): return
        snapangle = self.snapAngle*pi/180
        snapd = self.snapDistance
        bestangle = None
        bbox = svgobject.getBBox()
        L1, R1, T1, B1 = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height

        checksegs = []
        checkobjs = []
        for objid in self.objectDict:
            if objid == svgobject.id: continue
            obj = self.objectDict[objid]
            if getattr(obj, "group", None): continue
            if not isinstance(obj, (PolygonObject, PolygonGroup)): continue
            bbox = obj.getBBox()
            L2, R2, T2, B2 = bbox.x, bbox.x+bbox.width, bbox.y, bbox.y+bbox.height
            if L2-R1 > snapd or R2-L1 < -snapd or T2-B1 > snapd or B2-T1 < -snapd: continue
            checksegs.extend(obj.segments)
            checkobjs.append(obj)
        if not checksegs:
            print("ES-disjoint", time.time()-tt)
            return
        checksegs.sort(key = lambda seg: seg.angle) #all segments which could possibly be snapped to, sorted by angle from vertical
        for seg in checksegs: #if any segments have an angle within snapangle of -pi/2, create a copy with equaivalent angle close to +pi/2
            if seg.angle > snapangle - pi/2: break
            newseg = Segment(seg.leftpoint, seg.rightpoint, seg.poly, seg.index)
            newseg.angle = seg.angle + pi
            checksegs.append(newseg)

        objsegs = sorted(svgobject.segments, key = lambda seg: seg.angle)
        for seg in objsegs: #do the same for the object being snapped
            if seg.angle > snapangle - pi/2: break
            newseg = Segment(seg.leftpoint, seg.rightpoint, seg.poly, seg.index)
            newseg.angle = seg.angle + pi
            objsegs.append(newseg)

        #print("ES-createsegments", time.time()-tt)
        #print("objsegs")
        #for seg in objsegs: print(seg)
        #print("checksegs")
        #for seg in checksegs: print(seg)
        checkstart = 0
        piby4 = pi/4
        found = False
        for i, seg1 in enumerate(objsegs): #sweep stops at the angle of each segment of object to be snapped
            angle1 = seg1.angle
            #print("\nChecking:", angle1)
            checksegs = checksegs[checkstart:] #remove segments with angle << angle of object segments
            if not checksegs: break
            #print("check angles", [seg.angle for seg  in checksegs])
            try:
                tonextangle = objsegs[i+1].angle - angle1 #find amount between current and next angle in the sweep
            except IndexError:
                tonextangle = 0
            #print("tonextangle", tonextangle)
            checkstart = 0
            for seg2 in checksegs: #start checking segments within snapangle of the current object segment
                angle2 = seg2.angle
                #print("Against:", angle2)
                angled = angle2 - angle1
                #print("Current best angle", bestangle)
                #print("angled", angled)
                absangle = abs(angled)
                if (bestangle is None and absangle < snapangle) or (bestangle is not None and absangle < bestangle):
                    #print("Angles close enough")
                    (objleft, objright) = (seg1.leftx, seg1.rightx) #First check bounding boxes - if disjoint, ignore segment
                    (objtop, objbottom) = (seg1.top, seg1.bottom)
                    (checkleft, checkright) = (seg2.leftx-snapd, seg2.rightx+snapd)
                    (checktop, checkbottom) = (seg2.top-snapd, seg2.bottom+snapd)
                    if not (objleft > checkright or objright < checkleft or objtop > checkbottom or objbottom < checktop):
                        objp, objq = seg1.leftpoint, seg1.rightpoint #Next check whether segments intersect ...
                        checkp, checkq = seg2.leftpoint, seg2.rightpoint
                        #print("Not disjoint segments")
                        #print("obj:", seg1)
                        #print("check:", seg2)
                        objv, checkv = objq-objp, checkq-checkp
                        diff, product = checkp - objp, objv.cross(checkv)
                        (t, u) = (diff.cross(objv)/product, diff.cross(checkv)/product) if product != 0 else (inf, inf)
                        #print("t and u", t, u)
                        if 0<=t<=1 and 0<=u<=1: #... if so, distance between them is 0
                            (bestangle, angle, centre, vector, objseg, checkseg) = (absangle, angled, objp + u*objv, (0, 0), seg1, seg2)
                        else: #... if not, check how close each endpoint of segment is to the other segment,
                            bestd = None #vertically or horizontally depending on the angle of the segment
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
                    checkstart += 1 #angle just checked will be too small when sweep moves on
                    #print("New checkstart", checkstart)
                if angled > snapangle:
                    #print("Finished checking", angle1)
                    break #angle just checked is too great - time to move sweep on
                if bestangle == 0:
                    found = True #Angle of 0 can't be beaten, so abort search at this sweep point...
                    break
            if found: break #... and abort sweep completely
        #print("ES-findbestsnap", time.time()-tt)

        if bestangle is not None: #First snap the edges together
            #print("Angle, centre, vector", angle*180/pi, centre, vector)
            if not (angle ==0 and vector == (0, 0)): svgobject.rotateandtranslate(angle*180/pi, centre, vector)
        if self.vertexSnap: #Even if we can't snap the edges, can still try to snap the vertices
            self.doVertexSnap(svgobject, [p for obj in checkobjs for p in obj.pointList])
        print("ES-dosnap", time.time()-tt)

def _getboundingbox(poly, xdp=None, ydp=None):
    xcoords = [round(x, xdp) for (x,y) in poly] if xdp else [x for (x,y) in poly]
    left = min(xcoords)
    right = max(xcoords)
    ycoords = [round(y, ydp) for (x,y) in poly] if ydp else [y for (x,y) in poly]
    top = min(ycoords)
    bottom = max(ycoords)
    return (left, top), (right, bottom)

def _compareboundingboxes(poly1, poly2, xdp=None, ydp=None):
    if xdp and not ydp: ydp = xdp
    ((left1, top1), (right1, bottom1)) = _getboundingbox(poly1, xdp, ydp)
    ((left2, top2), (right2, bottom2)) = _getboundingbox(poly2, xdp, ydp)
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
            segs = poly.segments
            anglesfromvertical.extend([abs(seg.angle) for seg in segs])
        #print("angles", [a*180/pi for a in anglesfromvertical])
        if 0 not in anglesfromvertical: return 0
        positiveangles = [a for a in anglesfromvertical if a>0.1]
        return round(min(positiveangles)/2, 1)

    a = getbestangle(polylist)
    cosa, sina = cos(a), sin(a)
    #print("Best angle", a*180/pi)
    coordslists = []
    for poly in polylist:
        #print(f"Before rounding:{poly.pointList}")
        if a == 0:
            polyrotated = poly.pointList
        else:
            polyrotated = []
            t = svgbase.createSVGTransform()
            t.setRotate(a*180/pi, 5500, 5500)
            M = t.matrix
            P = poly.points
            L = P.numberOfItems
            for i in range(L):
                pt = P.getItem(i)
                newpt =  pt.matrixTransform(M)
                polyrotated.append((newpt.x, newpt.y))

        coords = [(round(x, xdp), y) for (x, y) in polyrotated]
        coordslists.append(coords)
        #print(f"After rotation and rounding:\n{coords}")
    return coordslists

def _getsortedsegments(polylist, coordslists):
    segments = []
    for poly, coordslist in zip(polylist, coordslists):
        L = len(coordslist)
        segments.extend([Segment(coordslist[i-1], coordslist[i], poly, ((i-1)%L, i)) for i in range(L)])
    segments.sort(key = lambda seg: (seg.leftx, round(seg.lefty, dp1), seg.gradient))
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

    polyA, polyB = getattr(self, "boundary", self), getattr(other, "boundary", other)
    coordslist1, coordslist2 = _getrotatedcoords([polyA, polyB], xdp=dp)

    transposed = False
    bboxresult = _compareboundingboxes(coordslist1, coordslist2, ydp=dp)
    #print("Bboxresult:", bboxresult)
    if bboxresult in {Position.DISJOINT, Position.TOUCHING}: return Position.DISJOINT
    if bboxresult == Position.EQUAL:
        if _equalpolygons(coordslist1, coordslist2): return Position.EQUAL
        elif _area(coordslist2) > _area(coordslist1):
            coordslist1, coordslist2 = coordslist2, coordslist1
            polyA, polyB = polyB, polyA
            transposed = True
    if bboxresult == Position.INSIDE:
        coordslist1, coordslist2 = coordslist2, coordslist1
        polyA, polyB = polyB, polyA
        transposed = True

    #print("Transposed", transposed)
    unusedsegments = _getsortedsegments([polyA, polyB], [coordslist1, coordslist2])
    #print("segments", time.time()-tt)
    #print("\nSegments at start:")
    #for seg in unusedsegments: print(seg)
    livesegments = []
    currentoutcome = None
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
    def calculatepoint(polyrefs):
        (poly1, index1), (poly2, index2) = polyrefs
        (i1a, i1b), (i2a, i2b) = index1, index2
        p1, p2 = poly1.pointList[i1a], poly2.pointList[i2a]
        v1, v2 = poly1.pointList[i1b] - p1, poly2.pointList[i2b] - p2
        #print("Poly1", p1, v1, "Poly2", p2, v2)
        #print("indexes", ix.index1, ix.index2)
        #print("cross of vectors", v1.cross(v2))
        if v1.cross(v2) == 0: return Point((0,0))
        t = (p2-p1).cross(v2)/v1.cross(v2)
        point = p1+t*v1
        return point

    def addtoixdict(point, polyrefs):
        ixkey = round(point, dp2)
        if ixkey in ixpoints:
            #print("combining with", ixpoints[ixkey])
            existingrefs = ixpoints[ixkey].polyrefs
            for poly, index in polyrefs:
                if (poly not in existingrefs) or isinstance(index, int):
                    existingrefs[poly] = index
                else:
                    oldindex = existingrefs[poly]
                    if isinstance(oldindex, tuple) and index != oldindex:
                        (a,b), (c,d) = index, oldindex
                        existingrefs[poly] = b if b==c else a
        else:
            #print("creating new")
            ixpoints[ixkey] = Intersection(polyrefs, point)
            #print(ixpoints[ixkey])

    def sweeppast(x, livesegments): #move to next value of x
        for seg in livesegments: #For all live segments, work out the current y coord
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

        for i, seg in enumerate(livesegments): #for each live segment,
            for seg2 in livesegments[i+1:]: #look at all segments whose y-coord was previously >= this segment's y-coord
                #print(f"Comparing:\n{seg}\nwith\n{seg2}")
                if seg.y == inf or seg2.y == inf: continue
                if seg.y > seg2.y and seg.poly != seg2.poly: #if this segment's y-coord  is now greater, they must have crossed
                    #print("Found intersection")
                    polyrefs = [(seg.poly, seg.index), (seg2.poly, seg2.index)]
                    point = calculatepoint(polyrefs)
                    addtoixdict(point, polyrefs)

        newsegments = []
        while unusedsegments and unusedsegments[0].leftx == x: #get any segments which start at this value of x
            newseg = unusedsegments.pop(0)
            newseg.y = round(newseg.lefty, dp2)
            newseg.xpos = "L"
            newseg.currentindex = newseg.leftindex
            newsegments.append(newseg)

        livesegments.sort(key=lambda seg: seg.y) #sort live segments based on y-coord (but not gradient; may be about to cross)
        livesegments = mergelists(livesegments, newsegments) #merge the new segments based on y-coord and gradient
        #print("\nLive segments (with new added):")
        #for seg in livesegments: print(seg)

        segiter = iter(livesegments)
        seg = next(segiter, None)
        while seg is not None: #look for segments whose current y-coord is the same
            prevseg = seg
            seg = next(segiter, None)
            if seg is None: break
            #print("\nPrevseg:", prevseg, "\nSeg:", seg)
            if seg.y == prevseg.y and seg.poly != prevseg.poly:
                if seg.xpos in {"L","R"} or prevseg.xpos in {"L","R"}: #but if the current position is in the middle of both segments, they could just be collinear
                    #print("found intersection")
                    point = seg.poly.pointList[seg.currentindex] if seg.xpos in {"L","R"} else prevseg.poly.pointList[prevseg.currentindex]
                    addtoixdict(point, [(seg.poly, seg.currentindex), (prevseg.poly, prevseg.currentindex)])

        livesegments = [seg for seg in livesegments if seg.xpos != "R"] #remove segments which are finished with
        return livesegments

    #print("polylist:")
    #for poly in polylist: print(poly, poly.pointList)
    tt = time.time()
    polylist = [getattr(poly, "boundary", poly) for poly in polylist]
    coordslists = _getrotatedcoords(polylist, xdp=dp)
    #print("FI-getrotatedcoords", time.time()-tt)

    unusedsegments = _getsortedsegments(polylist, coordslists)
    #print("FI-getsortedsegments", time.time()-tt)

    #print("\nSegments at start:")
    #for seg in unusedsegments: print(seg)
    ixpoints = {}
    livesegments = []
    xvalues = sorted(set(x for coordslist in coordslists for (x, y) in coordslist))
    #print("\nxValues", xvalues)
    for x in xvalues: #Vertical sweepline stops at each vertex of either polygon
        livesegments = sweeppast(x, livesegments)
    #print("FI-sweeppast", time.time()-tt)

    return list(ixpoints.values())

def boundary(polylist):
    tt = time.time()
    polylist = [getattr(poly, "boundary", poly) for poly in polylist]
    ixlist = findintersections(polylist)
    #print("B-findintersections", time.time()-tt)
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
        for (poly, index) in ix.polyrefs.items():
            #print(poly, "has listindex", poly.listindex)
            j = poly.listindex
            if isinstance(index, tuple):
                #print("Adding point to ixdict for", poly)
                ixdicts[j][index].append((L,i))
            else:
                #print("Replacing point", index, "in poly", poly)
                reflists[j][index] = (L, i)
        polyset = set(ix.polyrefs)
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
            reflists[j][i+offset:i+offset] = insert
            offset += len(insert)

    vertexdict = SetDict()
    for j in range(L):
        last = len(reflists[j]) - 1
        for i in range(last+1): vertexdict[reflists[j][i]].update({reflists[j][i-1], reflists[j][(i+1) if i<last else 0]})
    #print("B-makevertexdict", time.time()-tt)
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
    startpoly = next(iter(ixlist[i].polyrefs)) if j == L else polylist[j]
    for region in polyregions:
        if startpoly in region:
            boundaryregion = region
            break
    else:
        boundaryregion = {startpoly}

    #print("currentref, currentp, v1", currentref, currentp, v1)
    while True:
        maxangle = -pi
        for (j, i) in vertexdict[currentref]:
            p = pointlists[j][i]
            v2 = p-currentp
            angle = v2.anglefrom(v1)
            #print("ref", (j, i),"point",p, "pvec", v2, "angle", angle*180/pi)
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
    #print("B-constructboundary", time.time()-tt)

    if currentp != start: return False
    boundary = PolygonObject(newpointlist[:-1])
    if not (len(polyregions) == 1 and len(boundaryregion) == L):
        for poly in polylist:
            if poly not in boundaryregion:
                #print(f"{poly} not in boundaryregion")
                if boundary.positionRelativeTo(poly) != Position.CONTAINS: return None
    #print("B-checkunusedpolys", time.time()-tt)

    return boundary

PolygonObject.__bases__ = PolygonObject.__bases__ + (PolygonMixin,)
CanvasObject.__bases__ = CanvasObject.__bases__ + (PolygonCanvasMixin,)
class RegularPolygon(RegularPolygon, PolygonObject):
    pass
