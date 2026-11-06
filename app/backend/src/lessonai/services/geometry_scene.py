"""Canonical coordinates shared by measurement, web and export."""
import math
from lessonai.services.visual_requirements import VisualError, fingerprint

KINDS = {"cube", "square_pyramid_regular", "square_pyramid_at_a"}


def normalize_spec(data):
    raw_kind = data.get("polyhedron_type")
    kind = raw_kind.strip().lower() if isinstance(raw_kind, str) else raw_kind
    if kind not in KINDS:
        raise VisualError("Cần chọn rõ lập phương, chóp đều đáy vuông hoặc chóp có SA vuông góc đáy")
    try:
        a = float(data["base_edge"])
        h = a if kind == "cube" else float(data["height"])
    except (KeyError, TypeError, ValueError):
        raise VisualError("Thiếu cạnh đáy hoặc chiều cao") from None
    if not all(math.isfinite(v) and 0 < v <= 1e6 for v in (a, h)):
        raise VisualError("Số đo phải dương, hữu hạn và trong giới hạn")
    if kind == "cube" and data.get("height") is not None and float(data["height"]) != a:
        raise VisualError("Chiều cao hình lập phương phải bằng cạnh")
    return {"polyhedron_type": kind, "base_edge": a, "height": h}


def build_scene(data):
    spec = normalize_spec(data)
    a, h, kind = spec["base_edge"], spec["height"], spec["polyhedron_type"]
    vertices = {"A": [0, 0, 0], "B": [a, 0, 0], "C": [a, a, 0], "D": [0, a, 0]}
    edges = [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"]]
    faces = [["A", "B", "C", "D"]]
    if kind == "cube":
        for name in ("A", "B", "C", "D"):
            vertices[name + "'"] = [*vertices[name][:2], a]
            edges.append([name, name + "'"])
        edges.extend([[u + "'", v + "'"] for u, v in edges[:4]])
        faces += [["A'", "B'", "C'", "D'"]] + [[u, v, v + "'", u + "'"] for u, v in edges[:4]]
        volume = a ** 3
        foot = [0, 0, 0]
    else:
        foot = [a / 2, a / 2, 0] if kind == "square_pyramid_regular" else [0, 0, 0]
        vertices["S"] = [foot[0], foot[1], h]
        edges.extend([["S", name] for name in ("A", "B", "C", "D")])
        faces += [["S", u, v] for u, v in edges[:4]]
        volume = a * a * h / 3
    lengths = {f"{u}-{v}": math.dist(vertices[u], vertices[v]) for u, v in edges}
    # These checks deliberately use coordinates, not independent formula labels.
    assert all(math.isclose(lengths[f"{u}-{v}"], a) for u, v in edges[:4])
    if kind == "square_pyramid_regular":
        assert all(math.isclose(lengths["S-A"], lengths[f"S-{v}"]) for v in ("B", "C", "D"))
    return {"spec": spec, "vertices": vertices, "edges": edges, "faces": faces,
            "measurements": {"base_area": a*a, "height": h, "volume": volume, "edge_lengths": lengths},
            "altitude_foot": foot, "scene_fingerprint": fingerprint(spec), "status": "constraints_checked"}


def render_scene_png(spec, deck_id, slide_id):
    from lessonai.services.visual_requirements import checked_requirement
    if spec.get("deck_id") != deck_id or spec.get("slide_id") != slide_id:
        raise VisualError("Hình không thuộc slide đang xuất")
    checked_requirement(spec)
    scene = build_scene(spec)
    return _draw_scene(scene)


from lessonai.core.render_runtime import serialized_render


@serialized_render
def _draw_scene(scene):
    import io
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(5, 4))
    try:
        ax = fig.add_subplot(111, projection="3d")
        import numpy as np
        ax.view_init(elev=30, azim=-60)
        vertices={name:np.asarray(point,dtype=float) for name,point in scene["vertices"].items()}
        center=np.mean(list(vertices.values()),axis=0)
        camera=np.array([math.cos(math.pi/6)*math.cos(-math.pi/3),math.cos(math.pi/6)*math.sin(-math.pi/3),math.sin(math.pi/6)])
        front_faces=[]
        for face in scene["faces"]:
            points=[vertices[name] for name in face]
            normal=np.cross(points[1]-points[0],points[2]-points[0])
            if np.dot(normal,np.mean(points,axis=0)-center)<0:normal=-normal
            if np.dot(normal,camera)>1e-9:front_faces.append(set(face))
        for u, v in scene["edges"]:
            a, b = vertices[u],vertices[v]
            visible=any(u in face and v in face for face in front_faces)
            ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]], color="#2563eb",linestyle="-" if visible else "--",linewidth=1.6)
        for name, point in scene["vertices"].items():
            ax.text(*point, name)
        a, h = scene["spec"]["base_edge"], scene["spec"]["height"]
        ax.set_box_aspect((a, a, h))
        ax.set_axis_off()
        with io.BytesIO() as buffer:
            fig.savefig(buffer, format="png", dpi=120, transparent=True)
            return buffer.getvalue()
    finally:
        plt.close(fig)
