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

    def _transformedpoint(self, matrix):
        '''Not intended to be called by end users.'''
        pt = svgbase.createSVGPoint()
        (pt.x, pt.y) = self.XY
        pt =  pt.matrixTransform(matrix)
        return Point((pt.x, pt.y))

    def _transformedpointsetlist(self, matrix):
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
        elif isinstance(self, PointObject):
            self.XY = self._transformedpoint(matrix)
        elif isinstance(self, PolygonObject):
            #window.transformpoints([self.points], matrix)
            self._transformpoints(self.points, matrix)
            self._pointList = None
            self._segments = None
        else:
            self.pointList = self._transformedpointlist(matrix)
            if isinstance(self, BezierObject): self.pointsetList = self._transformedpointsetlist(matrix)
            self._update()
        hittarget = getattr(self, "hitTarget", None)
        if hittarget:
            hittarget.pointList = self.pointList
            if isinstance(self, BezierObject): hittarget.pointsetList = self.pointsetList
            hittarget._update()

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

    def rotateAndTranslate(self, angle, centre=None, vector=(0,0)):
        '''Rotate object clockwise by `angle` degrees around `centre`, and then translate by `vector`.
        If `centre` is not given, it is the centre of the object's bounding box.'''
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

    def enlarge(self, scalefactor, centre=(0,0)):
        '''Enlarge object by scale factor scalefactor, from centre.
        If centre is not given, the centre is the origin.'''
        (cx, cy) = centre
        matrix = svgbase.createSVGMatrix()
        matrix = matrix.translate(cx, cy)
        matrix = matrix.scale(scalefactor)
        matrix = matrix.translate(-cx, -cy)
        self.matrixTransform(matrix)

class TransformCanvasMixin(object):
    def _prepareTransform(self, event):
        self.selectedObject = self.getSelectedObject(event.target.id)
        if self.selectedObject and not self.selectedObject.fixed:
            self <= self.selectedObject
            self.showTransformHandles(self.selectedObject)
            if TransformType.TRANSLATE in self.transformTypes: self.transformHandles[TransformType.TRANSLATE]._select(event)
        else:
            self.hideTransformHandles()

    def _endTransform(self, event):
        if not isinstance(self.mouseOwner, TransformHandle): return
        currentcoords = self.getSVGcoords(event)
        offset = currentcoords - self.StartPoint
        if offset.coords != [0, 0]:
            centre = (cx, cy) = self.selectedObject.centre
            vec1 = (x1, y1) = self.StartPoint - centre
            vec2 = (x2, y2) = currentcoords - centre
            transformtype = self.mouseOwner.transformType

            self.selectedObject.style.transform = "translate(0px,0px)"
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

            if self.edgeSnap: self._doEdgeSnap(self.selectedObject)
            elif self.vertexSnap: self._doVertexSnap(self.selectedObject)

        if self.transformorigin:
            self.removeChild(self.transformorigin)
            self.transformorigin = None
        self.showTransformHandles(self.selectedObject)
        self.mouseOwner = None

    def showTransformHandles(self, svgobj):
        tempgroup = svg.g() #Needed to overcome bug in browser getBBox implementations
        tempgroup <= svgobj.cloneNode(True)
        self <= tempgroup
        bbox = tempgroup.getBBox()
        (x1, y1), (x2, y2) = svgobj.bbox = (bbox.x, bbox.y), (bbox.x+bbox.width, bbox.y+bbox.height)
        self.removeChild(tempgroup)
        (cx, cy) = svgobj.centre = Point(((x1+x2)/2, (y1+y2)/2))
        ((left, top), (right, bottom)) = self.viewWindow

        if not self.transformHandles: self.transformHandles = [self.transformBBox] + [TransformHandle(None, i, (0,0), self) for i in range(1,6)]
        for i, coords in enumerate([((x1+x2)/2,(y1+y2)/2), (x1,y1), (x2,(y1+y2)/2), ((x1+x2)/2,y2), (x2,y2)]):
            self.transformHandles[i+1].XY = coords
            self.transformHandles[i+1].owner = svgobj
        self.hideTransformHandles()

        self.usebox = False
        for ttype in self.transformTypes:
            if ttype in [TransformType.XSTRETCH, TransformType.YSTRETCH, TransformType.ENLARGE]: self.usebox = True

        if self.usebox:
            self.transformBBox.setPointList([Point((x1,y1)),Point((x2,y2))])
            #self.transformBBox._update()
            self <= self.transformBBox
            self.transformBBox.style.visibility = "visible"
        else:
            handlelength = min((bottom-top)*0.4, (y2-y1)*2)
            ypos = cy-handlelength
            if ypos < top: ypos = cy+handlelength
            handleposition = Point(((x1+x2)/2, ypos))
            self.transformHandles[2].XY = handleposition
            self.rotateLine.setPointList([svgobj.centre, handleposition])
            #self.rotateLine._update()
            self <= self.rotateLine
            self.rotateLine.style.visibility = "visible"
        for ttype in self.transformTypes:
            thandle = self.transformHandles[ttype]
            self <= thandle
            if ttype != TransformType.TRANSLATE: thandle.style.visibility = "visible"
        return [(x1,y1), (x2,y2)]

    def hideTransformHandles(self):
        for obj in self.transformHandles: obj.style.visibility = "hidden"
        self.rotateLine.style.visibility = "hidden"

    def _showTransformOrigin(self, svgobj, transformtype):
        (cx, cy) = svgobj.centre
        (x1, y1), (x2, y2) = svgobj.bbox
        if transformtype in [TransformType.NONE, TransformType.TRANSLATE]: return
        if transformtype in [TransformType.ROTATE, TransformType.ENLARGE]:
            self.transformorigin = PointObject((cx, cy), colour="blue", pointsize=4,canvas=self)
        elif transformtype == TransformType.XSTRETCH:
            self.transformorigin = LineObject([(cx,y1), (cx,y2)], linecolour="blue", linewidth=2)
        elif transformtype == TransformType.YSTRETCH:
            self.transformorigin = LineObject([(x1, cy), (x2, cy)], linecolour="blue", linewidth=2)
        self.transformorigin.style.vectorEffect = "non-scaling-stroke"
        self <= self.transformorigin

    def _movePoint(self, event):
        x = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        y = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        dx, dy = x-self.currentx, y-self.currenty
        if "touch" in event.type and abs(dx) < 5 and abs(dy) < 5: return
        self.currentx, self.currenty = x, y
        coords = self.getSVGcoords(event)
        if self.mouseMode == MouseMode.DRAW:
            self.mouseOwner._movePoint(coords)
        else:
            if self.mouseMode == MouseMode.TRANSFORM: dx, dy = x-self.startx, y-self.starty
            dx, dy = dx*self.scaleFactor, dy*self.scaleFactor
            self.mouseOwner._movePoint((dx, dy))
        return coords

