"""
FLAC - Encoding/Decoding for Yurilang
Uses the libFLAC.dll C API via `ctypes`
"""

import ctypes
import os
import sys
import math

if sys.platform == "win32":
    lib_name = "libflac.dll"
    lib_dir = "bin"
elif sys.platform == "linux":
    lib_name = "libflac.so"
    lib_dir = "bin"
elif sys.platform == "darwin":
    lib_name = "libflac.dylib"
    lib_dir = "bin"
else:
    raise OSError(f"Unsupported platform: {sys.platform}")

_dll_path = os.path.join(
    os.path.dirname(__file__), 
    "..", 
    lib_dir, 
    lib_name
)

_flac = ctypes.CDLL(_dll_path)

c_uint  = ctypes.c_uint32
c_int32 = ctypes.c_int32
c_bool  = ctypes.c_int   # FLAC__bool is int under the hood

# ─────────────────────────────────────────────
#  Encoder function signatures
# ─────────────────────────────────────────────
_flac.FLAC__stream_encoder_new.restype                       = ctypes.c_void_p
_flac.FLAC__stream_encoder_delete.argtypes                   = [ctypes.c_void_p]
_flac.FLAC__stream_encoder_set_channels.argtypes             = [ctypes.c_void_p, c_uint]
_flac.FLAC__stream_encoder_set_channels.restype              = c_bool
_flac.FLAC__stream_encoder_set_bits_per_sample.argtypes      = [ctypes.c_void_p, c_uint]
_flac.FLAC__stream_encoder_set_bits_per_sample.restype       = c_bool
_flac.FLAC__stream_encoder_set_sample_rate.argtypes          = [ctypes.c_void_p, c_uint]
_flac.FLAC__stream_encoder_set_sample_rate.restype           = c_bool
_flac.FLAC__stream_encoder_set_compression_level.argtypes    = [ctypes.c_void_p, c_uint]
_flac.FLAC__stream_encoder_set_compression_level.restype     = c_bool
_flac.FLAC__stream_encoder_set_total_samples_estimate.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
_flac.FLAC__stream_encoder_set_total_samples_estimate.restype  = c_bool
_flac.FLAC__stream_encoder_init_file.argtypes                = [ctypes.c_void_p, ctypes.c_char_p,
                                                                ctypes.c_void_p, ctypes.c_void_p]
_flac.FLAC__stream_encoder_init_file.restype                 = ctypes.c_int
_flac.FLAC__stream_encoder_process_interleaved.argtypes      = [ctypes.c_void_p,
                                                                ctypes.POINTER(c_int32), c_uint]
_flac.FLAC__stream_encoder_process_interleaved.restype       = c_bool
_flac.FLAC__stream_encoder_finish.argtypes                   = [ctypes.c_void_p]
_flac.FLAC__stream_encoder_finish.restype                    = c_bool

# ─────────────────────────────────────────────
#  Decoder function signatures
# ─────────────────────────────────────────────
_flac.FLAC__stream_decoder_new.restype                       = ctypes.c_void_p
_flac.FLAC__stream_decoder_delete.argtypes                   = [ctypes.c_void_p]
_flac.FLAC__stream_decoder_init_file.argtypes                = [ctypes.c_void_p, ctypes.c_char_p,
                                                                ctypes.c_void_p, ctypes.c_void_p,
                                                                ctypes.c_void_p, ctypes.c_void_p]
_flac.FLAC__stream_decoder_init_file.restype                 = ctypes.c_int
_flac.FLAC__stream_decoder_process_until_end_of_stream.argtypes = [ctypes.c_void_p]
_flac.FLAC__stream_decoder_process_until_end_of_stream.restype  = c_bool
_flac.FLAC__stream_decoder_finish.argtypes                   = [ctypes.c_void_p]
_flac.FLAC__stream_decoder_finish.restype                    = c_bool


