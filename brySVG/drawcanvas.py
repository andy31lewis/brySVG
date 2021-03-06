#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014-2021 Andy Lewis                                          #
# --------------------------------------------------------------------------- #
# For details, see the LICENSE file in this repository                        #

from brySVG.dragcanvas import *

class NonBezierMixin(object):
    '''Methods for LineObject, PolylineObject, PolygonObject, CircleObject, EllipseObject and RectangleObject'''
    def setPoint(self, i, point):
        self.pointList[i] = point
        self._update()
        self._updatehittarget()
    """
    def setPoints(self, pointlist):
        self.pointList = pointlist
        self._update()
        self._updatehittarget()
    """
    def _movePoint(self, coords):
       self.setPoint(-1, coords)

class PolyshapeMixin(object):
    '''Methods for PolylineObject and PolygonObject.'''
    def _appendPoint(self, point):
        self.pointList.append(point)
        self._update()

    def insertPoint(self, index, point):
        self.pointList.insert(index, point)
        self._update()
        self._updatehittarget()

    def deletePoint(self, index):
        self.deletePoints(index, index+1)

    def deletePoints(self, start, end):
        del self.pointList[slice(start, end)]
        self._update()
        self._updatehittarget()

class BezierMixin(object):
    '''Methods for all types of BezierObject. The parameters point, pointlist, pointset etc should be (lists of) Point object(s).'''
    def setPointset(self, i, pointset):
        self.pointList[i] = pointset[1]
        self.pointsetList[i] = pointset
        self._update()
        self._updatehittarget()

    def setPointsetList(self, pointsetlist):
        self.pointList = [pointset[1] for pointset in pointsetlist]
        self.pointsetList = pointsetlist
        self._update()
        self._updatehittarget()

    def setPoint(self, i, point):
        self.pointList[i] = point
        self.pointsetList = self._getpointsetlist(self.pointList)
        self._update()
        self._updatehittarget()
    """
    def setPoints(self, pointlist):
        self.pointList = pointlist
        self.pointsetList = self._getpointsetlist(pointlist)
        self._update()
        self._updatehittarget()
    """
    def _appendPoint(self, point):
        self.pointList.append(point)
        self.pointsetList = self._getpointsetlist(self.pointList)
        self._update()

    def deletePoints(self, start, end):
        del self.pointList[slice(start, end)]
        self.pointsetList = self._getpointsetlist(self.pointList)
        self._update()
        self._updatehittarget()

    def insertPoint(self, index, point):
        self.pointList.insert(index, point)
        if isinstance(self, SmoothBezierMixin):
            self.pointsetList = self._getpointsetlist(self.pointList)
        else:
            L = len(self.pointList)
            triple = [self.pointList[index-1], point, self.pointList[(index+1)%L]]
            cpoint1, cpoint2 = SmoothBezierMixin._calculatecontrolpoints(self, triple)
            #cpoint1, cpoint2 = (self.pointList[index-1]+point)/2, (self.pointList[(index+1)%L]+point)/2
            self.pointsetList.insert(index, [cpoint1, point, cpoint2])
            self.pointsetList[index-1][2] = cpoint1
            self.pointsetList[(index+1)%L][0] = cpoint2
        self._update()
        self._updatehittarget()

    def deletePoint(self, index):
        point = self.pointList[index]
        del self.pointList[index]
        if isinstance(self, SmoothBezierMixin):
            self.pointsetList = self._getpointsetlist(self.pointList)
        else:
            L = len(self.pointsetList)
            #triple = [self.pointList[index-1], point, self.pointList[(index+1)%L]]
            #cpoint1, cpoint2 = SmoothBezierMixin.calculatecontrolpoints(self, triple)
            #cpoint1, cpoint2 = (self.pointList[index-1]+point)/2, (self.pointList[(index+1)%L]+point)/2
            #self.pointsetList.insert(index, [cpoint1, point, cpoint2])
            if index == 0 and self.pointsetList[index][0] is None:
                self.pointsetList[index+1][0] = None
            elif index == L-1 and self.pointsetList[index][2] is None:
                self.pointsetList[index-1][2] = None
            else:
                self.pointsetList[(index-1)%L][2] = point
                self.pointsetList[(index+1)%L][0] = point
            del self.pointsetList[index]
        self._update()
        self._updatehittarget()

    def _movePoint(self, point):
        self.pointList[-1] = point
        self._updatepointsetlist()
        if len(self.pointList) == 2:
            self._update()
        elif isinstance(self, (ClosedBezierObject, SmoothClosedBezierObject)):
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
    def setTool(self, tool):
        if self.mouseMode == MouseMode.DRAW: self._endDraw()
        self.tool = tool
        self.mouseMode = MouseMode.EDIT if tool in {"select", "insertpoint", "deletepoint"} else MouseMode.DRAW

    def _createObject(self, coords):
        colour = "none" if self.tool in ["polyline", "bezier", "smoothbezier"] else self.fillColour
        self.mouseOwner = shapetypes[self.tool](pointlist=[coords, coords], linecolour=self.penColour, linewidth=self.penWidth, fillcolour=colour)
        self.addObject(self.mouseOwner)
        self.mouseOwner.shapeType = self.tool

    def _drawPoint(self, event):
        if self.tool == "select": return
        if self.mouseOwner:
            if isinstance(self.mouseOwner, (PolyshapeMixin, BezierMixin)):
                coords = self.getSVGcoords(event)
                self.mouseOwner._appendPoint(coords)
        else:
            self.startx = self.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
            self.starty = self.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
            coords = self.getSVGcoords(event)
            self._createObject(coords)

    def _endDraw(self, event=None):
        if not self.mouseOwner: return
        svgobj = self.mouseOwner
        if isinstance(svgobj, (PolyshapeMixin, BezierMixin)):
            evtype = getattr(event, "type", None)
            if evtype == "dblclick":
                svgobj.deletePoints(-2, None)
                #print("Deleted last 2 points")
            elif self.mouseDetected:
                svgobj.deletePoints(-1, None)
                #print("Deleted last point")
            elif svgobj.pointList[0] == svgobj.pointList[1]:
                svgobj.deletePoints(None, 1)
                #print("deleted first point")
            while len(svgobj.pointList) > 1 and svgobj.pointList[-1] == svgobj.pointList[-2]:
                svgobj.deletePoints(-1, None)
            if len(svgobj.pointList) == 1: self.deleteObject(svgobj)
            if isinstance(svgobj, SectorObject): svgobj.pointList = svgobj.pointList[:2] + svgobj.pointList[-1:]
        elif isinstance(svgobj, NonBezierMixin):
            if svgobj.pointList[0] == svgobj.pointList[1]: self.deleteObject(svgobj)
        self.mouseOwner = None
        self.mouseMode = MouseMode.EDIT
        return svgobj

    def _createEditHitTargets(self):
        objlist = list(self.objectDict.values())
        for obj in objlist:
            if isinstance(obj, GroupObject): continue
            if hasattr(obj, "hitTarget"): continue
            if hasattr(obj, "reference"): continue # A hitTarget doesn't need its own hitTarget
            if isinstance(obj, UseObject):
                newobj = RectangleObject(obj.pointList, obj.angle)
            elif obj.fixed:
                continue
            elif isinstance(obj, (PolyshapeMixin, BezierMixin)):
                newobj = HitTarget(obj, self)
            else:
                if obj.style.fill != "none": continue
                newobj = obj.cloneObject()
                newobj.style.strokeWidth = 10*self.scaleFactor if self.mouseDetected else 25*self.scaleFactor
            newobj.reference = obj
            newobj.style.opacity = 0
            if not isinstance(newobj, HitTarget):
                for event in MOUSEEVENTS: newobj.bind(event, self._onHitTargetMouseEvent)
                for event in TOUCHEVENTS: newobj.bind(event, self._onHitTargetTouchEvent)
            obj.hitTarget = newobj
            self.hittargets.append(newobj)
            self.addObject(newobj)

    def _prepareEdit(self, event):
        if self.selectedObject: self.deselectObject()
        svgobject = self.getSelectedObject(event.target.id, getGroup=False)
        if not svgobject or svgobject.fixed: return
        self.selectedObject = svgobject
        self.createHandles(svgobject)
        if self.tool == "insertpoint":
            index, point = self._insertPoint(event)

    def createHandles(self, svgobject):
        if isinstance(svgobject, UseObject): return
        if isinstance(svgobject, BezierMixin):
            handles = []
            for i, (point0, point1, point2) in enumerate(svgobject.pointsetList):
                handle = Handle(svgobject, i, point1, "red", self)
                handle.controlHandles = []
                ch0 = None if point0 is None else ControlHandle(svgobject, i, 0, point0, "green", self)
                ch2 = None if point2 is None else ControlHandle(svgobject, i, 2, point2, "green", self)
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
            self.handles = GroupObject([Handle(svgobject, i, coords, "red", self) for i, coords in enumerate(svgobject.pointList)])
            self <= self.handles

    def _movePoint(self, event):
        x = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        dx, dy = x-self.currentx, y-self.currenty
        if "touch" in event.type and abs(dx) < 5 and abs(dy) < 5: return
        self.currentx, self.currenty = x, y
        if self.mouseMode == MouseMode.DRAW:
            coords = self.getSVGcoords(event)
            self.mouseOwner._movePoint(coords)
        else:
            if self.mouseMode == MouseMode.TRANSFORM: dx, dy = x-self.startx, y-self.starty
            dx, dy = dx*self.scaleFactor, dy*self.scaleFactor
            self.mouseOwner._movePoint((dx, dy))

    def _insertPoint(self, event):
        if not self.selectedObject: return None, None
        try:
            index = self.objectDict[event.target.id].segmentindex
        except (KeyError, AttributeError):
            return None, None
        self.deleteObject(self.handles)
        self.deleteObject(self.controlhandles)
        clickpoint = self.getSVGcoords(event)
        svgobject = self.selectedObject
        svgobject.insertPoint(index, clickpoint)
        self.createHandles(svgobject)
        return index, clickpoint

    def _deletePoint(self, index):
        if not self.selectedObject: return None
        if not isinstance(self.selectedObject, (PolyshapeMixin, BezierObject)): return None
        svgobject = self.selectedObject
        if len(svgobject.pointList) <= 2:
            self.deleteSelection()
            return None
        self.deleteObject(self.handles)
        self.deleteObject(self.controlhandles)
        svgobject.deletePoint(index)
        self.createHandles(svgobject)
        return index

    def _endEdit(self, event):
        if self.selectedObject:
            self.selectedObject._updatehittarget()
            if self.handles: self <= self.handles
            if self.controlhandles: self <= self.controlhandles
        self.mouseOwner = None

    def deselectObject(self):
        if not self.selectedObject: return
        self.deleteHandles()
        self.mouseOwner = self.selectedObject = self.selectedhandle = None

    def deleteHandles(self):
        self.deleteObject(self.handles)
        self.handles = None
        if isinstance(self.selectedObject, BezierMixin):
            self.deleteObject(self.controlhandles)
            self.controlhandles = None

