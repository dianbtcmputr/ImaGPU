from re import fullmatch
from langlib import LP

gl_types = {
    'void', 'bool', 'int', 'uint', 'float', 'double',
    'vec2', 'vec3', 'vec4', 'dvec2', 'dvec3', 'dvec4',
    'bvec2', 'bvec3', 'bvec4', 'ivec2', 'ivec3', 'ivec4',
    'uvec2', 'uvec3', 'uvec4',
    'mat2', 'mat3', 'mat4', 'mat2x2', 'mat2x3', 'mat2x4',
    'mat3x2', 'mat3x3', 'mat3x4', 'mat4x2', 'mat4x3', 'mat4x4',
    'dmat2', 'dmat3', 'dmat4', 'dmat2x2', 'dmat2x3', 'dmat2x4',
    'dmat3x2', 'dmat3x3', 'dmat3x4', 'dmat4x2', 'dmat4x3', 'dmat4x4',
}

gl_images = {
    'sampler1D', 'sampler2D', 'sampler3D', 'samplerCube',
    'sampler1DShadow', 'sampler2DShadow', 'samplerCubeShadow',
    'sampler1DArray', 'sampler2DArray', 'sampler1DArrayShadow', 'sampler2DArrayShadow',
    'samplerBuffer', 'sampler2DRect', 'sampler2DRectShadow',
    'isampler1D', 'isampler2D', 'isampler3D', 'isamplerCube',
    'isampler1DArray', 'isampler2DArray', 'isamplerBuffer', 'isampler2DRect',
    'usampler1D', 'usampler2D', 'usampler3D', 'usamplerCube',
    'usampler1DArray', 'usampler2DArray', 'usamplerBuffer', 'usampler2DRect',
    'image1D', 'image2D', 'image3D', 'imageCube',
    'iimage1D', 'iimage2D', 'iimage3D', 'iimageCube',
    'uimage1D', 'uimage2D', 'uimage3D', 'uimageCube',
    'image1DArray', 'image2DArray', 'imageCubeArray',
    'iimage1DArray', 'iimage2DArray', 'iimageCubeArray',
    'uimage1DArray', 'uimage2DArray', 'uimageCubeArray',
    'imageBuffer', 'iimageBuffer', 'uimageBuffer',
    'image2DRect', 'iimage2DRect', 'uimage2DRect',
    'atomic_uint',
}

gl_qualifiers = {
    'const', 'in', 'out', 'inout', 'uniform', 'attribute', 'varying',
    'centroid', 'flat', 'smooth', 'noperspective', 'patch',
    'sample', 'coherent', 'volatile', 'restrict', 'readonly', 'writeonly',
    'buffer', 'shared',
}

gl_flow = {
    'break', 'continue', 'do', 'for', 'while', 'switch', 'case', 'default',
    'if', 'else', 'discard', 'return',
}

gl_reserved = {
    'class', 'union', 'enum', 'typedef', 'template', 'this', 'inline',
    'mutable', 'friend', 'virtual', 'explicit', 'export', 'noinline',
    'public', 'private', 'protected', 'sizeof', 'alignof', 'offsetof',
    'typeid', 'typename', 'using', 'namespace',
}

gl_builtins = {
    'radians', 'degrees', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
    'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh','pow', 'exp', 'log',
    'exp2', 'log2', 'sqrt', 'inversesqrt', 'abs', 'sign', 'floor', 'ceil',
    'fract', 'mod', 'modf', 'min', 'max', 'clamp', 'mix', 'step',
    'smoothstep', 'isnan', 'isinf', 'floatBitsToInt', 'floatBitsToUint',
    'intBitsToFloat', 'uintBitsToFloat', 'length', 'distance', 'dot',
    'cross', 'normalize', 'faceforward', 'reflect', 'refract',
    'matrixCompMult', 'outerProduct', 'transpose', 'determinant',
    'inverse', 'lessThan', 'lessThanEqual', 'greaterThan',
    'greaterThanEqual', 'equal', 'notEqual', 'any', 'all', 'not',
    'textureSize', 'texture', 'textureProj', 'textureLod',
    'textureOffset', 'texelFetch', 'textureGrad', 'textureGather',
    'textureProjOffset', 'textureLodOffset', 'textureProjLod',
    'textureProjGrad', 'textureGradOffset', 'imageLoad',
    'imageStore', 'imageSize', 'atomicAdd', 'atomicMin', 'atomicMax',
    'atomicAnd', 'atomicOr', 'atomicXor', 'atomicExchange', 'atomicCompSwap',
    'memoryBarrier', 'memoryBarrierAtomicCounter', 'memoryBarrierBuffer',
    'memoryBarrierShared', 'memoryBarrierImage', 'groupMemoryBarrier', 'barrier'
}