def encode_samples(samples, path, sample_rate=44100, channels=1, bits=16, compression=5):
    """
    Encode a flat list of integer PCM samples to a .flac file.
    samples   : list of ints (interleaved if stereo)
    path      : output file path string
    """
    enc = _flac.FLAC__stream_encoder_new()
    if not enc:
        raise RuntimeError("Failed to create FLAC encoder")

    _flac.FLAC__stream_encoder_set_channels(enc, channels)
    _flac.FLAC__stream_encoder_set_bits_per_sample(enc, bits)
    _flac.FLAC__stream_encoder_set_sample_rate(enc, sample_rate)
    _flac.FLAC__stream_encoder_set_compression_level(enc, compression)
    _flac.FLAC__stream_encoder_set_total_samples_estimate(enc, len(samples) // channels)

    status = _flac.FLAC__stream_encoder_init_file(
        enc, path.encode("utf-8"), None, None
    )
    if status != 0:
        _flac.FLAC__stream_encoder_delete(enc)
        raise RuntimeError(f"FLAC encoder init failed with status {status}")

    buf = (c_int32 * len(samples))(*samples)
    ok = _flac.FLAC__stream_encoder_process_interleaved(enc, buf, len(samples) // channels)
    if not ok:
        raise RuntimeError("FLAC encoding process failed")

    _flac.FLAC__stream_encoder_finish(enc)
    _flac.FLAC__stream_encoder_delete(enc)


def decode_to_samples(path):
    """
    Decode a .flac file and return (samples: list[int], sample_rate, channels, bits).
    Uses a write callback to collect PCM frames.
    """
    collected = []
    meta      = {}

    WRITE_CB = ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_void_p,   # decoder
        ctypes.c_void_p,   # frame ptr  (FLAC__Frame*)
        ctypes.POINTER(ctypes.POINTER(c_int32)),  # buffer[channels][samples]
        ctypes.c_void_p    # client_data
    )

    # Metadata callback: called for STREAMINFO
    META_CB = ctypes.CFUNCTYPE(
        None,
        ctypes.c_void_p,   # decoder
        ctypes.c_void_p,   # metadata ptr
        ctypes.c_void_p    # client_data
    )

    ERROR_CB = ctypes.CFUNCTYPE(
        None,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p
    )

    # FLAC__Frame header is: blocksize(u32), sample_rate(u32), channels(u32), bits(u32), ...
    class _FrameHeader(ctypes.Structure):
        _fields_ = [
            ("blocksize",    ctypes.c_uint32),
            ("sample_rate",  ctypes.c_uint32),
            ("channels",     ctypes.c_uint32),
            ("channel_assignment", ctypes.c_int),
            ("bits_per_sample",    ctypes.c_uint32),
            ("number_type",  ctypes.c_int),
            ("frame_number", ctypes.c_uint64),
        ]

    class _Frame(ctypes.Structure):
        _fields_ = [("header", _FrameHeader)]

    def _write_cb(decoder, frame_ptr, buffer, client_data):
        frame  = ctypes.cast(frame_ptr, ctypes.POINTER(_Frame)).contents
        hdr    = frame.header
        meta.update({
            "sample_rate": hdr.sample_rate,
            "channels":    hdr.channels,
            "bits":        hdr.bits_per_sample,
        })
        for s in range(hdr.blocksize):
            for c in range(hdr.channels):
                collected.append(buffer[c][s])
        return 0  # FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE

    def _meta_cb(decoder, metadata, client_data):
        pass

    def _err_cb(decoder, status, client_data):
        pass

    write_cb = WRITE_CB(_write_cb)
    meta_cb  = META_CB(_meta_cb)
    err_cb   = ERROR_CB(_err_cb)

    dec = _flac.FLAC__stream_decoder_new()
    if not dec:
        raise RuntimeError("Failed to create FLAC decoder")

    status = _flac.FLAC__stream_decoder_init_file(
        dec, path.encode("utf-8"), write_cb, meta_cb, err_cb, None
    )
    if status != 0:
        _flac.FLAC__stream_decoder_delete(dec)
        raise RuntimeError(f"FLAC decoder init failed with status {status}")

    _flac.FLAC__stream_decoder_process_until_end_of_stream(dec)
    _flac.FLAC__stream_decoder_finish(dec)
    _flac.FLAC__stream_decoder_delete(dec)

    return collected, meta.get("sample_rate", 44100), meta.get("channels", 1), meta.get("bits", 16)


# ─────────────────────────────────────────────
#  Waveform generators (creative stuff 🎵 ^_^)
# ─────────────────────────────────────────────

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

def _flatten_samples(val):
    result = []
    for item in val:
        if isinstance(item, list):
            result.extend(_flatten_samples(item))
        elif isinstance(item, int):
            result.append(item)
    return result

def gen_sine(freq=440.0, duration=1.0, sample_rate=44100, amplitude=0.8):
    """Pure sine wave."""
    peak = int(amplitude * 32767)
    n    = int(sample_rate * duration)
    return [_clamp(int(peak * math.sin(2 * math.pi * freq * i / sample_rate)), -32768, 32767)
            for i in range(n)]

def gen_square(freq=440.0, duration=1.0, sample_rate=44100, amplitude=0.5):
    """Square wave."""
    peak   = int(amplitude * 32767)
    period = sample_rate / freq
    return [peak if (i % period) < (period / 2) else -peak
            for i in range(int(sample_rate * duration))]

def gen_sawtooth(freq=440.0, duration=1.0, sample_rate=44100, amplitude=0.6):
    """Sawtooth wave."""
    peak   = int(amplitude * 32767)
    period = sample_rate / freq
    return [int(peak * (2 * ((i % period) / period) - 1))
            for i in range(int(sample_rate * duration))]

def gen_noise(duration=1.0, sample_rate=44100, amplitude=0.3):
    """White noise."""
    import random
    peak = int(amplitude * 32767)
    return [random.randint(-peak, peak) for _ in range(int(sample_rate * duration))]

def gen_silence(duration=1.0, sample_rate=44100):
    return [0] * int(sample_rate * duration)

def mix(*tracks):
    flat_tracks = [_flatten_samples(t) for t in tracks]
    length = max(len(t) for t in flat_tracks)
    result = []
    for t in tracks:
        if isinstance(t, list) and len(t) > 0 and isinstance(t[0], list):
            t = [x for sub in t for x in sub]
        flat_tracks.append(t)

    for i in range(length):
        s = sum(t[i] for t in flat_tracks if i < len(t))
        result.append(_clamp(s, -32768, 32767))
    return result

def concat(*tracks):
    result = []
    for t in tracks:
        result.extend(_flatten_samples(t))
    return result


FLAC_OPS = {
    "encode":    encode_samples,
    "decode":    decode_to_samples,

    "sine":      gen_sine,
    "square":    gen_square,
    "saw":       gen_sawtooth,
    "noise":     gen_noise,
    "silence":   gen_silence,

    "mix":       mix,
    "concat":    concat,
}
