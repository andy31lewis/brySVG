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

class Intersection(object):
    def __init__(self, poly1, index1, poly2, index2, point=None):
        self.poly1 = poly1
        self.index1 = index1
        self.poly2 = poly2
        self.index2 = index2
        if point: self.point = point

class PolygonMixin(object):
    def extraupdate(self):
        L = len(self.pointList)
        self.segments = [Segment(self.pointList[i-1], self.pointList[i], self, ((i-1)%L, i)) for i in range(L)]

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
        def sweeppast(x, latestoutcome, livesegments):
            for seg in livesegments:
                if seg.rightx == x:
                    seg.y = round(seg.righty, dp2)
                else:
                    seg.y = round(seg.lefty + (x-seg.leftx)*seg.gradient, dp2)

            for i, seg in enumerate(livesegments):
                for seg2 in livesegments[i+1:]:
                    if seg.y == inf or seg2.y == inf: continue
                    if seg.y > seg2.y and seg.poly != seg2.poly:
                        return Position.OVERLAPS, None
            livesegments = [seg for seg in livesegments if seg.rightx > x]

            while unusedsegments and unusedsegments[0].leftx == x:
                newseg = unusedsegments.pop(0)
                newseg.y = round(newseg.lefty, dp2)
                livesegments.append(newseg)
            livesegments.sort(key=lambda seg: (seg.y, seg.gradient))

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

        coordslist1, coordslist2 = _getrotatedcoords(self, other, xdp=dp)

        transposed = False
        polyA, polyB = self, other
        bboxresult = _compareboundingboxes(coordslist1, coordslist2, ydp=dp)
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

        unusedsegments = _getsortedsegments(polyA, coordslist1, polyB, coordslist2)
        livesegments = []
        currentoutcome = None
        dp2 = dp-2
        xvalues = sorted(set(x for (x, y) in coordslist1+coordslist2))
        for x in xvalues: #Vertical sweepline stops at each vertex of either polygon
            currentoutcome, livesegments = sweeppast(x, currentoutcome, livesegments)
            if currentoutcome == Position.OVERLAPS: return currentoutcome
        if currentoutcome == Position.CONTAINS and transposed: currentoutcome = Position.INSIDE
        return currentoutcome

    def getIntersections(self, other):
        '''Returns a list of Intersection objects. Each Intersection has 3 attributes:
        .point: a Point whose coordinates are the intersection
        .selfindex: if this is an integer i, the intersection is at a vertex of self, namely self.pointList[i]
                    if this is a tuple (i-1, i), the intersection is between self.pointList[i-1] and self.pointList[i]
        .otherindex: same as selfindex but describes the location of the intersection on the other polygon.
        '''
        def calculatepoint(ix):
            (i1a, i1b), (i2a, i2b) = ix.index1, ix.index2
            p1, p2 = ix.poly1.pointList[i1a], ix.poly2.pointList[i2a]
            v1, v2 = ix.poly1.pointList[i1b] - p1, ix.poly2.pointList[i2b] - p2
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

            for i, seg in enumerate(livesegments):
                for seg2 in livesegments[i+1:]:
                    if seg.y == inf or seg2.y == inf: continue
                    if seg.y > seg2.y and seg.poly != seg2.poly:
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
            segiter = iter(livesegments)
            seg = next(segiter, None)
            while seg is not None:
                prevseg = seg
                seg = next(segiter, None)
                if seg is None: break
                if (x, seg.y) in usedpoints: continue
                if seg.y == prevseg.y and seg.poly != prevseg.poly:
                    if seg.xpos in {"L","R"} or prevseg.xpos in {"L","R"}:
                        intersections.append(Intersection(seg.poly, seg.currentindex, prevseg.poly, prevseg.currentindex))
                        usedpoints.add((x, seg.y))
                        while seg and seg.y == prevseg.y:
                            seg = next(segiter, None)

            livesegments = [seg for seg in livesegments if seg.xpos != "R"]
            return livesegments

        coordslist1, coordslist2 = _getrotatedcoords(self, other, xdp=dp)
        bboxresult = _compareboundingboxes(coordslist1, coordslist2, ydp=dp)
        if bboxresult == Position.DISJOINT: return []
        if bboxresult == Position.EQUAL and _equalpolygons(coordslist1, coordslist2):
            return [Intersection(self, i, other, i, point) for (i, point) in enumerate(self.pointList)]

        intersections = []
        usedpoints = set()
        unusedsegments = _getsortedsegments(self, coordslist1, other, coordslist2)
        livesegments = []
        dp2 = dp-2
        xvalues = sorted(set(x for (x, y) in coordslist1+coordslist2))
        for x in xvalues: #Vertical sweepline stops at each vertex of either polygon
            livesegments = sweeppast(x, livesegments)

        for ix in intersections:
            if isinstance(ix.index1, int):
                ix.point = ix.poly1.pointList[ix.index1]
            elif isinstance(ix.index2, int):
                ix.point = ix.poly2.pointList[ix.index2]
            else:
                ix.point = calculatepoint(ix)

            if ix.poly1 == self:
                ix.selfindex, ix.otherindex = ix.index1, ix.index2
            else:
                ix.selfindex, ix.otherindex = ix.index2, ix.index1

        return intersections

    def merge(self, other, sf=2):

        #print("self pointlist", self.pointList)
        ixlist = self.getIntersections(other)
        if ixlist == []: return None
        ixlist.sort(key = lambda ix:ix.point)
        pointlists = [self.pointList, other.pointList, [ix.point for ix in ixlist]]

        reflists = [[(j, i) for i in range(len(pointlists[j]))] for j in range(2)]
        #min0, min1 = min(self.pointList), min(other.pointList)
        #minref0, minref1 = (0, self.pointList.index(min0)), (1, other.pointList.index(min1))
        #minref = minref1 if min1 < min0 else minref0

        ixdicts = [ListDict(), ListDict()]
        for i, ix in enumerate(ixlist):
            index = [ix.selfindex, ix.otherindex]
            for j in range(2):
                if isinstance(index[j], tuple):
                    ixdicts[j][index[j]].append((2,i))
                else:
                    reflists[j][index[j]] = (2, i)

        for j in range(2):
            offset = 1
            for index in sorted(ixdicts[j]):
                (i, k) = index
                insert = ixdicts[j][index]
                if pointlists[j][k] < pointlists[j][i]: insert.reverse()
                reflists[j][i+offset:i+offset] = insert
                offset += len(insert)

        vertexdict = SetDict()
        for j in range(2):
            last = len(reflists[j]) - 1
            for i in range(last+1): vertexdict[reflists[j][i]].update({reflists[j][i-1], reflists[j][(i+1) if i<last else 0]})
        #print("vertexdict")
        #for point in vertexdict:
            #print(point, vertexdict[point])

        minp = Point((inf, inf))
        for (j, i) in vertexdict:
            p = pointlists[j][i]
            if p < minp: minp, minref = p, (j, i)
        currentref = minref
        currentp = start = minp
        newpointlist = [currentp]
        v1 = Point((0,1))
        usedrefs ={(start, v1)}
        #print("currentref, v1", currentref, v1)
        while True:
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
            if (currentref, v1) in usedrefs: break
            usedrefs.add((currentref, v1))
        #print("New pointlist", newpointlist)
        return PolygonObject(newpointlist[:-1]) if currentp == start else False