class HitTargetSegment(LineObject):
    def __init__(self, pointlist, width, reference, index):
        LineObject.__init__(self, pointlist, linewidth=width)
        self.reference = reference
        self.segmentindex = index
        self.style.opacity = 0

class BezierHitTargetSegment(BezierObject):
    def __init__(self, pointsetlist, width, reference, index):
        BezierObject.__init__(self, pointsetlist, linewidth=width)
        self.reference = reference
        self.segmentindex = index
        self.style.opacity = 0

class HitTarget(GroupObject):
    def __init__(self, reference, canvas):
        GroupObject.__init__(self)
        self.reference = reference
        self.style.cursor = reference.style.cursor
        self.canvas = canvas
        self._update()

    def _update(self):
        self.deleteAll()
        width = 10*self.canvas.scaleFactor if self.canvas.mouseDetected else 25*self.canvas.scaleFactor
        if isinstance(self.reference, PolyshapeMixin):
            pointlist = self.reference.pointList[:]
            if isinstance(self.reference, PolygonObject): pointlist.append(pointlist[0])
            for i in range(len(pointlist)-1):
                segment = HitTargetSegment(pointlist[i:i+2], width, self.reference, i+1)
                self.addObject(segment)
        else:
            pointsetlist = self.reference.pointsetList[:]
            if isinstance(self.reference, (ClosedBezierObject, SmoothClosedBezierObject)): pointsetlist.append(pointsetlist[0])
            for i in range(len(pointsetlist)-1):
                ps0 = [None] + pointsetlist[i][1:]
                ps1 = pointsetlist[i+1][:-1] + [None]
                segment = BezierHitTargetSegment([ps0, ps1], width, self.reference, i+1)
                self.addObject(segment)
        self.canvas.deleteObject(self)
        self.canvas.addObject(self)

