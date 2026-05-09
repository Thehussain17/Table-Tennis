"""
game/geometry_utils.py
Lightweight procedural mesh helpers for Panda3D (no external model files needed).
"""
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, GeomVertexWriter,
    Geom, GeomTriangles, GeomNode, NodePath,
)


def _add_quad(vertex_w, normal_w, color_w, tris, vi,
              v0, v1, v2, v3, norm, color):
    for v in (v0, v1, v2, v3):
        vertex_w.addData3(*v)
        normal_w.addData3(*norm)
        color_w.addData4(*color)
    tris.addVertices(vi,   vi+1, vi+2)
    tris.addVertices(vi,   vi+2, vi+3)
    return vi + 4


def create_box(name: str, sx: float, sy: float, sz: float,
               color=(1, 1, 1, 1)) -> NodePath:
    """Solid axis-aligned box centred at origin, dimensions sx×sy×sz."""
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, 'vertex')
    nw = GeomVertexWriter(vdata, 'normal')
    cw = GeomVertexWriter(vdata, 'color')
    tris = GeomTriangles(Geom.UHStatic)

    hx, hy, hz = sx / 2, sy / 2, sz / 2
    faces = [
        # (normal, four CCW vertices when viewed from outside)
        ((0, 0, 1),  [(-hx,-hy, hz),( hx,-hy, hz),( hx, hy, hz),(-hx, hy, hz)]),
        ((0, 0,-1),  [(-hx,-hy,-hz),(-hx, hy,-hz),( hx, hy,-hz),( hx,-hy,-hz)]),
        ((1, 0, 0),  [( hx,-hy,-hz),( hx, hy,-hz),( hx, hy, hz),( hx,-hy, hz)]),
        ((-1, 0, 0), [(-hx,-hy,-hz),(-hx,-hy, hz),(-hx, hy, hz),(-hx, hy,-hz)]),
        ((0, 1, 0),  [(-hx, hy,-hz),(-hx, hy, hz),( hx, hy, hz),( hx, hy,-hz)]),
        ((0,-1, 0),  [(-hx,-hy,-hz),( hx,-hy,-hz),( hx,-hy, hz),(-hx,-hy, hz)]),
    ]

    vi = 0
    for norm, verts in faces:
        vi = _add_quad(vw, nw, cw, tris, vi, *verts, norm, color)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    return NodePath(node)


def create_sphere(name: str, radius: float, stacks: int = 12,
                  slices: int = 16, color=(1, 1, 1, 1)) -> NodePath:
    """UV-sphere centred at origin."""
    import math
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, 'vertex')
    nw = GeomVertexWriter(vdata, 'normal')
    cw = GeomVertexWriter(vdata, 'color')
    tris = GeomTriangles(Geom.UHStatic)

    for i in range(stacks + 1):
        phi = math.pi * i / stacks
        for j in range(slices + 1):
            theta = 2 * math.pi * j / slices
            x = math.sin(phi) * math.cos(theta)
            y = math.sin(phi) * math.sin(theta)
            z = math.cos(phi)
            vw.addData3(x * radius, y * radius, z * radius)
            nw.addData3(x, y, z)
            cw.addData4(*color)

    for i in range(stacks):
        for j in range(slices):
            a = i * (slices + 1) + j
            b = a + (slices + 1)
            tris.addVertices(a,   b,   a+1)
            tris.addVertices(a+1, b,   b+1)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    return NodePath(node)


def create_cylinder(name: str, radius: float, height: float,
                    segments: int = 20, color=(1, 1, 1, 1)) -> NodePath:
    """Solid cylinder along Z axis, centred at origin."""
    import math
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, 'vertex')
    nw = GeomVertexWriter(vdata, 'normal')
    cw = GeomVertexWriter(vdata, 'color')
    tris = GeomTriangles(Geom.UHStatic)

    hz = height / 2
    vi = 0

    # Side faces
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        x0, y0 = math.cos(a0) * radius, math.sin(a0) * radius
        x1, y1 = math.cos(a1) * radius, math.sin(a1) * radius
        for (x, y) in [(x0, y0), (x1, y1), (x1, y1), (x0, y0)]:
            pass  # handled below
        pts = [(x0, y0, -hz), (x1, y1, -hz), (x1, y1, hz), (x0, y0, hz)]
        norms = [(x0/radius, y0/radius, 0)] * 2 + [(x1/radius, y1/radius, 0)] * 2
        for p, n in zip(pts, norms):
            vw.addData3(*p); nw.addData3(*n); cw.addData4(*color)
        tris.addVertices(vi, vi+1, vi+2)
        tris.addVertices(vi, vi+2, vi+3)
        vi += 4

    # Top / bottom caps
    for z, nz in [(hz, 1), (-hz, -1)]:
        cx_i = vi
        vw.addData3(0, 0, z); nw.addData3(0, 0, nz); cw.addData4(*color)
        vi += 1
        for i in range(segments):
            a = 2 * math.pi * i / segments
            vw.addData3(math.cos(a)*radius, math.sin(a)*radius, z)
            nw.addData3(0, 0, nz); cw.addData4(*color)
            vi += 1
        for i in range(segments):
            a = cx_i + 1 + i
            b = cx_i + 1 + (i + 1) % segments
            if nz > 0:
                tris.addVertices(cx_i, a, b)
            else:
                tris.addVertices(cx_i, b, a)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    return NodePath(node)