class PolygonGroup(GroupObject):
    def __init__(self, objlist=[]):
        self.boundary = None
        self.update()
        super().__init__(objlist)

    def addObject(self, svgobject, objid=None):
        if not isinstance(svgobject, (PolygonObject, PolygonGroup)): return False
        if self.objectList == []:
            self.boundary = PolygonObject(svgobject.pointList)
        else:
            newboundary = self.boundary.merge(svgobject)
            if not newboundary: return newboundary
            self.boundary = newboundary
        super().addObject(svgobject, objid)
        self.update()
        return True

    def deleteAll(self):
        self.boundary = None
        self.update()
        super().deleteAll()

    def update(self):
        self.pointList = [] if self.boundary is None else self.boundary.pointList
        self.segments = [] if self.boundary is None else self.boundary.segments

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
        objsegs = sorted(svgobject.segments, key = lambda seg: seg.angle)
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
            checksegs.extend(obj.segments)
        checksegs.sort(key = lambda seg: seg.angle)
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
                        #print("Moved", objp, objq)
                        #print("Fixed", checkp, checkq)
                        #print("Angle1, Angle2, abs()", angle1, angle2, abs(angle1))
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
                if tonextangle - angled > snapangle:
                    checkstart += 1
                    #print("New checkstart", checkstart)
                if angled > snapangle:
                    #print("Finished checking", angle1)
                    break

        if bestangle is not None:
            #print("Angle, centre, vector", angle*180/pi, centre, vector)
            svgobject.rotateandtranslate(angle*180/pi, centre, vector)
            if not self.vertexSnap: return
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
        #self.doSnap(svgobject)