class Handle(PointObject):
    def __init__(self, owner, index, coords, colour, canvas):
        pointsize = 7 if canvas.mouseDetected else 15
        opacity = 0.4
        strokewidth = 3
        PointObject.__init__(self, coords, colour, pointsize, canvas)
        self.style.strokeWidth = strokewidth
        self.style.fillOpacity = opacity
        self.owner = owner
        self.pointIndex = index
        self.canvas = canvas
        self.bind("mousedown", self._select)
        self.bind("touchstart", self._select)

    def _select(self, event):
        if event.type == "mousedown" and event.button > 0: return
        event.preventDefault()
        event.stopPropagation()
        if self.canvas.tool == "deletepoint":
            self.canvas._deletePoint(self.pointIndex)
            return
        self.canvas.startx = self.canvas.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        self.canvas.starty = self.canvas.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        self.canvas.mouseOwner = self
        if isinstance(self.owner, BezierMixin):
            if self.canvas.selectedhandle:
                for ch in self.canvas.selectedhandle.controlHandles: ch.style.visibility = "hidden"
            for ch in self.controlHandles: ch.style.visibility = "visible"
        self.canvas.selectedhandle = self

    def _movePoint(self, offset):
        self.XY += offset
        if isinstance(self.owner, BezierMixin):
            pointset = [None, self.XY, None]
            for ch in self.controlHandles:
                ch.XY += offset
                pointset[ch.subindex] = ch.XY
            self.owner.setPointset(self.pointIndex, pointset)
        else:
            self.owner.setPoint(self.pointIndex, self.XY)

