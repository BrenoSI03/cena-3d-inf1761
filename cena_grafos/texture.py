from __future__ import annotations

from . import graphics_math as gm
import numpy as np
import wgpu
from PIL import Image


class Texture:
  """Textura 2D associada a `varname`, com formato configurável. O conteúdo vem
  from one source: `filename` loads an image, `texel` fills a 1x1 solid
  color, otherwise a blank `width` x `height` texture is created. A pure
  resource-holder - no load/unload of its own, see TextureSet."""

  def __init__ (self, device: wgpu.GPUDevice, varname: str,
                filename: str | None, texel: gm.FloatArray | None = None,
                width: int = 1, height: int = 1,
                format: str = "rgba8unorm-srgb") -> None:
    """Cria a textura de cor ou de dados e envia seus texels para a GPU."""
    self.varname = varname
    if filename:
      # sem inverter: a linha 0 da imagem e a linha 0 da textura, ou seja
      # (s,t) = (0,0) e o canto SUPERIOR esquerdo, como manda a convencao da
      # WebGPU. Toda geometria daqui (Disk, Square, Quad, Cube, Sphere)
      # gera t crescendo para baixo, de acordo.
      img = Image.open(filename)
      img = img.convert("RGBA")
      data = np.array(img)
      width, height = img.size
    elif texel is None:
      data = np.zeros((height, width, 4), dtype='uint8')
    elif np.shape(texel) == (3,):
      width, height = 1, 1
      data = np.array([[[texel[0]*255, texel[1]*255, texel[2]*255, 255]]], dtype='uint8')
    elif np.shape(texel) == (4,):
      width, height = 1, 1
      data = np.array([[[texel[0]*255, texel[1]*255, texel[2]*255, texel[3]*255]]], dtype='uint8')
    else:
      raise RuntimeError("Invalid Texture parameters")
    self.width: int = width
    self.height: int = height

    self.tex: wgpu.GPUTexture = device.create_texture(
      size=(width, height, 1), format=format,
      usage=wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.COPY_DST,
    )
    device.queue.write_texture(
      {"texture": self.tex}, data.tobytes(),
      {"bytes_per_row": width * 4, "rows_per_image": height}, (width, height, 1),
    )
    self.view: wgpu.GPUTextureView = self.tex.create_view()

  def get_texture (self) -> wgpu.GPUTexture:
    return self.tex

  def get_width (self) -> int:
    return self.width

  def get_height (self) -> int:
    return self.height

  @property
  def resource (self) -> wgpu.GPUTextureView:
    """The GPU resource TextureSet/Shader.add_texture_set binds - this
    texture's view."""
    return self.view

