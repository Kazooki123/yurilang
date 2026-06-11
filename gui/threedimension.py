# YuriLang 3D Renderer w/ PyOpenGL
# Basic 3D on top of existing pygame windows 

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from pygame.locals import DOUBLEBUF, OPENGL
    import pygame
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    


class GL3DError(Exception):
    pass
    

class YuriGL3D:
    def __init__(self):
        if not OPENGL_AVAILABLE:
            raise GL3DError(
                "\n💔 @stage3 - PyOpenGL not installed!!\n"
                " | She tried  to see in 3D but couldn't.\n"
                " |> Hint: pip install pyopengl pyopengl_accelerate\n"
                "         uv pip install pyopengl pyopengl_accelerate --system (uv)"
            )
        self.initialized = False
        self.fov         = 45.0
        self.near        = 0.1
        self.far         = 100.0
        self.rot_x       = 0.0
        self.rot_y       = 0.0
        
    def setup(self, width=800, height=600, title="Yuri3D"):
        pygame.init()
        pygame.display.set_mode(
            (width, height),
            DOUBLEBUF | OPENGL
        )
        pygame.display.set_caption(title)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(
            self.fov,
            width / height,
            self.near,
            self.far
        )
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 5, 5, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
        
        self.initialized = True
        
    def clear(self, r=0.1, g=0.1, b=0.2):
        glClearColor(r, g, b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
    def camera(self, ex, ey, ez, tx=0, ty=0, tz=0):
        gluLookAt(
            float(ex), float(ey), float(ez),
            float(tx), float(ty), float(tz),
            0, 1, 0
        )
        
    def color3d(self, r, g, b):
        glColor3f(r/255, g/255, b/255)
        
    # - Shapes!! -
    def cube(self, x, y, z, size=1.0):
        s = float(size) / 2
        x, y, z = float(x), float(y), float(z)
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        glBegin(GL_QUADS)
        # f(ront)
        glNormal3f(0, 0, 1)
        glVertex3f(-s, -s, s); glVertex3f(s, -s, s)
        glVertex3f(s, s, s); glVertex3f(-s, s, s)
        # b(ack)
        glNormal3f(0, 0, -1)
        glVertex3f(-s, -s, -s); glVertex3f(-s, s, -s)
        glVertex3f(s, s, -s); glVertex3f(s, -s, -s)
        # t(op)
        glNormal3f(0, 1, 0)
        glVertex3f(-s, s, -s); glVertex3f(-s, s, s)
        glVertex3f(s, s, s); glVertex3f(s, s, -s)
        # bo(ttom)
        glNormal3f(0, -1, 0)
        glVertex3f(-s, -s, -s); glVertex3f(s, -s, -s)
        glVertex3f(s, -s, s); glVertex3f(-s, -s, s)
        # r(ight)
        glNormal3f(1, 0, 0)
        glVertex3f(s, -s, -s); glVertex3f(s, s, -s)
        glVertex3f(s, s, s); glVertex3f(s, -s, s)
        # l(eft)
        glNormal3f(-1, 0, 0)
        glVertex3f(-s, -s, -s); glVertex3f(-s, -s, s)
        glVertex3f(-s, s, s); glVertex3f(-s, s, -s)
        
        glEnd()
        glPopMatrix()
        
    def sphere(self, x, y, z, radius=1.0, slices=16, stacks=16):
        glPushMatrix()
        glTranslatef(float(x), float(y), float(z))
        quad = gluNewQuadric()
        gluSphere(quad, float(radius), slices, stacks)
        gluDeleteQuadric(quad)
        glPopMatrix()
        
    def plane(self, x, y, z, w=2.0, h=2.0):
        hw, hh = float(w)/2, float(h)/2
        x, y, z = float(x), float(y), float(z)
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-hw, 0, -hh)
        glVertex3f(hw, 0, -hh)
        glVertex3f(hw, 0, hh)
        glVertex3f(-hw, 0, hh)
        glEnd()
        glPopMatrix()
        
    def rotate3d(self, angle, ax, ay, az):
        glRotatef(float(angle), float(ax), float(ay), float(ax))
        
    def flip(self):
        pygame.display.flip()
        
    def is_running(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    
_gl3d_instance = None

    
def get_gl3d():
    global _gl3d_instance
    if _gl3d_instance is None:
        _gl3d_instance = YuriGL3D()
    return _gl3d_instance
