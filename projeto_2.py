"""Projeto 2: cena 3D com spot, decal, normal map, fog e arcball."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import wgpu
from cena_grafos import graphics_math as gm
from cena_grafos.camera3d import Camera3D
from cena_grafos.cube import Cube
from cena_grafos.node import Node
from cena_grafos.phongmaterial import PhongMaterial
from cena_grafos.pipeline import Pipeline
from cena_grafos.renderer import Renderer
from cena_grafos.sampler import Sampler
from cena_grafos.scene import Scene
from cena_grafos.shader import Shader
from cena_grafos.sphere import Sphere
from cena_grafos.spotlight import SpotLight
from cena_grafos.texture import Texture
from cena_grafos.textureset import TextureSet
from cena_grafos.transform import Transform
from rendercanvas.glfw import RenderCanvas, loop

PROJECT_DIR = Path(__file__).resolve().parent
SCENE_GRAPH_DIR = PROJECT_DIR / "cena_grafos"
IMAGE_DIR = PROJECT_DIR / "imagens"
SHADER_PATH = SCENE_GRAPH_DIR / "lit_textured.wgsl"

BACKGROUND_COLOR = (0.08022, 0.09990, 0.14126, 1.0)  # #505969 em sRGB
FOG_COLOR = (0.37626, 0.41789, 0.47353, 1.0)  # #A5ADB7 em sRGB
FOG_DENSITY = 0.045

canvas: RenderCanvas
context: Any
device: wgpu.GPUDevice
renderer: Renderer
camera: Camera3D
scene: Scene


def create_transform(
    x: float,
    y: float,
    z: float,
    scale_x: float,
    scale_y: float,
    scale_z: float,
) -> Transform:
    """Cria uma transformação que primeiro escala e depois translada."""
    transform = Transform()
    transform.translate(x, y, z)
    transform.scale(scale_x, scale_y, scale_z)
    return transform


def create_texture_sets(
    device: wgpu.GPUDevice,
    shader: Shader,
) -> tuple[TextureSet, TextureSet, TextureSet, TextureSet]:
    """Cria no setup os conjuntos neutro, de decal e de rugosidade."""
    decal_sampler = Sampler(device, "decal_sampler")
    normal_sampler = Sampler(device, "normal_sampler")

    # Texturas neutras usadas nos objetos sem decal ou relevo.
    white_decal = Texture(
        device,
        "decal_texture",
        None,
        texel=gm.vec4(1.0, 1.0, 1.0, 1.0),
    )
    neutral_normal = Texture(
        device,
        "normal_texture",
        None,
        texel=gm.vec4(0.5, 0.5, 1.0, 1.0),
        format="rgba8unorm",
    )
    wood_decal = Texture(
        device,
        "decal_texture",
        str(IMAGE_DIR / "wood_texture.jpg"),
    )
    stopwatch_decal = Texture(
        device,
        "decal_texture",
        str(IMAGE_DIR / "stopwatch.jpg"),
    )
    golf_normal = Texture(
        device,
        "normal_texture",
        str(IMAGE_DIR / "golfball.png"),
        format="rgba8unorm",
    )

    # Combinações usadas na mesa, na caixa e na esfera com relevo.
    plain = TextureSet([
        white_decal,
        decal_sampler,
        neutral_normal,
        normal_sampler,
    ])
    wood = TextureSet([
        wood_decal,
        decal_sampler,
        neutral_normal,
        normal_sampler,
    ])
    stopwatch = TextureSet([
        stopwatch_decal,
        decal_sampler,
        neutral_normal,
        normal_sampler,
    ])
    rough = TextureSet([
        white_decal,
        decal_sampler,
        golf_normal,
        normal_sampler,
    ])

    for texture_set in (plain, wood, stopwatch, rough):
        shader.add_texture_set(texture_set)
    return plain, wood, stopwatch, rough


def create_scene(device: wgpu.GPUDevice, target_format: str) -> Scene:
    """Cria os recursos gráficos e monta a hierarquia da cena."""
    table_width = 6.0
    table_depth = 3.8
    tabletop_thickness = 0.35
    leg_height = 2.8
    leg_thickness = 0.4
    box_width = 1.5
    box_height = 1.1
    box_depth = 1.2
    small_sphere_radius = 0.38
    large_sphere_radius = 0.75

    # Spot posicionado acima da mesa e apontado para os objetos da cena.
    light = SpotLight(
        4.5,
        8.0,
        5.5,
        -4.5,
        -5.0,
        -5.5,
        angle=24.0,
        exponent=6.0,
        space="world",
    )
    light.set_ambient(0.24, 0.24, 0.24)
    light.set_diffuse(0.82, 0.82, 0.82)
    light.set_specular(1.0, 1.0, 1.0)

    # Shader final com iluminação de spot, texturas, relevo e fog.
    shader = Shader(device, str(SHADER_PATH), light=light, space="camera")
    shader.set_value("fog_color", gm.vec4(*FOG_COLOR))
    shader.set_value("fog_density", FOG_DENSITY)
    shader.set_vertex_buffers([
        {
            "array_stride": 3 * 4,
            "step_mode": "vertex",
            "attributes": [
                {"format": "float32x3", "offset": 0, "var_name": "coord"},
            ],
        },
        {
            "array_stride": 3 * 4,
            "step_mode": "vertex",
            "attributes": [
                {"format": "float32x3", "offset": 0, "var_name": "normal"},
            ],
        },
        {
            "array_stride": 3 * 4,
            "step_mode": "vertex",
            "attributes": [
                {"format": "float32x3", "offset": 0, "var_name": "tangent"},
            ],
        },
        {
            "array_stride": 2 * 4,
            "step_mode": "vertex",
            "attributes": [
                {"format": "float32x2", "offset": 0, "var_name": "texcoord"},
            ],
        },
    ])
    pipeline = Pipeline(
        shader,
        target_format,
        primitive={"cull_mode": "back"},
    )

    table_material = PhongMaterial(0.92, 0.86, 0.74)
    table_material.set_shininess(20.0)
    box_material = PhongMaterial(1.0, 1.0, 1.0)
    box_material.set_shininess(18.0)
    small_sphere_material = PhongMaterial(0.18, 0.78, 0.30)
    small_sphere_material.set_shininess(48.0)
    large_sphere_material = PhongMaterial(0.72, 0.80, 0.95)
    large_sphere_material.set_shininess(28.0)

    for material in (
        table_material,
        box_material,
        small_sphere_material,
        large_sphere_material,
    ):
        shader.add_material(material)

    plain_textures, wood_textures, stopwatch_textures, rough_textures = (
        create_texture_sets(device, shader)
    )

    # Geometrias usadas para montar todos os objetos da cena.
    cube = Cube(device)
    sphere = Sphere(device)

    tabletop_height = leg_height
    tabletop_top = tabletop_height + tabletop_thickness
    leg_x = table_width / 2.0 - leg_thickness
    leg_z = table_depth / 2.0 - leg_thickness

    # Tampo da mesa com a textura de madeira.
    tabletop = Node(
        trf=create_transform(
            0.0,
            tabletop_height,
            0.0,
            table_width,
            tabletop_thickness,
            table_depth,
        ),
        apps=[wood_textures],
        shps=[cube],
    )

    # Quatro pés posicionados nos cantos do tampo.
    legs = []
    for x, z in (
        (-leg_x, leg_z),
        (leg_x, leg_z),
        (-leg_x, -leg_z),
        (leg_x, -leg_z),
    ):
        legs.append(Node(
            trf=create_transform(
                x,
                0.0,
                z,
                leg_thickness,
                leg_height,
                leg_thickness,
            ),
            shps=[cube],
        ))

    table = Node(
        apps=[table_material],
        nodes=[tabletop, *legs],
    )

    box_x = -1.15
    box_z = 0.35
    # Caixa sobre a mesa com a textura de cronômetro.
    box = Node(
        trf=create_transform(
            box_x,
            tabletop_top,
            box_z,
            box_width,
            box_height,
            box_depth,
        ),
        apps=[box_material, stopwatch_textures],
        shps=[cube],
    )

    # Esfera verde posicionada sobre a caixa.
    small_sphere = Node(
        trf=create_transform(
            box_x,
            tabletop_top + box_height + small_sphere_radius,
            box_z,
            small_sphere_radius,
            small_sphere_radius,
            small_sphere_radius,
        ),
        apps=[small_sphere_material],
        shps=[sphere],
    )

    # Esfera com textura de bola de golfe e silhueta esférica preservada.
    large_sphere = Node(
        trf=create_transform(
            1.35,
            tabletop_top + large_sphere_radius,
            -0.45,
            large_sphere_radius,
            large_sphere_radius,
            large_sphere_radius,
        ),
        apps=[large_sphere_material, rough_textures],
        shps=[sphere],
    )

    root = Node(
        pipeline=pipeline,
        apps=[plain_textures],
        nodes=[table, box, small_sphere, large_sphere],
    )
    return Scene(root)


def initialize(device: wgpu.GPUDevice, target_format: str) -> None:
    """Configura a câmera, o arcball e a cena."""
    global camera, scene

    camera = Camera3D(9.0, 7.0, 11.0)
    camera.set_center(0.0, 2.1, 0.0)
    camera.set_angle(42.0)
    camera.set_z_planes(0.1, 100.0)

    arcball = camera.create_arcball()
    arcball.attach(canvas)

    scene = create_scene(device, target_format)


def draw() -> None:
    """Renderiza um quadro com a câmera atual."""
    target_texture = context.get_current_texture()
    renderer.render(target_texture, scene, camera)


def main() -> None:
    """Inicializa o WebGPU e entrega o redesenho ao canvas."""
    global canvas, context, device, renderer

    canvas = RenderCanvas(
        size=(900, 700),
        title="Projeto 2 - Cena 3D",
        update_mode="continuous",
        max_fps=60,
    )
    adapter = wgpu.gpu.request_adapter_sync()
    device = adapter.request_device_sync()
    context = canvas.get_context("wgpu")
    target_format = context.get_preferred_format(device.adapter)
    context.configure(device=device, format=target_format)

    renderer = Renderer(
        device,
        depth_test=True,
        clear_value=BACKGROUND_COLOR,
    )
    initialize(device, target_format)

    canvas.request_draw(draw)
    loop.run()


if __name__ == "__main__":
    main()