class ControlHandle(PointObject):
    def __init__(self, owner, index, subindex, coords, colour, canvas):
        pointsize = 7 if canvas.mouseDetected else 15
        opacity = 0.4
        strokewidth = 3
        PointObject.__init__(self, coords, colour, pointsize, canvas)
        self.style.fillOpacity = opacity
        self.style.strokeWidth = strokewidth
        self.style.visibility = "hidden"
        self.owner = owner
        self.pointIndex = index
        self.subindex = subindex
        self.canvas = canvas
        self.bind("mousedown", self._select)
        self.bind("touchstart", self._select)

    def _select(self, event):
        event.stopPropagation()
        self.canvas.startx = self.canvas.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        self.canvas.starty = self.canvas.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        self.canvas.mouseOwner = self

    def _movePoint(self, offset):
        self.XY += offset
        pointset = self.owner.pointsetList[self.pointIndex]
        pointset[self.subindex] = self.XY
        if self.linkedHandle:
            point = pointset[1]
            thisoffset = self.XY - point
            otheroffset = self.linkedHandle.XY - point
            newoffset = thisoffset*(otheroffset.length()/thisoffset.length())
            newothercoords = point-newoffset
            pointset[self.linkedHandle.subindex] = newothercoords
            self.linkedHandle.XY = newothercoords
        self.owner.setPointset(self.pointIndex, pointset)

nonbezier = [LineObject, RectangleObject, EllipseObject, CircleObject, SectorObject, PolylineObject, PolygonObject, ImageObject]
for cls in nonbezier:
    cls.__bases__ = cls.__bases__ + (NonBezierMixin,)
    #print(cls, cls.__bases__)
polyshape = [PolylineObject, PolygonObject, SectorObject]
for cls in polyshape:
    cls.__bases__ = cls.__bases__ + (PolyshapeMixin,)
    #print(cls, cls.__bases__)
bezier = [BezierObject, ClosedBezierObject, SmoothBezierObject, SmoothClosedBezierObject]
for cls in bezier:
    cls.__bases__ = cls.__bases__ + (BezierMixin,)
    #print(cls, cls.__bases__)
CanvasObject.__bases__ = CanvasObject.__bases__ + (DrawCanvasMixin,)
