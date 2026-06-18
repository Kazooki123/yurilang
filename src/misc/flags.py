# Flags from LGBTQ
# </3
# TODO: Add Country Flags.

import random

def random_flag():
    name = random.choice(list(FLAGS.keys()))
    print_flag(name)
    return name

def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _print_stripes(stripes, width=33):
    for color in stripes:
        r, g, b = _hex_to_rgb(color)
        print(f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m")    

# ─────────────────
#  Flag definitions
# ─────────────────

LESBIAN_FLAG = [
    "D52D00", "EF7627", "FF9A56",
    "FFFFFF",
    "D162A4", "B55690", "A30262",
]

SAPPHIC_FLAG = [
    "FD8BA8", "FBF2FF", "C76BC5", "FDD768"
]

BUTCH_FLAG = [
    "D52C00", "F07528", "FFFCEE", "FFAD09", "A06E00"
]

MLM_FLAG = [
    # 2024 community redesign — greens/blues
    "078D70", "26CEAA", "98E8C1",
    "FFFFFF",
    "7BADE2", "5049CC", "3D1A78",
]

BI_FLAG = [
    "D60270", "D60270",
    "9B4F96",
    "0038A8", "0038A8",
]

TRANS_FLAG = [
    "5BCEFA", "F5A9B8", "FFFFFF", "F5A9B8", "5BCEFA",
]

PAN_FLAG = [
    "FF218C", "FFD800", "21B1FF"
]

GFLUID_FLAG = [
    "FF75A2", "FFFFFF", "BE18D6", "000000", "2F3CBE"
]

ASEXUAL_FLAG = [
    "000000", "A3A3A3", "FFFFFF", "800080"
]

ABRO_FLAG = [
    "75CA91", "B3E4C7", "FFFFFF", "E695B5", "D9446C"
]

FLAGS = {
    "lesbian": LESBIAN_FLAG,
    "sapphic": SAPPHIC_FLAG,
    "butch":   BUTCH_FLAG,
    "mlm":     MLM_FLAG,
    "bi":      BI_FLAG,
    "trans":   TRANS_FLAG,
    "pan":     PAN_FLAG,
    "gfluid":  GFLUID_FLAG,
    "asexual": ASEXUAL_FLAG,
    "abro":    ABRO_FLAG
}

def print_flag(name):
    name = str(name).lower()
    stripes = FLAGS.get(name)
    if stripes is None:
        raise ValueError(f"Unknown flag '{name}' — options: {', '.join(FLAGS.keys())}")
    _print_stripes(stripes)
