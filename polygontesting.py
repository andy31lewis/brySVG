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

class Enum(list):
    def __init__(self, name, string):
        values = string.split()
        for i, value in enumerate(values):
            setattr(self, value, i)
            self.append(i)

Position = Enum ('Position', 'CONTAINS INSIDE OVERLAPS EQUAL DISJOINT')

def containspoint(polygonobject, point):
    '''Returns "interior" if point is inside the polygon, "edge" if it is on an edge, or False otherwise'''
    (x, y) = point
    pointlist = polygonobject.pointList
    length = len(pointList)
    counter = 0
    (x1, y1) = pointList[0]
    for i in range(1, length+1):
        (x2, y2) = pointList[i%length]
        if y1 == y2:
            if y == y1 and min(x1,x2)<=x<=max(x1,x2): return "edge"
        elif min(y1,y2)<y<=max(y1,y2) and x<max(x1, x2):
            xcheck = x1 + (y-y1)*(x2-x1)/(y2-y1)
            if x == xcheck: return "edge"
            elif x < xcheck:
                counter += 1
        (x1, y1) = (x2, y2)
    return "interior" if counter%2 == 1 else False

def polygonobjectarea(poly):
    '''Returns the area of the PolygonObject'''
    return polygonarea(poly.pointList)

def polygonarea(poly):
    '''Returns the area of the polygon given as a list of coordinates'''
    area = 0
    (x0, y0) = poly[-1]
    for (x1, y1) in poly:
        area += x1*y0 - x0*y1
        (x0, y0) = (x1, y1)
    return abs(area/2)

def equalpolygonobjects(poly1, poly2):
    '''Returns True if the polygon is identical to other, False otherwise.
    other is another PolygonObject'''
    return equalpolygons(poly1.pointList, poly2.Pointlist)

def equalpolygons(poly1, poly2):
    '''Returns True if poly1 is identical to poly2, False otherwise.
    poly1 and poly2 are lists of vertex coordinates.'''
    start1 = poly1.index(min(poly1))
    poly1 =  poly1[start1+1:]+poly1[:start1]
    start2 = poly2.index(min(poly2))
    poly2 =  poly2[start2+1:]+poly2[:start2]
    return poly1 == poly2 or poly1 == poly2[::-1]

def polygonobjectboundingbox(poly):
    return polygonboundingbox(poly.pointList)

def polygonboundingbox(poly):
    xcoords = [x for (x,y) in poly]
    left = min(xcoords)
    right = max(xcoords)
    ycoords = [y for (x,y) in poly]
    top = min(ycoords)
    bottom = max(ycoords)
    return (left, top), (right, bottom)

def relativeposition(poly1, poly2, dp=1):
    '''Returns an Enum value: Position.CONTAINS, Position.INSIDE, Position.OVERLAPS, Position.DISJOINT or Position.EQUAL.
    other is another PolygonObject.'''
    ABOVE, BELOW, CONTAINS, ABOVEORCONTAINS, BELOWORCONTAINS = 0, 1, 2, 3, 4
    ENDING, ONGOING, STARTING = 0, 1, 2
    START, END = 0, 1

    def makeregion(ID, bounds, status):
        return {"ID":ID, "bounds":bounds, "status":status, "position":{}}

    def compareboundingboxes(poly1, poly2):
        ((left1, top1), (right1, bottom1)) = polygonboundingbox(poly1)
        ((left2, top2), (right2, bottom2)) = polygonboundingbox(poly2)
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
    poly1 = [(round(x,dp1), round(y,dp1)) for (x, y) in poly1.pointList]
    poly2 = [(round(x,dp1), round(y,dp1)) for (x, y) in poly2.pointList]
    transposed = False

    bboxresult = compareboundingboxes(poly1, poly2)
    if bboxresult == Position.DISJOINT: return Position.DISJOINT
    if bboxresult == Position.EQUAL:
        if equalpolygons(poly1, poly2): return Position.EQUAL
        elif polygonarea(poly2) > polygonarea(poly1):
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


