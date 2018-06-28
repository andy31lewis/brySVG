#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2008-2018 Andy Lewis                                               #
# --------------------------------------------------------------------------- #
# This program is free software; you can redistribute it and/or modify it     #
# under the terms of the GNU General Public License version 2 as published by #
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,     #
# MA 02111-1307 USA                                                           #
# This program is distributed in the hope that it will be useful, but WITHOUT #
# ANY WARRANTY. See the GNU General Public License for more details.          #

from browser import document
from .SVGobjects import *

def delete(element):
    element.parentNode.removeChild(element)
    del element

class UserSVGCanvas(CanvasObject):
    def __init__(self, width, height, colour):
        CanvasObject.__init__(self, width, height, colour)
        self.PathTypes = {"polygon":UserPolygon, "polyline":UserPolyline, "ellipse":UserEllipse, "bezier":UserBezier, "closedbezier":UserClosedBezier}
        self.bind("contextmenu", self.OnCanvasRightClick)
        self.bind("mousemove", self.OnCanvasMove)
        self.bind("mouseup", self.OnCanvasLeftUp)
        self.bind("mousedown", self.OnCanvasLeftDown)
        #self.bind("touchmove", self.OnCanvasMove)
        #self.bind("touchend", self.OnCanvasLeftUp)
        #self.bind("touchstart", self.OnCanvasLeftDown)
        self.bind("dblclick", self.OnCanvasDoubleClick)
        document.bind("keydown", self.DeleteSelection)

        self.Tool = "select"
        self.PenColour = None
        self.FillColour  = None
        self.PenWidth = 5
        self.PathList = []

    def getSVGcoords(self, event):
        pt = self.createSVGPoint()
        (pt.x, pt.y) = (event.clientX, event.clientY)
        SVGpt =  pt.matrixTransform(self.getScreenCTM().inverse())
        return (SVGpt.x, SVGpt.y)

    def OnCanvasRightClick(self, event):
        event.preventDefault()
    
    def OnCanvasMove(self, event):
        if self.MouseOwner:
            self.MouseOwner.OnMove(event)

    def OnCanvasLeftUp(self, event):
        if self.MouseOwner:
            self.MouseOwner.OnLeftUp(event)
    
    def OnCanvasLeftDown(self, event):
        if self.MouseOwner:
            self.MouseOwner.OnLeftDown(event)
            return
        
        if self.SelectedPath:
            self.DeSelectPath()
        
        if self.Tool in self.PathTypes.keys():
            coords = self.getSVGcoords(event)
            print (coords)
            self.NewPath = self.PathTypes[self.Tool](coords, self)

    def OnCanvasDoubleClick(self,event):
        if self.MouseOwner:
            self.MouseOwner.OnDoubleClick(event)
            self.Tool = "select"
            
    def DeSelectPath(self):
        if self.SelectedPath:
            delete(self.SelectedPath.Handles)
            if isinstance(self.SelectedPath, (UserBezier, UserClosedBezier)):
                delete(self.SelectedPath.ControlHandlesGroup)
                del self.SelectedPath.ControlHandles
            self.MouseOwner = self.SelectedPath = None

    def DeleteSelection(self,event):
        #print (event.target, event.currentTarget)
        if event.keyCode == 46:
            if self.SelectedPath:
                delete(self.SelectedPath.Handles)
                if isinstance(self.SelectedPath, (UserBezier, UserClosedBezier)):
                    delete(self.SelectedPath.ControlHandlesGroup)
                    del self.SelectedPath.ControlHandles
                delete(self.SelectedPath)
                self.PathList.remove(self.SelectedPath)
                self.SelectedPath = None
                
class PathMixin(object):
    '''Provides common functions for each of the path classes below'''
    def initialise(self, Parent):
        self.Parent = Parent
        self.Parent <= self
        
        self.LineColour = self.Parent.PenColour
        self.LineWidth = self.Parent.PenWidth
        self.FillColour = self.Parent.FillColour
        self.Parent.PathList.append(self)
        self.bind("click", self.SelectPath)
        if self.Parent.Tool != "select":
            self.Type = self.Parent.Tool
            self.Parent.MouseOwner = self

    def OnLeftDown(self, event):
        if self.Parent.Tool in ("polygon", "polyline", "bezier", "closedbezier"):
            coords = self.Parent.getSVGcoords(event)
            self.AppendPoint(coords)

    def OnMove(self, event):
        coords = self.Parent.getSVGcoords(event)
        self.SetPoint(-1, coords)

    def OnLeftUp(self, event):
        pass

    def OnDoubleClick(self, event):
        if self.Parent.Tool in ["polygon", "polyline", "bezier", "closedbezier"]:
            self.DeletePoints(-2, None)
        self.Parent.MouseOwner = None

    def SelectPath(self, object):
        if self.Parent.Tool != "select": return
        if self.Parent.SelectedPath:
            self.Parent.DeSelectPath()
        self.Parent.SelectedPath = self
        self.Handles = GroupObject([Handle(self, i, coords) for i, coords in enumerate(self.PointList)], "handles")
        self.Parent <= self.Handles
        if isinstance(self, UserBezier):
            controlhandles = []
            last = len(self.FullPointList)-1
            for i, point in enumerate(self.FullPointList):
                if i == 0: controlhandles.append((ControlHandle(self, i, 1, point[1]), ))
                elif i == last: controlhandles.append((ControlHandle(self, i, 0, point[0]), ))
                else:
                    controlhandles.append((ControlHandle(self, i, 0, point[0]), ControlHandle(self, i, 2, point[2])))
            self.ControlHandles = controlhandles
            self.ControlHandlesGroup = GroupObject([ch for chset in controlhandles for ch in chset], "controlhandles")
            self.Parent <= self.ControlHandlesGroup

