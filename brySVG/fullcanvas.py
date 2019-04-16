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

from brySVG.transformcanvas import *

class NonBezierMixin(object):
    '''Methods for LineObject, PolylineObject, PolygonObject, CircleObject, EllipseObject and RectangleObject'''
    def setPoint(self, i, point):
        self.pointList[i] = point
        self.update()

    def setPoints(self, pointlist):
        self.pointList = pointlist
        self.update()

    def movePoint(self, coords):
       self.setPoint(-1, coords)

class PolyshapeMixin(object):
    '''Methods for PolylineObject and PolygonObject.'''
    def appendPoint(self, point):
        self.pointList.append(point)
        self.update()

    def deletePoints(self, start, end):
        del self.pointList[slice(start, end)]
        self.update()

class BezierMixin(object):
    '''Methods for all types of BezierObject. The parameters point, pointlist, pointset etc should be (lists of) Point object(s).'''
    def setPointset(self, i, pointset):
        self.pointList[i] = pointset[1]
        self.pointsetList[i] = pointset
        self.update()

    def setPointsets(self, pointsetlist):
        self.pointList = [pointset[1] for pointset in pointsetlist]
        self.pointsetList = pointsetlist
        self.update()

    def setPoint(self, i, point):
        self.pointList[i] = point
        self.pointsetList = self.getpointsetlist(self.pointList)
        self.update()

    def setPoints(self, pointlist):
        self.pointList = pointlist
        self.pointsetList = self.getpointsetlist(pointlist)
        self.update()

    def appendPoint(self, point):
        self.pointList.append(point)
        self.pointsetList = self.getpointsetlist(self.pointList)
        self.update()

    def deletePoints(self, start, end):
        del self.pointList[slice(start, end)]
        self.pointsetList = self.getpointsetlist(self.pointList)
        self.update()

    def movePoint(self, point):
        self.pointList[-1] = point
        self.updatepointsetlist()
        if len(self.pointList) == 2:
            self.update()
        elif isinstance(self, ClosedBezierObject):
            ((x1,x2),(x3,x4),(x5,x6)) = self.pointsetList[-2]
            ((x7,x8),(x9,x10),(x11,x12)) = self.pointsetList[-1]
            ((x13,x14),(x15,x16),(x17,x18)) = self.pointsetList[0]
            self.plist = self.plist[:-16]+[x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14,x15,x16]
            self.plist[4:6] = [x17, x18]
            self.attrs["d"] = " ".join(str(x) for x in self.plist)
        else:
            ((x1,x2),(x3,x4),(x5,x6)) = self.pointsetList[-2]
            ((x7,x8),(x9,x10),dummy) = self.pointsetList[-1]
            self.plist = self.plist[:-10]+[x1,x2,x3,x4,x5,x6,x7,x8,x9,x10]
            self.attrs["d"] = " ".join(str(x) for x in self.plist)

class DrawCanvasMixin(object):
    def createObject(self, coords):
        colour = None if self.tool in ["polyline", "bezier", "smoothbezier"] else self.fillColour
        self.mouseOwner = self.shapetypes[self.tool](pointlist=[coords, coords], linecolour=self.penColour, linewidth=self.penWidth, fillcolour=colour)
        self.addObject(self.mouseOwner)
        self.mouseOwner.shapeType = self.tool

    def drawPoint(self, event):
        if self.tool == "select": return
        if self.mouseOwner:
            if isinstance(self.mouseOwner, (PolyshapeMixin, BezierMixin)):
                coords = self.getSVGcoords(event)
                self.mouseOwner.appendPoint(coords)
        else:
            self.startx = self.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
            self.starty = self.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
            coords = self.getSVGcoords(event)
            self.createObject(coords)

    def endDraw(self,event):
        if not self.mouseOwner: return
        if self.mouseDetected and isinstance(self.mouseOwner, (PolyshapeMixin, BezierMixin)):
            self.mouseOwner.deletePoints(-2, None)
        self.mouseOwner = None
        self.mouseMode = MouseMode.EDIT

    def prepareEdit(self, event):
        if self.selectedObject: self.deselectObject()
        svgobject = self.getSelectedObject(event.target.id, getGroup=False)
        if not svgobject or svgobject.fixed: return
        self.selectedObject = svgobject
        if isinstance(svgobject, BezierMixin):
            handles = []
            controlhandles = []
            for i, (point0, point1, point2) in enumerate(svgobject.pointsetList):
                handle = Handle(svgobject, i, point1, self)
                handle.controlHandles = []
                ch0 = None if point0 is None else ControlHandle(svgobject, i, 0, point0, self)
                ch2 = None if point2 is None else ControlHandle(svgobject, i, 2, point2, self)
                if ch0:
                    ch0.linkedHandle = ch2 if isinstance(svgobject, SmoothBezierMixin) else None
                    handle.controlHandles.append(ch0)
                if ch2:
                    ch2.linkedHandle = ch0 if isinstance(svgobject, SmoothBezierMixin) else None
                    handle.controlHandles.append(ch2)
                handles.append(handle)
            self.handles = GroupObject(handles)
            self <= self.handles
            self.controlhandles = GroupObject([ch for handle in handles for ch in handle.controlHandles])
            self <= self.controlhandles
        else:
            self.handles = GroupObject([Handle(svgobject, i, coords, self) for i, coords in enumerate(svgobject.pointList)])
            self <= self.handles

    def movePoint(self, event):
        x = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        dx, dy = x-self.currentx, y-self.currenty
        if "touch" in event.type and abs(dx) < 5 and abs(dy) < 5: return
        self.currentx, self.currenty = x, y
        if self.mouseMode == MouseMode.DRAW:
            coords = self.getSVGcoords(event)
            self.mouseOwner.movePoint(coords)
        else:
            if self.mouseMode == MouseMode.TRANSFORM: dx, dy = x-self.startx, y-self.starty
            dx, dy = dx*self.scaleFactor, dy*self.scaleFactor
            self.mouseOwner.movePoint((dx, dy))

    def endEdit(self, event):
        hittarget = getattr(self.selectedObject, "hitTarget", None)
        if hittarget:
            hittarget.pointList = self.selectedObject.pointList
            if isinstance(self.selectedObject, BezierMixin): hittarget.pointsetList = self.selectedObject.pointsetList
            hittarget.update()
        self.mouseOwner = None

    def deselectObject(self):
        if not self.selectedObject: return
        self.deleteObject(self.handles)
        self.handles = None
        if isinstance(self.selectedObject, BezierMixin):
            self.deleteObject(self.controlhandles)
            self.controlhandles = None
        self.mouseOwner = self.selectedObject = self.selectedhandle = None

