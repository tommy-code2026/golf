import base64
import math
import os
import random
import sys

import bpy


def build_relief(image_path, glb_path):
  if not os.path.isfile(image_path):
    raise FileNotFoundError(image_path)
  bpy.ops.object.select_all(action="SELECT")
  bpy.ops.object.delete(use_global=False)
  random.seed(101)

  def material(name, color, metallic=0.0, roughness=0.8):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return result

  grass = material("Meadow", (0.18, 0.36, 0.065))
  fairway = material("Fairway", (0.36, 0.58, 0.09))
  stripe = material("Mown grass", (0.47, 0.66, 0.13))
  green = material("Putting green", (0.55, 0.72, 0.19))
  sand = material("Bunker sand", (0.88, 0.81, 0.58))
  water = material("Lake water", (0.025, 0.34, 0.45), 0.35, 0.2)
  stone = material("Walkways", (0.57, 0.60, 0.54))
  dark = material("Island edge", (0.07, 0.15, 0.10))
  glass = material("101 blue green glass", (0.045, 0.29, 0.32), 0.55, 0.26)
  trim = material("101 silver mullions", (0.55, 0.73, 0.68), 0.65, 0.35)
  concrete = material("City limestone", (0.62, 0.65, 0.60))
  windows = material("City windows", (0.09, 0.22, 0.25), 0.35)
  bark = material("Tree trunks", (0.20, 0.12, 0.055))
  leaves = [material("Foliage " + str(index), color) for index, color in enumerate(
    [(0.055, 0.21, 0.055), (0.13, 0.32, 0.07), (0.26, 0.42, 0.09), (0.64, 0.23, 0.38)])]
  flag_material = material("Golf flags", (0.87, 0.12, 0.08))

  def mesh_object(name, vertices, faces, surface):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    result = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(result)
    result.data.materials.append(surface)
    return result

  def box(name, location, dimensions, surface):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    result = bpy.context.object
    result.name = name
    result.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    result.data.materials.append(surface)
    return result

  def oval(name, x, y, z, radius_x, radius_y, height, surface, angle=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=(x, y, z))
    result = bpy.context.object
    result.name = name
    result.scale = (radius_x, radius_y, height)
    result.rotation_euler.z = angle
    result.data.materials.append(surface)
    for polygon in result.data.polygons:
      polygon.use_smooth = True
    return result

  def cylinder(name, x, y, z, radius, depth, surface):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=depth, location=(x, y, z))
    result = bpy.context.object
    result.name = name
    result.data.materials.append(surface)
    return result

  def ring(name, radius_x, radius_y, width, z, surface):
    vertices = []
    for step in range(129):
      angle = step * math.tau / 128
      for offset in (-width / 2, width / 2):
        vertices.append(((radius_x + offset) * math.cos(angle),
                 (radius_y + offset) * math.sin(angle), z))
    return mesh_object(name, vertices, [(step * 2, step * 2 + 1, step * 2 + 3, step * 2 + 2)
                       for step in range(128)], surface)

  oval("Solid landscape island", 0, 0, -0.45, 10.8, 9.0, 0.7, dark)
  oval("Rolling meadow", 0, 0, -0.16, 10.7, 8.9, 0.45, grass)
  ring("Outer cart path", 9.8, 7.9, 0.19, 0.34, stone)
  ring("Inner promenade", 4.5, 3.7, 0.28, 0.35, stone)
  ring("Central boulevard", 2.9, 2.6, 0.35, 0.37, stone)

  for hole in range(18):
    angle = math.tau * hole / 18
    center_x, center_y = 7.4 * math.cos(angle), 6.05 * math.sin(angle)
    rotation = angle + math.pi / 2
    oval(f"Hole {hole + 1:02d} fairway", center_x, center_y, 0.30, 1.18, 0.61, 0.19, fairway, rotation)
    for lane in (-0.55, 0, 0.55):
      oval("Mowing stripe", center_x + lane * math.cos(rotation),
         center_y + lane * math.sin(rotation), 0.43, 0.19, 0.47, 0.055, stripe, rotation)
    green_x = center_x + 0.70 * math.cos(rotation)
    green_y = center_y + 0.70 * math.sin(rotation)
    oval(f"Hole {hole + 1:02d} green", green_x, green_y, 0.47, 0.40, 0.32, 0.06, green)
    oval("Sand bunker", center_x - 0.55 * math.cos(rotation) + 0.25,
       center_y - 0.55 * math.sin(rotation) + 0.30, 0.43, 0.29, 0.20, 0.05, sand, rotation)
    cylinder("Flagpole", green_x, green_y, 0.83, 0.012, 0.64, trim)
    mesh_object("Red golf flag", [(green_x, green_y, 1.13), (green_x + 0.24, green_y, 1.06),
                                     (green_x, green_y, 0.98)], [(0, 1, 2)], flag_material)
    lake_angle = angle + math.pi / 18
    oval("Lake shoreline", 5.85 * math.cos(lake_angle), 4.85 * math.sin(lake_angle),
       0.30, 0.94, 0.57, 0.10, sand, rotation)
    oval("Lake", 5.85 * math.cos(lake_angle), 4.85 * math.sin(lake_angle),
       0.36, 0.87, 0.50, 0.045, water, rotation)
    bridge = box("Footbridge", (5.85 * math.cos(lake_angle), 4.85 * math.sin(lake_angle), 0.49),
           (0.17, 1.2, 0.09), stone)
    bridge.rotation_euler.z = angle

  box("101 plaza", (0, 0, 0.39), (3.4, 3.0, 0.18), stone)
  box("101 shopping podium", (0, 0, 0.65), (2.5, 2.15, 0.5), concrete)
  box("101 entrance", (0, -1.12, 0.77), (1.25, 0.2, 0.55), glass)
  box("101 tapered base", (0, 0, 1.24), (1.25, 1.25, 0.9), glass)
  for tier in range(8):
    bottom_z = 1.67 + tier * 0.71
    bottom_width = 1.02 - tier * 0.025
    top_width = bottom_width + 0.25
    vertices = [(sign_x * width / 2, sign_y * width / 2, height)
          for width, height in ((bottom_width, bottom_z), (top_width, bottom_z + 0.66))
          for sign_x, sign_y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    mesh_object(f"101 tier {tier + 1} four facades", vertices,
          [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], glass)
    box("101 projecting cornice", (0, 0, bottom_z + 0.66), (top_width + 0.08, top_width + 0.08, 0.055), trim)
    for floor in range(1, 8):
      fraction = floor / 8
      facade_width = bottom_width + 0.25 * fraction
      box("101 floor band", (0, 0, bottom_z + fraction * 0.66), (facade_width + 0.012, facade_width + 0.012, 0.014), trim)
    for side in range(4):
      for column in range(-4, 5):
        bottom_point = (column * bottom_width / 10, -bottom_width / 2 - 0.008, bottom_z)
        top_point = (column * top_width / 10, -top_width / 2 - 0.008, bottom_z + 0.66)
        side_angle = side * math.pi / 2
        def rotate(point):
          return (point[0] * math.cos(side_angle) - point[1] * math.sin(side_angle),
              point[0] * math.sin(side_angle) + point[1] * math.cos(side_angle), point[2])
        lower, upper = rotate(bottom_point), rotate(top_point)
        mesh_object("101 vertical mullion", [lower, upper,
              (upper[0] + 0.009, upper[1] + 0.009, upper[2]),
                            (lower[0] + 0.009, lower[1] + 0.009, lower[2])], [(0, 1, 2, 3)], trim)
  box("101 crown", (0, 0, 7.60), (0.55, 0.55, 0.8), glass)
  box("101 lantern", (0, 0, 8.13), (0.32, 0.32, 0.32), trim)
  cylinder("101 spire", 0, 0, 8.76, 0.033, 1.0, trim)

  for building in range(16):
    angle = building * math.tau / 16
    center_x, center_y = 3.5 * math.cos(angle), 2.8 * math.sin(angle)
    height = random.uniform(0.65, 2.05)
    box("District building", (center_x, center_y, 0.36 + height / 2), (0.62, 0.65, height), concrete)
    box("Rooftop", (center_x, center_y, 0.38 + height), (0.52, 0.55, 0.06), stone)
    for floor in range(int(height / 0.15)):
      box("District glazing", (center_x, center_y, 0.45 + floor * 0.15), (0.63, 0.66, 0.065), windows)

  for tree_index in range(340):
    angle = random.uniform(0, math.tau)
    radius = random.choice((random.uniform(9.4, 10.4), random.uniform(4.4, 4.8)))
    center_x, center_y = radius * math.cos(angle), radius * 0.81 * math.sin(angle)
    height = random.uniform(0.32, 0.68)
    cylinder("Tree trunk", center_x, center_y, 0.42 + height / 3, 0.035, height, bark)
    oval("Tree canopy", center_x, center_y, 0.50 + height, height * 0.42,
       height * 0.42, height * 0.6, random.choices(leaves, weights=(4, 5, 3, 1))[0])

  objects = list(bpy.context.scene.objects)
  assert len([item for item in objects if item.name.startswith("Hole ") and "green" in item.name]) == 18
  assert len([item for item in objects if "four facades" in item.name]) == 8
  assert bpy.data.objects["101 spire"].location.z > 8
  print(f"Verified full 3D geometry: {len(objects)} objects, 18 greens, 8 tower tiers, spire above 8 units")
  bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(glb_path)[0] + ".blend")
  for surface in bpy.data.materials:
    group = [item for item in bpy.context.scene.objects if item.type == "MESH" and item.data.materials and item.data.materials[0] == surface]
    if not group:
      continue
    bpy.ops.object.select_all(action="DESELECT")
    for item in group:
      item.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    if len(group) > 1:
      bpy.ops.object.join()
    bpy.context.object.data.validate()
    bpy.context.object.name = surface.name
  bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", export_extras=True)