class UserPolygon(PolygonObject, PathMixin):
    def __init__(self, coords, Parent):
        self.initialise(Parent)
        PolygonObject.__init__(self, [coords, coords], self.LineColour, self.LineWidth, self.FillColour)
        
class UserPolyline(PolylineObject, PathMixin):
    def __init__(self, coords, Parent):
        self.initialise(Parent)
        PolylineObject.__init__(self, [coords, coords], self.LineColour, self.LineWidth)
        
class UserEllipse(EllipseObject, PathMixin):
    def __init__(self, coords, Parent):
        self.initialise(Parent)
        EllipseObject.__init__(self, [coords, coords], self.LineColour, self.LineWidth, self.FillColour)
        
class UserBezier(SmoothBezierObject, PathMixin):
    def __init__(self, coords, Parent):
        self.initialise(Parent)
        SmoothBezierObject.__init__(self, [coords, coords], self.LineColour, self.LineWidth)
        
class UserClosedBezier(SmoothClosedBezierObject, PathMixin):
    def __init__(self, coords, Parent):
        self.initialise(Parent)
        SmoothClosedBezierObject.__init__(self, [coords, coords], self.LineColour, self.LineWidth, self.FillColour)
        
    def SelectPath(self, object):
        if self.Parent.Tool != "select": return
        if self.Parent.SelectedPath:
            self.Parent.DeSelectPath()
        self.Parent.SelectedPath = self
        self.Handles = GroupObject([Handle(self, i, coords) for i, coords in enumerate(self.PointList)], "handles")
        self.Parent <= self.Handles
        
        controlhandles = []
        for i, point in enumerate(self.FullPointList):
            controlhandles.append((ControlHandle(self, i, 0, point[0]), ControlHandle(self, i, 2, point[2])))
        self.ControlHandles = controlhandles
        self.ControlHandlesGroup = GroupObject([ch for chset in controlhandles for ch in chset], "controlhandles")
        self.Parent <= self.ControlHandlesGroup

class Handle(PointObject):
    def __init__(self, owner, index, coords):
        PointObject.__init__(self, coords, "red", 5)
        self.owner = owner
        self.index = index
        self.bind("mousedown", self.Select)
    
    def Select(self, event):
        event.stopPropagation()
        if self.owner.Parent.MouseOwner == None:
            self.owner.Parent.MouseOwner = self

    def OnMove(self,event):
        offset = Point(self.owner.Parent.getSVGcoords(event)) - self.XY
        self.XY += offset
        if isinstance(self.owner, UserBezier):
            last = len(self.owner.FullPointList)-1
            pointset = [self.XY, None] if self.index==0 else [None, self.XY] if self.index==last else [None, self.XY, None]
            for ch in self.owner.ControlHandles[self.index]:
                ch.XY += offset
                pointset[ch.subindex] = ch.XY
            self.owner.SetPointset(self.index, pointset)
        elif isinstance(self.owner, UserClosedBezier):
            pointset = [None, self.XY, None]
            for ch in self.owner.ControlHandles[self.index]:
                ch.XY += offset
                pointset[ch.subindex] = ch.XY
            self.owner.SetPointset(self.index, pointset)
        else:
            self.owner.SetPoint(self.index, self.XY)

    def OnLeftUp(self, event):
        self.owner.Parent.MouseOwner = None

class ControlHandle(PointObject):
    def __init__(self, owner, index, subindex, coords):
        PointObject.__init__(self, coords, "green", 5)
        self.owner = owner
        self.index = index
        self.subindex = subindex
        self.bind("mousedown", self.Select)
    
    def Select(self, event):
        event.stopPropagation()
        if self.owner.Parent.MouseOwner == None:
            self.owner.Parent.MouseOwner = self

    def OnMove(self,event):
        newcoords = Point(self.owner.Parent.getSVGcoords(event))
        self.XY = newcoords

        pointset = list(self.owner.FullPointList[self.index])
        if len(pointset) == 3:
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

    def OnLeftUp(self, event):
        self.owner.Parent.MouseOwner = None