class Handle(PointObject):
    def __init__(self, owner, index, coords, canvas):
        pointsize = 7 if canvas.mouseDetected else 15
        opacity = 1 if canvas.mouseDetected else 0.2
        strokewidth = 1 if canvas.mouseDetected else 3
        PointObject.__init__(self, coords, "red", pointsize, canvas)
        self.style.strokeWidth = strokewidth
        self.style.fillOpacity = opacity
        self.owner = owner
        self.index = index
        self.canvas = canvas
        self.bind("mousedown", self.select)
        self.bind("touchstart", self.select)

    def select(self, event):
        event.stopPropagation()
        self.canvas.startx = self.canvas.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        self.canvas.starty = self.canvas.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        self.canvas.mouseOwner = self
        if isinstance(self.owner, BezierMixin):
            if self.canvas.selectedhandle:
                for ch in self.canvas.selectedhandle.controlHandles: ch.style.visibility = "hidden"
            for ch in self.controlHandles: ch.style.visibility = "visible"
        self.canvas.selectedhandle = self

    def movePoint(self, offset):
        self.XY += offset
        if isinstance(self.owner, BezierMixin):
            pointset = [None, self.XY, None]
            for ch in self.controlHandles:
                ch.XY += offset
                pointset[ch.subindex] = ch.XY
            self.owner.setPointset(self.index, pointset)
        else:
            self.owner.setPoint(self.index, self.XY)

class ControlHandle(PointObject):
    def __init__(self, owner, index, subindex, coords, canvas):
        pointsize = 7 if canvas.mouseDetected else 15
        opacity = 1 if canvas.mouseDetected else 0.2
        strokewidth = 1 if canvas.mouseDetected else 3
        PointObject.__init__(self, coords, "green", pointsize, canvas)
        self.style.fillOpacity = opacity
        self.style.strokeWidth = strokewidth
        self.style.visibility = "hidden"
        self.owner = owner
        self.index = index
        self.subindex = subindex
        self.canvas = canvas
        self.bind("mousedown", self.select)
        self.bind("touchstart", self.select)

    def select(self, event):
        event.stopPropagation()
        self.canvas.startx = self.canvas.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        self.canvas.starty = self.canvas.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        self.canvas.mouseOwner = self

    def movePoint(self, offset):
        self.XY += offset
        pointset = list(self.owner.pointsetList[self.index])
        pointset[self.subindex] = self.XY
        if self.linkedHandle:
            point = pointset[1]
            thisoffset = self.XY - point
            otheroffset = self.linkedHandle.XY - point
            newoffset = thisoffset*(otheroffset.length()/thisoffset.length())
            newothercoords = point-newoffset
            pointset[self.linkedHandle.subindex] = newothercoords
            self.linkedHandle.XY = newothercoords
        self.owner.setPointset(self.index, tuple(pointset))

class LineObject(LineObject, NonBezierMixin):
    pass

class PolylineObject(PolylineObject, NonBezierMixin, PolyshapeMixin):
    pass

class PolygonObject(PolygonObject, NonBezierMixin, PolyshapeMixin):
    pass

class RectangleObject(RectangleObject, NonBezierMixin):
    pass

class EllipseObject(EllipseObject, NonBezierMixin):
    pass

class CircleObject(CircleObject, NonBezierMixin):
    pass

class BezierObject(BezierObject, BezierMixin):
    pass

class ClosedBezierObject(ClosedBezierObject, BezierMixin):
    pass

class SmoothBezierObject(SmoothBezierObject, BezierMixin):
    pass

class SmoothClosedBezierObject(SmoothClosedBezierObject, BezierMixin):
    pass

class RegularPolygon(RegularPolygon, NonBezierMixin):
    pass

class CanvasObject(CanvasObject, DrawCanvasMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shapetypes = {"line":LineObject, "polygon":PolygonObject, "polyline":PolylineObject,
        "rectangle":RectangleObject, "ellipse":EllipseObject, "circle":CircleObject,
        "bezier":BezierObject, "closedbezier":ClosedBezierObject, "smoothbezier":SmoothBezierObject, "smoothclosedbezier":SmoothClosedBezierObject}


