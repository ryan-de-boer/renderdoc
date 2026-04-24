/******************************************************************************
 * The MIT License (MIT)
 *
 * Copyright (c) 2015-2026 Baldur Karlsson
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 ******************************************************************************/

#define MESH_UBO

#include "glsl_ubos.h"

// this allows overrides from outside on GL where we use name-interface matching. On vulkan we can
// default to whatever name we like

#ifndef SECONDARY_NAME
#define SECONDARY_NAME fragin_secondary
#endif

#ifndef NORM_NAME
#define NORM_NAME fragin_norm
#endif

IO_LOCATION(0) in vec4 SECONDARY_NAME;
IO_LOCATION(1) in vec4 NORM_NAME;
IO_LOCATION(2) in vec2 gsout_uv_binding;

IO_LOCATION(0) out vec4 color_out;

layout(set = 0, binding = 2) uniform sampler2D meshTexture;

void main(void)
{
  int type = Mesh.displayFormat;

  if(type == MESHDISPLAY_SECONDARY || type == MESHDISPLAY_MESHLET)
  {
    color_out = vec4(SECONDARY_NAME.xyz, 1);
  }
  else if(type == MESHDISPLAY_SECONDARY_ALPHA)
  {
    color_out = vec4(SECONDARY_NAME.www, 1);
  }
  else if(type == MESHDISPLAY_FACELIT)
  {
    vec3 lightDir = normalize(vec3(0, -0.3f, -1));

    color_out = vec4(Mesh.color.xyz * abs(dot(lightDir, NORM_NAME.xyz)), 1);
  }
  else if(type == MESHDISPLAY_EXPLODE)
  {
    vec3 lightDir = normalize(vec3(0, -0.3f, -1));

    color_out = vec4(SECONDARY_NAME.xyz * abs(dot(lightDir, NORM_NAME.xyz)), 1);
  }
  else if(type == MESHDISPLAY_TEXTURED)
  {


vec3 lightDir = normalize(vec3(0, -0.3f, -1));
vec2 uv = gsout_uv_binding.xy;
if (Mesh.flipV==1)
{
uv.y = 1.0 - uv.y;    // flip V
}

vec4 texColor = texture(meshTexture, uv);

    // discard fully transparent pixels so they don't affect depth
    if(texColor.w < 0.1)
        discard;

float lighting = abs(dot(lightDir, NORM_NAME.xyz));

//lighting = lighting * 0.7 + 1.5;  // scale down dark areas, add ambient lift quake
//lighting = lighting * 0.7 + 0.0;  // scale down dark areas, add ambient lift crysis needs lower ambient
lighting = lighting * 0.7 + Mesh.ambient;

color_out = vec4(texColor.xyz * lighting, texColor.w);

    // debug: show UVs as RG colour - should show red/green gradient if UVs are correct
//   color_out = vec4(gsout_uv_binding.x, gsout_uv_binding.y, 0.0, 1.0);
// color_out = vec4(1.0, 0.0, 0.0, 1.0);  // solid red

//    vec3 lightDir = normalize(vec3(0, -0.3f, -1));

//    vec2 uv = gsout_uv_binding.xy;
//    vec4 texColor = texture(meshTexture, uv);
//    //brighten
//    texColor = texColor + vec4(0.5,0.5,0.5,0.0)
//    color_out = vec4(texColor.xyz * abs(dot(lightDir, NORM_NAME.xyz)), 1);


//    vec2 uv = gsout_uv_binding.xy;
//    uv.y = 1.0 - uv.y;    // flip V
//    color_out = texture(meshTexture, uv);


//    vec2 uv = SECONDARY_NAME.xy;
//    uv.y = 1.0 - uv.y;    // flip V
//    color_out = texture(meshTexture, uv);
//    color_out = texture(meshTexture, vec2(0.5,0.5));
  }
  else    // if(type == MESHDISPLAY_SOLID)
  {
    color_out = vec4(Mesh.color.xyz, 1);
  }

// In main(), add a case for MESHDISPLAY_TEXTURED:
#if defined(VULKAN)
//  if(ubo.displayFormat == MESHDISPLAY_TEXTURED)
//  {
//    // secondary.xy carries the UVs (same as Secondary mode uses secondary channel)
//    vec2 uv = secondary.xy;
//    fragColor = texture(meshTexture, uv);
//    return;
//  }
#endif

}