def _compareboundingboxes(poly1, poly2, xdp=None, ydp=None):
    def getboundingbox(poly):
        xcoords = [round(x, xdp) for (x,y) in poly] if xdp else [x for (x,y) in poly]
        left = min(xcoords)
        right = max(xcoords)
        ycoords = [round(y, ydp) for (x,y) in poly] if ydp else [y for (x,y) in poly]
        top = min(ycoords)
        bottom = max(ycoords)
        return (left, top), (right, bottom)

    if xdp: ydp = xdp
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

def _getrotatedcoords(self, other, xdp):
    def getbestangle(poly1, poly2):
        fromvertical = [abs(seg.angle) for seg in poly1.segments + poly2.segments]
        if 0 not in fromvertical: return 0
        positiveangles = [a for a in fromvertical if a>0.1]
        return min(positiveangles)/2

    a = getbestangle(self, other)
    dp1 = xdp+1
    #print(f"Before rotation:\nPoly1: {self.pointList}\nPoly2: {other.pointList}")
    poly1 = [(round(x, dp1), round(y, dp1)) for (x, y) in self.pointList]
    poly2 = [(round(x, dp1), round(y, dp1)) for (x, y) in other.pointList]
    #print(f"After rounding before rotation:\nPoly1: {poly1}\nPoly2: {poly2}")
    cosa, sina = cos(a), sin(a)
    poly1rotated = self.pointList if a == 0 else [(x*cosa-y*sina, x*sina+y*cosa) for (x, y) in poly1]
    poly2rotated = other.pointList if a == 0 else [(x*cosa-y*sina, x*sina+y*cosa) for (x, y) in poly2]

    coords1 = [(round(x, xdp), y) for (x, y) in poly1rotated]
    coords2 = [(round(x, xdp), y) for (x, y) in poly2rotated]
    #print(f"After rotation:\nPoly1: {coords1}\nPoly2: {coords2}")
    return coords1, coords2

def _getsortedsegments(poly1, coordslist1, poly2, coordslist2):
    L1, L2 = len(coordslist1), len(coordslist2)
    seglist1 = [Segment(coordslist1[i-1], coordslist1[i], poly1, ((i-1)%L1, i)) for i in range(L1)]
    seglist2 = [Segment(coordslist2[i-1], coordslist2[i], poly2, ((i-1)%L2, i)) for i in range(L2)]
    segments = seglist1 + seglist2
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

PolygonObject.__bases__ = PolygonObject.__bases__ + (PolygonMixin,)
CanvasObject.__bases__ = CanvasObject.__bases__ + (PolygonCanvasMixin,)
class RegularPolygon(RegularPolygon, PolygonObject):
    pass