class TransformHandle(PointObject):
    def __init__(self, owner, transformtype, coords, canvas):
        pointsize = 7 if canvas.mouseDetected else 15
        opacity = 0.4
        strokewidth = 3
        PointObject.__init__(self, coords, "red", pointsize, canvas)
        self.style.fillOpacity = opacity
        self.style.strokeWidth = strokewidth
        self.style.vectorEffect = "non-scaling-stroke"
        self.owner = owner
        self.canvas = canvas
        self.transformType = transformtype
        self.bind("mousedown", self._select)
        self.bind("touchstart", self._select)

    def _select(self, event):
        event.stopPropagation()
        self.canvas.mouseOwner = self
        self.startx, self.starty = self.canvas.StartPoint = self.canvas.getSVGcoords(event)
        self.canvas.startx = self.canvas.currentx = event.targetTouches[0].clientX if "touch" in event.type else event.clientX
        self.canvas.starty = self.canvas.currenty = event.targetTouches[0].clientY if "touch" in event.type else event.clientY
        self.canvas.hideTransformHandles()
        if self.transformType == TransformType.ROTATE: self.canvas.rotateLine.style.visibility = "visible"
        if self.transformType != TransformType.TRANSLATE: self.style.visibility = "visible"
        self.canvas._showTransformOrigin(self.owner, self.transformType)

    def _movePoint(self, offset):
        (dx, dy) = offset
        if (dx, dy) == (0, 0): return
        (x, y) = self.startx + dx, self.starty + dy
        self.XY = (x, y)
        if self.transformType == TransformType.TRANSLATE:
            transformstring = f"translate({dx}px,{dy}px)"
            if isinstance(self.owner, [EllipseObject, RectangleObject]) and self.owner.angle != 0:
                self.owner.style.transform = transformstring + self.owner.rotatestring
            else:
                self.owner.style.transform = transformstring
            return

        (cx, cy) = self.owner.centre
        (x1, y1) = self.startx - cx, self.starty - cy
        (x2, y2) = x -cx, y - cy
        #self.owner.style.transformOrigin = f"{cx}px {cy}px"
        if self.transformType == TransformType.ROTATE:
            (x3, y3) = (x1*x2+y1*y2, x1*y2-x2*y1)
            angle = atan2(y3, x3)*180/pi
            transformstring = f"translate({cx}px,{cy}px) rotate({angle}deg) translate({-cx}px,{-cy}px)"
            if not self.canvas.usebox:
                self.canvas.rotateLine.pointList = [self.owner.centre, self.XY]
                self.canvas.rotateLine._update()
        elif self.transformType == TransformType.XSTRETCH:
            xfactor = x2/x1
            yfactor = xfactor if isinstance(self.owner, CircleObject) else 1
            transformstring = f"translate({cx}px,{cy}px) scale({xfactor},{yfactor}) translate({-cx}px,{-cy}px)"
        elif self.transformType == TransformType.YSTRETCH:
            yfactor = y2/y1
            xfactor = yfactor if isinstance(self.owner, CircleObject) else 1
            transformstring = f"translate({cx}px,{cy}px) scale({xfactor},{yfactor}) translate({-cx}px,{-cy}px)"
        elif self.transformType == TransformType.ENLARGE:
            transformstring = f"translate({cx}px,{cy}px) scale({hypot(x2, y2)/hypot(x1, y1)}) translate({-cx}px,{-cy}px)"

        if isinstance(self.owner, [EllipseObject, RectangleObject]) and self.owner.angle != 0:
            self.owner.style.transform = self.owner.rotatestring + transformstring
        else:
            self.owner.style.transform = transformstring

classes = [LineObject, RectangleObject, EllipseObject, CircleObject, PolylineObject, PolygonObject, BezierObject,
ClosedBezierObject, SmoothBezierObject, SmoothClosedBezierObject, PointObject, RegularPolygon, GroupObject]
for cls in classes:
    cls.__bases__ = cls.__bases__ + (TransformMixin,)
    #print(cls, cls.__bases__)
CanvasObject.__bases__ = CanvasObject.__bases__ + (TransformCanvasMixin,)
