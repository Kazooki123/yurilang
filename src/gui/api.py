from src.gui.renderer import YuriRenderer
from src.gui.threedimension import YuriGL3D

_renderer = None
_3drenderer = None

def get_renderer():
    global _renderer
    if _renderer is None:
        _renderer = YuriRenderer()
    return _renderer


def get_3drenderer():
    global _3drenderer
    if _3drenderer is None:
        _3drenderer = YuriGL3D()
    return _3drenderer


def reset_renderer():
    global _renderer, _3drenderer
    if _renderer:
        _renderer.exit_stage()
    _renderer = None
    

def stage(width=800, height=600, title="Yuri3D"):
    r = get_renderer()
    r.setup(width, height, title)
    

def scene_running():
    r = get_renderer()
    return r.is_running()
    
    
def curtain():
    get_renderer().curtain()
  

def actor(shape, *args):
    get_renderer().actor(shape, *args)
    
    
def spotlight(r_val, g, b):
    get_renderer().spotlight(r_val, g, b)


def backdrop(r_val, g, b):
    get_renderer().backdrop(r_val, g, b)
    

def perform():
    return get_renderer().perform()


def exit_stage():
    get_renderer().exit_stage()


def set_fps(fps):
    get_renderer().set_fps(fps)


def get_keys():
    return get_renderer().get_keys()


def get_mouse():
    return get_renderer().get_mouse()


def fps_actual():
    return get_renderer().fps_actual()