imagpu_reserv ={
    '_buf', '_size', '_Params', '_inimg', '_outimg', '_refimg', '_placeholder_'
}

imgpu_func = {
    'igGetPix', 'igRefPix',
}

imgpu_vars = {
    'ig_Position', 'ig_PixColor', 'ig_Params', 'ig_InSize',
    'ig_OutSize',
}

def glsl_name_check(name: str):
    if not fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
        return LP("glslname.charset")
    elif name.startswith('gl_') or name.startswith('ig'):
        return LP("glslname.startwith")
    elif '__' in name:
        return LP("glslname.underline")
    else:
        for setname, vset in {LP("glslname.names.gl_types"): gl_types,
                              LP("glslname.names.gl_images"): gl_images,
                              LP("glslname.names.gl_qualifiers"): gl_qualifiers,
                              LP("glslname.names.gl_flow"): gl_flow,
                              LP("glslname.names.gl_reserved"): gl_reserved,
                              LP("glslname.names.gl_builtins"): gl_builtins,
                              LP("glslname.names.imgpu_kw"): imagpu_reserv}.items():
            if name in vset:
                return LP("glslname.duplicate", name=setname)
    return True

SIZER_TEMPLATE = """#version 430
layout(local_size_x = 1) in;
layout(binding = 0) buffer _buf {int _size[];};

#PARAM_STRUCT#
uniform _Params ig_Params;

uniform ivec2 ig_InSize;

void main(){
    ivec2 ig_OutSize;
    ###
    _size[0] = ig_OutSize.x;
    _size[1] = ig_OutSize.y;
}"""

PIXER_TEMPLATE = """#version 430
layout (local_size_x = 1) in;
layout (binding = 0, rgba8) uniform image2D _inimg;
layout (binding = 1, rgba8) uniform image2D _outimg;
layout (binding = 2, rgba8) uniform image2D _refimg;

#PARAM_STRUCT#
uniform _Params ig_Params;

const ivec2 ig_InSize = ivec2(imageSize(_inimg));
const ivec2 ig_OutSize = ivec2(imageSize(_outimg));

vec4 igGetPix(ivec2 xy){
    #SRC_BOUNDARY_IMPL#
}

vec4 igRefPix(ivec2 xy){
    #REF_BOUNDARY_IMPL#
}

void main(){
    const ivec2 ig_Position = ivec2(gl_GlobalInvocationID.xy);
    vec4 ig_PixColor;
    ###
    imageStore(_outimg, ig_Position, ig_PixColor);
}"""

# ---------- 预览着色器（固定）----------
PREVIEW_VERT_SOURCE = """#version 430
uniform vec2 winSize;
uniform vec2 imgSize;
uniform float scale;
uniform vec2 pan;
const vec2 positions[5] = vec2[5](
    vec2(-1.0, -1.0), vec2( 1.0, -1.0), vec2( 1.0,  1.0),
    vec2(-1.0,  1.0), vec2(-1.0, -1.0)
);
const vec2 texCoords[5] = vec2[5](
    vec2(0.0, 0.0), vec2(1.0, 0.0), vec2(1.0, 1.0),
    vec2(0.0, 1.0), vec2(0.0, 0.0)
);
out vec2 vTexCoord;
void main() {
    float winAspect = winSize.x / winSize.y;
    float imgAspect = imgSize.x / imgSize.y;
    vec2 pos = positions[gl_VertexID];
    if (winAspect > imgAspect)
        pos.x *= imgAspect / winAspect;
    else
        pos.y *= winAspect / imgAspect;
    pos *= scale;
    vec2 ndcPan = vec2(pan.x * 2.0 / winSize.x, -pan.y * 2.0 / winSize.y);
    pos += ndcPan;
    gl_Position = vec4(pos, 0.0, 1.0);
    vTexCoord = texCoords[gl_VertexID];
}"""

PREVIEW_FRAG_SOURCE = """#version 430
uniform ivec2 imgSize_i;
layout(binding = 0, rgba8) uniform image2D img;
in vec2 vTexCoord;
out vec4 FragColor;
void main() {
    ivec2 coord = ivec2(vTexCoord * vec2(imgSize_i));
    coord = clamp(coord, ivec2(0), imgSize_i - 1);
    FragColor = imageLoad(img, coord);
}"""