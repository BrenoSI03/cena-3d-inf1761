from __future__ import annotations

import math
from typing import Any

from . import graphics_math as gm
from .light import Light


class SpotLight(Light):
    """Luz de spot definida por posição, direção, abertura e expoente."""

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        direction_x: float,
        direction_y: float,
        direction_z: float,
        angle: float,
        exponent: float,
        space: str = "world",
        **values: Any,
    ) -> None:
        """Recebe a abertura em graus e guarda seu cosseno para o shader."""
        Light.__init__(self, space, **values)
        self.set_position(x, y, z)
        self.set_direction(direction_x, direction_y, direction_z)
        self.set_angle(angle)
        self.set_exponent(exponent)

    def set_position(self, x: float, y: float, z: float) -> None:
        """Define a posição do spot no espaço escolhido."""
        self.set("light_position", gm.vec4(x, y, z, 1.0))

    def set_direction(self, x: float, y: float, z: float) -> None:
        """Define a direção do eixo central do cone."""
        self.set("light_direction", gm.vec3(x, y, z))

    def set_angle(self, angle: float) -> None:
        """Converte a abertura em graus para o limite de cosseno."""
        self.set("spot_cutoff", math.cos(gm.radians(angle)))

    def set_exponent(self, exponent: float) -> None:
        """Define a concentração da intensidade no eixo do spot."""
        self.set("spot_exponent", exponent)

    def map(self, matrix: gm.Mat4) -> dict[str, Any]:
        """Mapeia a posição como ponto e a direção como vetor unitário."""
        position = matrix @ self.get("light_position")
        direction = self.get("light_direction")
        mapped_direction = (
            matrix @ gm.vec4(direction[0], direction[1], direction[2], 0.0)
        )[:3]
        return {
            "light_position": position,
            "light_direction": gm.normalize(mapped_direction),
        }

