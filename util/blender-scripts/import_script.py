import os
import re
import xml.etree.ElementTree as ET
import bpy

SCALE = 1.0


def parse_mat(path):
    mats = {}
    if not os.path.exists(path):
        return mats
    with open(path, "r") as f:
        text = f.read()
    for m in re.finditer(r"material\s+([^\s{]+)", text):
        name = m.group(1)
        body = text[m.end() :]
        bc, end_idx = 0, 0
        for j, char in enumerate(body):
            if char == "{":
                bc += 1
            elif char == "}":
                bc -= 1
            if bc == 0 and j > 0:
                end_idx = j
                break
        t_list = []
        for line in body[:end_idx].splitlines():
            line = line.strip()
            if line.startswith(
                "texture "
            ) and not line.startswith("//"):
                tk = line.split()
                if len(tk) >= 2:
                    # TRUE FIX: Extract the filename string item [1]
                    # instead of assigning the full text row array block!
                    t_list.append(tk[1].strip())
        t1 = t_list[0] if len(t_list) >= 1 else None
        t2 = t_list[1] if len(t_list) >= 2 else None
        if t1 or t2:
            mats[name] = (t1, t2)
    return mats


def make_node_mat(name, t1, t2, fdir):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "OPAQUE"

    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    k = (
        "Specular IOR Level"
        if "Specular IOR Level" in bsdf.inputs
        else "Specular"
    )
    bsdf.inputs[k].default_value = 0.0
    if not t1 and not t2:
        bsdf.inputs["Base Color"].default_value = (1, 0, 1, 1)
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        return mat
    uv1 = nodes.new("ShaderNodeUVMap")
    uv1.uv_map, uv1.location = "UVMap_1", (-650, 200)
    tex1 = nodes.new("ShaderNodeTexImage")
    tex1.location = (-400, 200)
    if t1:
        p1 = os.path.join(fdir, t1)
        if os.path.exists(p1):
            img1 = bpy.data.images.load(p1)
            img1.alpha_mode = "STRAIGHT"
            img1.pack()
            tex1.image = img1
    links.new(uv1.outputs["UV"], tex1.inputs["Vector"])

    if not t2:
        links.new(tex1.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        try:
            mix = nodes.new("ShaderNodeMix")
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            amb = nodes.new("ShaderNodeMix")
            # UPDATED: Changed from MIX to ADD blend type
            amb.data_type, amb.blend_type = "RGBA", "ADD"
            # UPDATED: Set blend factor calculation to 0.3
            amb.inputs["Factor"].default_value = 0.3
        except:
            mix = nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MULTIPLY"
            mix.inputs["Fac"].default_value = 1.0
            amb = nodes.new("ShaderNodeMixRGB")
            # UPDATED: Changed from MIX to ADD blend type
            amb.blend_type = "ADD"
            # UPDATED: Set legacy factor property slider to 0.3
            amb.inputs["Fac"].default_value = 0.3
        mix.location, amb.location = (-150, 100), (100, 200)
        uv2 = nodes.new("ShaderNodeUVMap")
        uv2.uv_map, uv2.location = "UVMap_2", (-650, -100)
        tex2 = nodes.new("ShaderNodeTexImage")
        tex2.location = (-400, -100)
        if t2:
            p2 = os.path.join(fdir, t2)
            if os.path.exists(p2):
                img2 = bpy.data.images.load(p2)
                img2.alpha_mode = "STRAIGHT"
                img2.pack()
                tex2.image = img2
        links.new(uv2.outputs["UV"], tex2.inputs["Vector"])
        if mix.type == "MIX_RGB":
            links.new(
                tex1.outputs["Color"], mix.inputs["Color1"]
            )
            links.new(
                tex2.outputs["Color"], mix.inputs["Color2"]
            )
            links.new(
                mix.outputs["Color"], amb.inputs["Color1"]
            )
            links.new(
                tex1.outputs["Color"], amb.inputs["Color2"]
            )
            links.new(
                amb.outputs["Color"], bsdf.inputs["Base Color"]
            )
        else:
            links.new(tex1.outputs["Color"], mix.inputs["A"])
            links.new(tex2.outputs["Color"], mix.inputs["B"])
            links.new(mix.outputs["Result"], amb.inputs["A"])
            links.new(tex1.outputs["Color"], amb.inputs["B"])
            links.new(
                amb.outputs["Result"], bsdf.inputs["Base Color"]
            )

    links.new(tex1.outputs["Alpha"], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def load_xml(fpath, m_dict, fdir):
    try:
        root = ET.parse(fpath).getroot()
    except:
        return
    verts, norms, uv1, uv2 = [], [], [], []
    geom = root.find(".//sharedgeometry")
    if geom is not None:
        vbuf = geom.find("vertexbuffer")
        has_n = (
            vbuf is not None and vbuf.get("normals") == "true"
        )
        for v in geom.findall(".//vertex"):
            p = v.find("position")
            verts.append(
                (
                    -float(p.get("x")) * SCALE,
                    float(p.get("z")) * SCALE,
                    float(p.get("y")) * SCALE,
                )
            )
            if has_n:
                n = v.find("normal")
                norms.append(
                    (
                        -float(n.get("x")),
                        float(n.get("z")),
                        float(n.get("y")),
                    )
                )
            tc = v.findall("texcoord")
            u1 = float(tc[0].get("u")) if len(tc) >= 1 else 0.0
            v1 = 1.0 - float(tc[0].get("v")) if len(tc) >= 1 else 0.0
            uv1.append((u1, v1))
            u2 = float(tc[1].get("u")) if len(tc) >= 2 else 0.0
            v2 = 1.0 - float(tc[1].get("v")) if len(tc) >= 2 else 0.0
            uv2.append((u2, v2))
    if not verts:
        return
    # FIXED: Extract [0] array block item string to drop tuple conversion
    b_name = os.path.splitext(os.path.basename(fpath))[0]
    mesh_data = bpy.data.meshes.new(b_name)
    obj = bpy.data.objects.new(mesh_data.name, mesh_data)
    bpy.context.collection.objects.link(obj)
    faces, f_mats = [], []
    sub_el = root.find("submeshes")
    if sub_el is not None:
        for idx, sub in enumerate(sub_el.findall("submesh")):
            m_name = sub.get("material")
            t1, t2 = m_dict.get(m_name, (None, None))
            obj.data.materials.append(make_node_mat(m_name, t1, t2, fdir))
            f_el = sub.find("faces")
            if f_el is not None:
                for f in f_el.findall("face"):
                    faces.append(
                        (
                            int(f.get("v1")),
                            int(f.get("v2")),
                            int(f.get("v3")),
                        )
                    )
                    f_mats.append(idx)
    else:
        for f_el in root.findall(".//faces"):
            for f in f_el.findall("face"):
                faces.append(
                    (
                        int(f.get("v1")),
                        int(f.get("v2")),
                        int(f.get("v3")),
                    )
                )
                f_mats.append(0)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.validate()
    mesh_data.update()
    for i, face in enumerate(mesh_data.polygons):
        if i < len(f_mats):
            face.material_index = f_mats[i]
    u1 = mesh_data.uv_layers.new(name="UVMap_1")
    for lp in mesh_data.loops:
        u1.data[lp.index].uv = uv1[lp.vertex_index]
    u2 = mesh_data.uv_layers.new(name="UVMap_2")
    for lp in m_data.loops if "m_data" in locals() else mesh_data.loops:
        u2.data[lp.index].uv = uv2[lp.vertex_index]
    if norms and len(norms) == len(verts):
        try:
            mesh_data.normals_split_custom_set(
                [norms[lp.vertex_index] for lp in mesh_data.loops]
            )
        except:
            pass
    mesh_data.update()


def run_batch(fdir):
    if not os.path.exists(fdir):
        return
    m_cache = {}
    for fn in os.listdir(fdir):
        if fn.lower().endswith(".material"):
            p = os.path.join(fdir, fn)
            m_cache.update(parse_mat(p))
    for fn in os.listdir(fdir):
        if fn.lower().endswith(".mesh.xml"):
            p = os.path.join(fdir, fn)
            load_xml(p, m_cache, fdir)

# Update the system folder directory below
run_batch("/home/ryan-de-boer/Meshes/BS3/park/parkscene4/")