HTML_TEMPLATE = r'''<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#e8f0e9">
  <title>Taipei 101 | 3D Golf Landscape</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap" rel="stylesheet">
  <style>
    :root { color-scheme: light; --ink: #123d36; --muted: #52716a; --paper: #e8f0e9; --line: rgba(18,61,54,.18); }
    * { box-sizing: border-box; }
    html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; }
    body { color: var(--ink); background: radial-gradient(ellipse at 50% 46%, #f8f7ed 0%, #e8f0e9 48%, #cbded7 100%); font-family: "DM Sans", sans-serif; }
    #stage { position: fixed; inset: 0; }
    canvas { display: block; width: 100%; height: 100%; touch-action: none; }
    .masthead { position: absolute; z-index: 2; top: clamp(22px,4vw,52px); left: clamp(22px,5vw,72px); pointer-events: none; animation: arrive .8s both; }
    .eyebrow { margin: 0 0 8px; color: #4a776d; font-size: 10px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
    h1 { margin: 0; font: 400 36px/1.05 "DM Serif Display", Georgia, serif; letter-spacing: 0; }
    .subtitle { margin: 12px 0 0; color: var(--muted); font-size: 13px; }
    .badge { position: absolute; z-index: 2; top: clamp(26px,4vw,55px); right: clamp(22px,5vw,72px); padding: 9px 13px; border: 1px solid var(--line); border-radius: 2px; background: rgba(248,249,241,.62); color: var(--ink); font-size: 10px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; backdrop-filter: blur(8px); }
    .controls { position: absolute; z-index: 2; right: clamp(20px,4vw,56px); bottom: clamp(22px,4vw,52px); display: flex; gap: 8px; animation: arrive .8s .15s both; }
    button { min-height: 42px; padding: 0 15px; border: 1px solid var(--line); border-radius: 2px; background: rgba(248,249,241,.83); color: var(--ink); font: 600 12px "DM Sans",sans-serif; cursor: pointer; backdrop-filter: blur(8px); transition: background .18s, transform .18s; }
    button:hover { background: #fff; transform: translateY(-1px); }
    button[aria-pressed="true"] { background: var(--ink); color: white; }
    .views { position: absolute; z-index: 2; left: 50%; bottom: 38px; transform: translateX(-50%); display: flex; gap: 1px; border: 1px solid var(--line); border-radius: 4px; overflow: hidden; }
    .views button { border: 0; border-radius: 0; min-width: 62px; }
    .controls button { width: 42px; height: 42px; padding: 10px; display: grid; place-items: center; }
    button svg { width: 19px; height: 19px; }
    .caption { position: absolute; z-index: 2; left: clamp(22px,5vw,72px); bottom: clamp(28px,4vw,56px); color: var(--muted); font-size: 11px; letter-spacing: .03em; pointer-events: none; }
    #loading { position: absolute; inset: 0; display: grid; place-items: center; z-index: 3; background: var(--paper); color: var(--ink); font-size: 12px; letter-spacing: .12em; text-transform: uppercase; transition: opacity .45s; }
    #loading.done { opacity: 0; pointer-events: none; }
    @keyframes arrive { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 600px) { h1 { font-size: 28px; } .masthead { top: 24px; } .badge { display: none; } .caption { bottom: 116px; max-width: 55%; line-height: 1.5; font-size: 10px; } .views { bottom: 22px; left: 20px; transform: none; } .views button { min-width: 52px; } .controls { right: 18px; bottom: 22px; flex-direction: column; } button { min-height: 40px; padding: 0 11px; } }
  </style>
  <script type="importmap">
    {"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/"}}
  </script>
</head>
<body>
  <main id="stage" aria-label="Taipei 101 and golf course three dimensional scene">
    <div id="loading">Preparing the course</div>
    <header class="masthead"><p class="eyebrow">Taipei, Taiwan</p><h1>Taipei 101<br>Golf Course</h1></header>
    <div class="badge">18 holes · Taipei 101</div>
    <p class="caption">圖像參考重建 · 概念場景，非實測模型</p>
    <nav class="views" aria-label="場景視角"><button data-view="overview" aria-pressed="true">全景</button><button data-view="tower" aria-pressed="false">101</button><button data-view="course" aria-pressed="false">球場</button><button data-view="top" aria-pressed="false">俯視</button></nav>
    <nav class="controls" aria-label="場景控制"><button id="orbit" type="button" title="自動環繞" aria-label="自動環繞" aria-pressed="false"><i data-lucide="orbit"></i></button><button id="reset" type="button" title="重置視角" aria-label="重置視角"><i data-lucide="rotate-ccw"></i></button><button id="fullscreen" type="button" title="全螢幕" aria-label="全螢幕"><i data-lucide="expand"></i></button></nav>
  </main>
  <script type="module">
    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
    import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
    import { createIcons, Orbit, RotateCcw, Expand } from 'https://esm.sh/lucide@0.468.0';
    createIcons({ icons: { Orbit, RotateCcw, Expand } });
    const stage = document.querySelector('#stage');
    const loading = document.querySelector('#loading');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#e8f0e9');
    const camera = new THREE.PerspectiveCamera(34, innerWidth / innerHeight, 0.1, 100);
    camera.position.set(5.2, 3.8, 6.1);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(innerWidth, innerHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.95;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    stage.prepend(renderer.domElement);
    scene.add(new THREE.HemisphereLight('#fff8e9', '#54766a', 2.25));
    const keyLight = new THREE.DirectionalLight('#fff4d8', 3.1);
    keyLight.position.set(-3.5, 6, 4.5);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.camera.left = -4;
    keyLight.shadow.camera.right = 4;
    keyLight.shadow.camera.top = 4;
    keyLight.shadow.camera.bottom = -4;
    keyLight.shadow.normalBias = 0.035;
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight('#d4edff', 1.1);
    fillLight.position.set(4, 3, -4);
    scene.add(fillLight);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: '#e8f0e9', roughness: 1 }));
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.16;
    ground.receiveShadow = true;
    scene.add(ground);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 0.45;
    controls.maxDistance = 24;
    controls.maxPolarAngle = Math.PI * 0.495;
    controls.autoRotateSpeed = 0.8;
    const views = {
      overview: { position: [5.2, 3.8, 6.1], target: [0, -0.3, 0] },
      tower: { position: [2.4, 1.3, 3.3], target: [0, 0.15, 0] },
      course: { position: [3.7, 0.9, 4.5], target: [0, -0.8, 0] },
      top: { position: [0, 8, 0.01], target: [0, -0.8, 0] }
    };
    let activeView = 'overview';
    let reliefModel = null;
    function fitCamera() {
      const preset = views[activeView];
      const aspect = innerWidth / innerHeight;
      camera.fov = 40;
      controls.target.fromArray(preset.target);
      const offset = new THREE.Vector3().fromArray(preset.position).sub(controls.target);
      offset.multiplyScalar(Math.max(1, 0.90 / aspect));
      camera.position.copy(controls.target).add(offset);
      camera.updateProjectionMatrix();
      controls.update();
    }
    fitCamera();
    const modelData = '__MODEL_DATA__';
    const binary = Uint8Array.from(atob(modelData), character => character.charCodeAt(0)).buffer;
    new GLTFLoader().parse(binary, '', ({ scene: model }) => {
      model.traverse(object => { if (object.isMesh) { object.castShadow = true; object.receiveShadow = true; } });
      scene.add(model);
      model.scale.setScalar(0.24);
      const bounds = new THREE.Box3().setFromObject(model);
      const center = bounds.getCenter(new THREE.Vector3());
      model.position.sub(center);
      reliefModel = model;
      fitCamera();
      ground.position.y = bounds.min.y - center.y - 0.012;
      controls.update();
      window.__golfScene = { scene, camera, controls, renderer, model, views };
      document.body.dataset.ready = 'true';
      loading.classList.add('done');
      setTimeout(() => loading.remove(), 500);
    }, error => { loading.textContent = 'Could not load the 3D model'; console.error(error); });
    document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
      activeView = button.dataset.view;
      document.querySelectorAll('[data-view]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      fitCamera();
    }));
    document.querySelector('#orbit').addEventListener('click', event => {
      controls.autoRotate = !controls.autoRotate;
      event.currentTarget.setAttribute('aria-pressed', String(controls.autoRotate));
    });
    document.querySelector('#reset').addEventListener('click', () => {
      controls.autoRotate = false;
      document.querySelector('#orbit').setAttribute('aria-pressed', 'false');
      document.querySelector('[data-view="overview"]').click();
    });
    document.querySelector('#fullscreen').addEventListener('click', async () => {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    });
    addEventListener('resize', () => { fitCamera(); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); });
    renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
  </script>
</body>
</html>'''


def main():
    separator = sys.argv.index("--")
    image_path, html_path = [os.path.abspath(path) for path in sys.argv[separator + 1 :]]
    glb_path = os.path.splitext(html_path)[0] + ".glb"
    build_relief(image_path, glb_path)
    with open(glb_path, "rb") as model_file:
      encoded_model = base64.b64encode(model_file.read()).decode("ascii")
    output = HTML_TEMPLATE.replace("__MODEL_DATA__", encoded_model)
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(output)
    print(f"Created {html_path} ({os.path.getsize(html_path):,} bytes)")


if __name__ == "__main__":
    main()