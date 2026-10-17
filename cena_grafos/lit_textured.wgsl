struct Matrix {
  vertex: mat4x4<f32>,
  normal: mat4x4<f32>,
}
@group(1) @binding(0) var<storage, read> matrix: array<Matrix>;

struct Global {
  projection: mat4x4<f32>,
  light_ambient: vec3<f32>,
  light_diffuse: vec3<f32>,
  light_specular: vec3<f32>,
  light_position: vec4<f32>,
  camera_position: vec4<f32>,
  light_direction: vec3<f32>,
  spot_cutoff: f32,
  spot_exponent: f32,
  fog_color: vec4<f32>,
  fog_density: f32,
}
@group(0) @binding(0) var<uniform> global: Global;

struct Material {
  base_color: vec3<f32>,
  opacity: f32,
  specular_color: vec3<f32>,
  shininess: f32,
}
@group(2) @binding(0) var<uniform> material: Material;

@group(3) @binding(0) var decal_texture: texture_2d<f32>;
@group(3) @binding(1) var decal_sampler: sampler;
@group(3) @binding(2) var normal_texture: texture_2d<f32>;
@group(3) @binding(3) var normal_sampler: sampler;

struct VertexOutput {
  @builtin(position) clip_position: vec4<f32>,
  @location(0) light: vec3<f32>,
  @location(1) view: vec3<f32>,
  @location(2) spot_direction: vec3<f32>,
  @location(3) texcoord: vec2<f32>,
  @location(4) position_eye: vec3<f32>,
}

@vertex
fn vs_main(
  @builtin(instance_index) instance_index: u32,
  @location(0) coord: vec3<f32>,
  @location(1) normal: vec3<f32>,
  @location(2) tangent: vec3<f32>,
  @location(3) texcoord: vec2<f32>,
) -> VertexOutput {
  let m = matrix[instance_index];
  let position_eye = (m.vertex * vec4<f32>(coord, 1.0)).xyz;

  let normal_eye = normalize((m.normal * vec4<f32>(normal, 0.0)).xyz);
  let tangent_raw = (m.normal * vec4<f32>(tangent, 0.0)).xyz;
  let tangent_eye = normalize(
    tangent_raw - dot(tangent_raw, normal_eye) * normal_eye
  );
  let bitangent_eye = cross(normal_eye, tangent_eye);

  // As linhas desta matriz levam vetores da câmera ao espaço tangente.
  let eye_to_tangent = transpose(
    mat3x3<f32>(tangent_eye, bitangent_eye, normal_eye)
  );
  let light_eye = normalize(global.light_position.xyz - position_eye);
  let view_eye = normalize(-position_eye);
  let spot_direction_eye = normalize(global.light_direction);

  var out: VertexOutput;
  out.light = eye_to_tangent * light_eye;
  out.view = eye_to_tangent * view_eye;
  out.spot_direction = eye_to_tangent * spot_direction_eye;
  out.texcoord = texcoord;
  out.position_eye = position_eye;
  out.clip_position = global.projection * vec4<f32>(position_eye, 1.0);
  return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
  let normal_texel = textureSample(
    normal_texture, normal_sampler, in.texcoord
  );
  let normal = normalize(2.0 * normal_texel.rgb - vec3<f32>(1.0));
  let light = normalize(in.light);
  let view = normalize(in.view);
  let spot_direction = normalize(in.spot_direction);

  let spot_cosine = dot(-light, spot_direction);
  var spot = 0.0;
  if (spot_cosine >= global.spot_cutoff) {
    spot = pow(max(spot_cosine, 0.0), global.spot_exponent);
  }

  let decal = textureSample(decal_texture, decal_sampler, in.texcoord).rgb;
  var matte = material.base_color * decal * global.light_ambient;
  var specular = vec3<f32>(0.0);
  let ndotl = dot(normal, light);
  if (ndotl > 0.0) {
    matte += material.base_color * decal * global.light_diffuse * ndotl;
    let reflected = normalize(reflect(-light, normal));
    let specular_factor = pow(
      max(dot(reflected, view), 0.0), material.shininess
    );
    specular = material.specular_color * global.light_specular * specular_factor;
  }

  let lit_color = spot * (matte + specular);
  let distance = length(in.position_eye);
  let fog_factor = exp(-pow(global.fog_density * distance, 2.0));
  let final_color = mix(global.fog_color.rgb, lit_color, fog_factor);
  return vec4<f32>(final_color, 1.0);
}
