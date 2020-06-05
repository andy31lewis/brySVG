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

from brySVG.dragcanvas import *

class TransformMixin(object):
    '''Provides methods for objects to be translated, rotated, stretched or enlarged.
    Note that if no mouse interaction is needed with the objects after the transformation, it is better to use the
    translateElement, rotateElement, scaleElement methods provided by the CanvasObject, as they are much faster.'''

    def transformedpointlist(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        newpointlist = []
        for point in self.pointList:
            (pt.x, pt.y) = point
            pt =  pt.matrixTransform(matrix)
            newpointlist.append(Point((pt.x, pt.y)))
        return newpointlist

    def transformedpoint(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        (pt.x, pt.y) = self.XY
        pt =  pt.matrixTransform(matrix)
        return Point((pt.x, pt.y))

    def transformedpointsetlist(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        newpointsetlist = []
        for pointset in self.pointsetList:
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

    def matrixTransform(self, matrix):
        '''Transform object using a SVGmatrix'''
        if isinstance(self, GroupObject):
            for obj in self.objectList:
                obj.matrixTransform(matrix)
            return
        elif isinstance(self, PointObject):
            self.XY = self.transformedpoint(matrix)
        else:
            self.pointList = self.transformedpointlist(matrix)
            if isinstance(self, BezierObject): self.pointsetList = self.transformedpointsetlist(matrix)
            hittarget = getattr(self, "hitTarget", None)
            if hittarget:
                hittarget.pointList = self.pointList
                if isinstance(self, BezierObject): hittarget.pointsetList = self.pointsetList
                hittarget.update()
        self.update()

    def translate(self, vector):
        '''Translate object by vector'''
        t = svgbase.createSVGTransform()
        t.setTranslate(*vector)
        self.matrixTransform(t.matrix)

    def rotate(self, angle, centre=None):
        '''Rotate object clockwise by angle degrees around centre.
        If centre is not given, it is the centre of the object's bounding box.'''
        if not centre:
            bbox = self.getBBox()
            centre = (bbox.x+bbox.width/2, bbox.y+bbox.height/2)
        if isinstance(self, (EllipseObject, RectangleObject)):
            self.angle += angle
        t = svgbase.createSVGTransform()
        t.setRotate(angle, *centre)
        self.matrixTransform(t.matrix)

    def rotateandtranslate(self, angle, centre=None, vector=(0,0)):
        if not centre:
            bbox = self.getBBox()
            centre = (bbox.x+bbox.width/2, bbox.y+bbox.height/2)
        t = svgbase.createSVGTransform()
        if angle != 0: t.setRotate(angle, *centre)
        M = t.matrix.translate(*vector) if vector != (0,0) else t.matrix
        self.matrixTransform(M)

    def rotateByVectors(self, vec1, vec2, centre=(0, 0)):
        '''Rotate object clockwise by the angle between vec1 and vec2 around centre.
        If centre is not given, it is the origin.'''
        (cx, cy) = centre
        (x1, y1) = vec1
        (x2, y2) = vec2
        (x3, y3) = (x1*x2+y1*y2, x1*y2-x2*y1)
        angle = atan2(y3, x3)*180/pi
        if isinstance(self, (EllipseObject, RectangleObject)):
            self.angle += angle
        matrix = svgbase.createSVGMatrix()
        matrix = matrix.translate(cx, cy)
        matrix = matrix.rotateFromVector(x3, y3)
        matrix = matrix.translate(-cx, -cy)
        self.matrixTransform(matrix)

    def xstretch(self, xscale, cx=0):
        '''Stretch object in the x-direction by scale factor xscale, with invariant line x = cx.
        If cx is not given, the invariant line is the y-axis.'''
        angle = 0
        if isinstance(self, [EllipseObject, RectangleObject]) and self.angle != 0:
            angle = self.angle
            self.rotate(-angle)
        matrix = svgbase.createSVGMatrix()
        matrix = matrix.translate(cx, 0)
        matrix.a = xscale
        matrix = matrix.translate(-cx, 0)
        self.matrixTransform(matrix)
        if angle != 0: self.rotate(angle)

    def ystretch(self, yscale, cy=0):
        '''Stretch object in the y-direction by scale factor yscale, with invariant line y = cy.
        If cy is not given, the invariant line is the x-axis.'''
        angle = 0
        if isinstance(self, [EllipseObject, RectangleObject]) and self.angle != 0:
            angle = self.angle
            self.rotate(-angle)
        matrix = svgbase.createSVGMatrix()
        matrix = matrix.translate(0, cy)
        matrix.d = yscale
        matrix = matrix.translate(0, -cy)
        self.matrixTransform(matrix)
        if angle != 0: self.rotate(angle)

    def enlarge(self, scalefactor, centre):
        '''Enlarge object by scale factor scalefactor, from centre.
        If cx and cy are not given, the centre is the origin.'''
        (cx, cy) = centre
        matrix = svgbase.createSVGMatrix()
        matrix = matrix.translate(cx, cy)
        matrix = matrix.scale(scalefactor)
        matrix = matrix.translate(-cx, -cy)
        self.matrixTransform(matrix)

class TransformCanvasMixin(object):
    def prepareTransform(self, event):
        self.selectedObject = self.getSelectedObject(event.target.id)
        if self.selectedObject and not self.selectedObject.fixed:
            self <= self.selectedObject
            self.showTransformHandles(self.selectedObject)
            if TransformType.TRANSLATE in self.transformTypes: self.transformHandles[TransformType.TRANSLATE].select(event)
        else:
            self.hideTransformHandles()

    def endTransform(self, event):
        if not isinstance(self.mouseOwner, TransformHandle): return
        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.StartPoint
        if offset.coords != [0, 0]:
            centre = (cx, cy) = self.selectedObject.Centre
            vec1 = (x1, y1) = self.StartPoint - centre
            vec2 = (x2, y2) = currentcoords - centre
            transformtype = self.mouseOwner.transformType

            self.selectedObject.attrs["transform"] = ""
            if transformtype == TransformType.TRANSLATE:
                self.selectedObject.translate(offset)
            elif transformtype == TransformType.ROTATE:
                self.selectedObject.rotateByVectors(vec1, vec2, (cx, cy))
            elif transformtype == TransformType.XSTRETCH:
                self.selectedObject.xstretch(x2/x1, cx)
            elif transformtype == TransformType.YSTRETCH:
                self.selectedObject.ystretch(y2/y1, cy)
            elif transformtype == TransformType.ENLARGE:
                self.selectedObject.enlarge(hypot(x2, y2)/hypot(x1, y1), (cx, cy))

            if self.edgeSnap: self.doEdgeSnap(self.selectedObject)
            elif self.vertexSnap: self.doVertexSnap(self.selectedObject)

        if self.transformorigin:
            self.deleteObject(self.transformorigin)
            self.transformorigin = None
        self.showTransformHandles(self.selectedObject)
        self.mouseOwner = None

    def showTransformHandles(self, svgobj):
        tempgroup = GroupObject([svgobj.cloneNode(True)]) #Needed to overcome bug in browser getBBox implementations
        self <= tempgroup
        bbox = tempgroup.getBBox()
        x1, y1, x2, y2 = bbox.x, bbox.y, bbox.x+bbox.width, bbox.y+bbox.height
        self.deleteObject(tempgroup)
        svgobj.Centre = Point(((x1+x2)/2, (y1+y2)/2))

        self.transformBBox.pointList = [Point((x1,y1)),Point((x2,y2))]
        self.transformBBox.update()
        self <= self.transformBBox
        self.transformBBox.style.visibility = "visible"
        if not self.transformHandles: self.transformHandles = [self.transformBBox] + [TransformHandle(None, i, (0,0), self) for i in range(1,6)]
        for i, coords in enumerate([((x1+x2)/2,(y1+y2)/2), (x1,y1), (x2,(y1+y2)/2), ((x1+x2)/2,y2), (x2,y2)]):
            self.transformHandles[i+1].XY = coords
            self.transformHandles[i+1].owner = svgobj
        for ttype in self.transformTypes:
            thandle = self.transformHandles[ttype]
            self <= thandle
            if ttype != TransformType.TRANSLATE: thandle.style.visibility = "visible"
        return [(x1,y1), (x2,y2)]

    def hideTransformHandles(self):
        for obj in self.transformHandles: obj.style.visibility = "hidden"

    def showTransformOrigin(self, transformtype):
        [(x1,y1), (x2,y2)] = self.transformBBox.pointList
        (cx, cy) = ((x1+x2)/2, (y1+y2)/2)
        if transformtype in [TransformType.NONE, TransformType.TRANSLATE]: return
        if transformtype in [TransformType.ROTATE, TransformType.ENLARGE]:
            self.transformorigin = PointObject((cx, cy), colour="blue", pointsize=3,canvas=self)
        elif transformtype == TransformType.XSTRETCH:
            self.transformorigin = LineObject([(cx,y1), (cx,y2)], linecolour="blue", linewidth=2)
        elif transformtype == TransformType.YSTRETCH:
            self.transformorigin = LineObject([(x1, cy), (x2, cy)], linecolour="blue", linewidth=2)
        self <= self.transformorigin

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

class TransformHandle(PointObject):
    def __init__(self, owner, transformtype, coords, canvas):
        pointsize = 7 if canvas.mouseDetected else 15
        opacity = 1 if canvas.mouseDetected else 0.2
        strokewidth = 1 if canvas.mouseDetected else 3
        PointObject.__init__(self, coords, "red", pointsize, canvas)
        self.style.fillOpacity = opacity
        self.style.strokeWidth = strokewidth
        self.owner = owner
        self.canvas = canvas
        self.transformType = transformtype
        self.bind("mousedown", self.select)
        self.bind("touchstart", self.select)

    def select(self, event):
        event.stopPropagation()
        self.canvas.mouseOwner = self
        self.startx, self.starty = self.canvas.StartPoint = self.canvas.getSVGcoords(event)
        self.canvas.startx = self.canvas.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        self.canvas.starty = self.canvas.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        self.canvas.hideTransformHandles()
        if self.transformType != TransformType.TRANSLATE: self.style.visibility = "visible"
        self.canvas.showTransformOrigin(self.transformType)

    def movePoint(self, offset):
        (dx, dy) = offset
        if (dx, dy) == (0, 0): return
        (x, y) = self.startx + dx, self.starty + dy
        self.XY = (x, y)
        if self.transformType == TransformType.TRANSLATE:
            transformstring = "translate({},{})".format(dx, dy)
            if isinstance(self.owner, [EllipseObject, RectangleObject]) and self.owner.angle != 0:
                self.owner.attrs["transform"] = transformstring + self.owner.rotatestring
            else:
                self.owner.attrs["transform"] = transformstring
            return

        (cx, cy) = self.owner.Centre
        (x1, y1) = self.startx - cx, self.starty - cy
        (x2, y2) = x -cx, y - cy

        if self.transformType == TransformType.ROTATE:
            (x3, y3) = (x1*x2+y1*y2, x1*y2-x2*y1)
            angle = atan2(y3, x3)*180/pi
            transformstring = "rotate({},{},{})".format(angle,cx,cy)
        elif self.transformType == TransformType.XSTRETCH:
            xfactor = x2/x1
            yfactor = xfactor if isinstance(self.owner, CircleObject) else 1
            transformstring = "translate({},{}) scale({},{}) translate({},{})".format(cx, cy, xfactor, yfactor, -cx, -cy)
        elif self.transformType == TransformType.YSTRETCH:
            yfactor = y2/y1
            xfactor = yfactor if isinstance(self.owner, CircleObject) else 1
            transformstring = "translate({},{}) scale({},{}) translate({},{})".format(cx, cy, xfactor, yfactor, -cx, -cy)
        elif self.transformType == TransformType.ENLARGE:
            transformstring = "translate({},{}) scale({}) translate({},{})".format(cx, cy, hypot(x2, y2)/hypot(x1, y1), -cx, -cy)

        if isinstance(self.owner, [EllipseObject, RectangleObject]) and self.owner.angle != 0:
            self.owner.attrs["transform"] = self.owner.rotatestring + transformstring
        else:
            self.owner.attrs["transform"] = transformstring

classes = [LineObject, RectangleObject, EllipseObject, CircleObject, PolylineObject, PolygonObject, BezierObject,
ClosedBezierObject, SmoothBezierObject, SmoothClosedBezierObject, PointObject, RegularPolygon, GroupObject]
for cls in classes:
    cls.__bases__ = cls.__bases__ + (TransformMixin,)
    #print(cls, cls.__bases__)
CanvasObject.__bases__ = CanvasObject.__bases__ + (TransformCanvasMixin,)
