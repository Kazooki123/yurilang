"""
Raylib - Yurilang

Raylib bindings for Yurilang via the `raylib-py` package.
Called from `store/raylib.yuri` ships (functions)
DLL Support soon.
"""

import raylib as rl
import ctypes

# ───────
# Classes
# ───────

class Vector3(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
    ]

class Camera3D(ctypes.Structure):
    _fields_ = [
        ("position",    Vector3),
        ("target",      Vector3),
        ("up",          Vector3),
        ("fovy",        ctypes.c_float),
        ("projection",  ctypes.c_int),
    ]

# ───────
#  Window
# ───────

def rl_overture(width, height, title):
    rl.InitWindow(int(width), int(height), title.encode())
    rl.SetTargetFPS(60)

def rl_finale():
    rl.CloseWindow()

def rl_scene_running():
    return not rl.WindowShouldClose()

def rl_set_fps(fps):
    rl.SetTargetFPS(int(fps))

def rl_tempo():
    return rl.GetFrameTime()

# ────────
#  Drawing
# ────────

def rl_limelight():
    rl.BeginDrawing()

def rl_blackout():
    rl.EndDrawing()

def rl_backdrop(r, g, b):
    rl.ClearBackground((int(r), int(g), int(b), 255))

def rl_caption(text, x, y, size, r, g, b):
    rl.DrawText(str(text).encode(), int(x), int(y), int(size),
                (int(r), int(g), int(b), 255))

def rl_rect(x, y, w, h, r, g, b):
    rl.DrawRectangle(int(x), int(y), int(w), int(h),
                     (int(r), int(g), int(b), 255))

def rl_circle(x, y, radius, r, g, b):
    rl.DrawCircle(int(x), int(y), float(radius),
                  (int(r), int(g), int(b), 255))

def rl_line(x1, y1, x2, y2, r, g, b):
    rl.DrawLine(int(x1), int(y1), int(x2), int(y2),
                (int(r), int(g), int(b), 255))

# ───
# 3D
# ───

def make_vec(x, y, z):
    v = Vector3()
    v.x = float(x)
    v.y = float(y)
    v.z = float(z)
    return v

_camera = None

def rl_lens(ex, ey, ez, tx, ty, tz):
    """Set up a 3D camera."""
    global _camera
    
    camera = Camera3D()
    camera.position = make_vec(ex, ey, ez)
    camera.target   = make_vec(tx, ty, tz)
    camera.up       = make_vec(0.0, 1.0, 0.0)
    camera.fovy     = 45.0
    camera.projection = rl.CAMERA_PERSPECTIVE
    
    _camera = camera

def rl_depth():
    """BeginMode3D — requires @lens called first."""
    if _camera is None:
        raise RuntimeError("@depth — no camera set, call @lens first")
    
    rl.BeginMode3D(_camera)

def rl_surface():
    rl.EndMode3D()

def rl_cube(x, y, z, w, h, d, r, g, b):
    rl.DrawCube(
        make_vec(x, y, z),
        float(w), float(h), float(d),
        (int(r), int(g), int(b), 255)
    )

def rl_cube_wires(x, y, z, w, h, d):
    rl.DrawCubeWires(
        make_vec(x, y, z),
        float(w), float(h), float(d),
        (0, 0, 0, 255)
    )

def rl_sphere(x, y, z, radius, r, g, b):
    rl.DrawSphere(
        make_vec(x, y, z),
        float(radius),
        (int(r), int(g), int(b), 255)
    )

def rl_grid(slices, spacing):
    rl.DrawGrid(int(slices), float(spacing))

# ──────
#  Input
# ──────

_KEY_MAP = {
    "up":     rl.KEY_UP,
    "down":   rl.KEY_DOWN,
    "left":   rl.KEY_LEFT,
    "right":  rl.KEY_RIGHT,
    "space":  rl.KEY_SPACE,
    "escape": rl.KEY_ESCAPE,
    "w":      rl.KEY_W,
    "a":      rl.KEY_A,
    "s":      rl.KEY_S,
    "d":      rl.KEY_D,
    "e":      rl.KEY_E,
    "q":      rl.KEY_Q,
}

def rl_cue(key):
    code = _KEY_MAP.get(str(key).lower(), 0)
    return rl.IsKeyDown(code)

def rl_cue_pressed(key):
    code = _KEY_MAP.get(str(key).lower(), 0)
    return rl.IsKeyPressed(code)

def rl_mouse_x():
    return rl.GetMouseX()

def rl_mouse_y():
    return rl.GetMouseY()

def rl_mouse_pressed(button):
    btn = rl.MOUSE_BUTTON_LEFT if str(button) == "left" else rl.MOUSE_BUTTON_RIGHT
    return rl.IsMouseButtonPressed(btn)

# ──────
#  Audio
# ──────

def rl_sound_init():
    rl.InitAudioDevice()

def rl_sound_close():
    rl.CloseAudioDevice()

def rl_sound_load(path):
    return rl.LoadSound(path.encode())

def rl_sound_play(sound):
    rl.PlaySound(sound)


RAYLIB_OPS = {
    "overture":      rl_overture,
    "finale":        rl_finale,
    "scene_running": rl_scene_running,
    "set_fps":       rl_set_fps,
    "tempo":         rl_tempo,
    "limelight":     rl_limelight,
    "blackout":      rl_blackout,
    "backdrop":      rl_backdrop,
    "caption":       rl_caption,
    "rect":          rl_rect,
    "circle":        rl_circle,
    "line":          rl_line,
    "lens":          rl_lens,
    "depth":         rl_depth,
    "surface":       rl_surface,
    "cube":          rl_cube,
    "cube_wires":    rl_cube_wires,
    "sphere":        rl_sphere,
    "grid":          rl_grid,
    "cue":           rl_cue,
    "cue_pressed":   rl_cue_pressed,
    "mouse_x":       rl_mouse_x,
    "mouse_y":       rl_mouse_y,
    "mouse_pressed": rl_mouse_pressed,
    "sound_init":    rl_sound_init,
    "sound_close":   rl_sound_close,
    "sound_load":    rl_sound_load,
    "sound_play":    rl_sound_play,
}
