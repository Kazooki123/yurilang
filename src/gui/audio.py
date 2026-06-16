try:
    import pygame as pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AudioError(Exception):
    pass


class YuriAudio:
    def __init__(self):
        if not PYGAME_AVAILABLE:
            raise AudioError(
                "\n💔 @stage - pygame not installed!\n"
                " | She tried to set the stage but the dependency wasn't there...\n"
                " |> Hint: pip install pygame"
                "          uv pip install pygame (uv)"
            )
        pygame.mixer.init(
            frequency=44100,
            size=16,
            channels=2,
            buffer=512,
        )
        self.sounds = {}
        self.music = None
        self.volume = 1.0

    def load_sound(self, label, path):
        try:
            self.sounds[label] = pygame.mixer.Sound(path)
        except Exception as e:
            raise AudioError(f"\n💔 @sound loud - Could not load '{path}'!\n  {e}")

    def play_sound(self, label, loops=0):
        if label not in self.sounds:
            raise AudioError(
                f"\n💔 @sound play - '{label}' not loaded properly!\n"
                f' |> Hint: @sound load {label} "path.wav" first.'
            )
        self.sounds[label].play(loops=loops)

    def stop_sound(self, label):
        if label in self.sounds:
            self.sounds[label].stop()

    def volume_sound(self, label, vol):
        if label in self.sounds:
            self.sounds[label].set_volume(max(0.0, min(1.0, float(vol))))

    def play_music(self, path, loops=-1):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops)
        except Exception as e:
            raise AudioError(
                f"\n💔 @music play - Could not load '{path}'!\n"
                f" | {e}"
                " |> Hint: Use a .ogg or .wav for best compatibility.\n"
            )

    def stop_music(self):
        pygame.mixer.music.stop()

    def pause_music(self):
        pygame.mixer.music.pause()

    def resume_music(self):
        pygame.mixer.music.unpause()

    def volume_music(self, vol):
        pygame.mixer.music.set_volume(max(0.0, min(1.0, float(vol))))

    def is_playing(self):
        return pygame.mixer.music.get_busy()

    def cleanup(self):
        pygame.mixer.quit()


_audio_instance = None


def get_audio():
    global _audio_instance
    if _audio_instance is None:
        _audio_instance = YuriAudio()
    return _audio_instance
