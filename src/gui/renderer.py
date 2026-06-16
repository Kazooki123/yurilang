# Yurilang GUI - Using pygame

try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class RendererError(Exception):
    pass


class YuriRenderer:
    def __init__(self):
        if not PYGAME_AVAILABLE:
            raise RendererError(
                "\n💔 @stage - pygame not installed!\n"
                " | She tried to set the stage but the dependency wasn't there...\n"
                " |> Hint: pip install pygame"
                "          uv pip install pygame (uv)"
            )

        self.screen = None
        self.clock = None
        self.width = 800
        self.height = 600
        self.title = "Yuri3D"
        self.fps = 60
        self.color = (255, 192, 203)
        self.bg_color = (20, 27, 46)
        self.font = None
        self.font_size = 24
        self.running = False
        self.initialized = False

    def setup(self, width=800, height=600, title="Yuri3D"):
        self.width = int(width)
        self.height = int(height)
        self.title = str(title)

        pygame.init()
        pygame.display.set_caption(self.title)

        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", self.font_size)
        self.running = True
        self.initialized = True

        self.screen.fill(self.bg_color)
        pygame.display.flip()

    def spotlight(self, r, g, b):
        self.color = (
            max(0, min(255, int(r))),
            max(0, min(255, int(g))),
            max(0, min(255, int(b))),
        )

    def backdrop(self, r, g, b):
        self.bg_color = (
            max(0, min(255, int(r))),
            max(0, min(255, int(g))),
            max(0, min(255, int(b))),
        )

    def curtain(self):
        self._check_init()
        self.screen.fill(self.bg_color)

    def perform(self):
        self._check_init()
        pygame.display.flip()
        self.clock.tick(self.fps)
        return self._handle_events()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False

        return True

    def is_running(self):
        return self.running

    def exit_stage(self):
        if self.initialized:
            pygame.quit()
            self.initialized = False
            self.running = False

    def actor(self, shape, *args):
        """
        @actor shape ...args -> dragw a shape actor!!

        Shapes:
            circles x y radius
            rect    x y w h
            line    x1 y1 x2 y2
            text    "message" x y
            pixel   x y
            image   "path" x y
        """
        self._check_init()
        shape = str(shape).lower().strip()

        if shape == "circle":
            x, y, r = int(args[0]), int(args[1]), int(args[2])
            pygame.draw.circle(self.screen, self.color, (x, y), r)

        elif shape == "rect":
            x, y, w, h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
            pygame.draw.rect(self.screen, self.color, (x, y, w, h))

        elif shape == "rect_outline":
            x, y, w, h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
            thickness = int(args[4]) if len(args) > 4 else 2
            pygame.draw.rect(self.screen, self.color, (x, y, w, h), thickness)

        elif shape == "line":
            x1, y1 = int(args[0]), int(args[2])
            x2, y2 = int(args[3]), int(args[4])
            thickness = int(args[4]) if len(args) > 4 else 1
            pygame.draw.line(self.screen, self.color, (x1, y1), (x2, y2), thickness)

        elif shape == "text":
            text = str(args[0]).strip('"')
            x, y = int(args[1]), int(args[2])
            size = int(args[3]) if len(args) > 3 else self.font_size
            font = pygame.font.SysFont("monospace", size)
            surface = font.render(text, True, self.color)
            self.screen.blit(surface, (x, y))

        elif shape == "pixel":
            x, y = int(args[0]), int(args[1])
            self.screen.set_at((x, y), self.color)

        elif shape == "image":
            path = str(args[0]).strip('"')
            x, y = int(args[1]), int(args[2])
            try:
                img = pygame.image.load(path)
                self.screen.blit(img, (x, y))
            except Exception as e:
                raise RendererError(
                    f"\n💔 @actor image - Could not load '{path}'!\n   {e}"
                )

        elif shape == "triangle":
            points = [
                (int(args[0]), int(args[1])),
                (int(args[2]), int(args[3])),
                (int(args[4]), int(args[5])),
            ]
            pygame.draw.polygon(self.screen, self.color, points)

        else:
            raise RendererError(
                f"\n💔 @actor - Unknown shape '{shape}'!\n"
                " | Available: circle, rect, rect_outline, line,\n"
                "              text, pixel, image, triangle\n"
            )

    def get_keys(self):
        keys = pygame.key.get_pressed()
        return {
            "up": keys[pygame.K_UP] or keys[pygame.K_w],
            "down": keys[pygame.K_DOWN] or keys[pygame.K_s],
            "left": keys[pygame.K_LEFT] or keys[pygame.K_a],
            "right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            "space": keys[pygame.K_SPACE],
            "enter": keys[pygame.K_RETURN],
            "escape": keys[pygame.K_ESCAPE],
            "shift": keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT],
        }

    def get_mouse(self):
        x, y = pygame.mouse.get_pos()
        buttons = pygame.mouse.get_pressed()
        return x, y, buttons[0], buttons[2]

    def fps_actual(self):
        if self.clock:
            return int(self.clock.get_fps())
        return 0

    def _check_init(self):
        if not self.initialized:
            raise RendererError(
                "\n💔 @actor/@curtain/@perform - Stage has not set up!!\n"
                " | She tried to perform without a stage.\n"
                " |> Hint: Call @stage first:\n"
                '          @stage 800 600 "My Scene"\n'
            )

    def set_fps(self, fps):
        self.fps = int(fps)

    def set_font_size(self, size):
        self.font_size = int(size)
        if self.initialized:
            self.font = pygame.font.SysFont("monospace", self.font_size)
