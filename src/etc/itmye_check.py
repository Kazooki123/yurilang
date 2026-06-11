# ITMYE — Is This Memory Yuri Enough??
# YuriLang's Borrow Checker, but make it gay  :3
#
# Checks:
#   1. Mutability — is the variable mutable or immutable?
#   2. Ownership — does it have an owner? is it unused?
#   3. Movement — has it been moved (@devoted transfer)?
#   4. OS Yuri Score
#   5. Final score


import platform
import os
from types import crush_hints


# Wow colors, freaking fancy!!!
PINK = "\033[38;5;218m"
PURPLE = "\033[38;5;183m"
GREEN = "\033[38;5;156m"
RED = "\033[38;5;203m"
YELLOW = "\033[38;5;228m"
CYAN = "\033[38;5;159m"
GREY = "\033[38;5;245m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


OS_SCORES = {
    # Linus Torvalids
    "arch": (100, "Arch Linux. She configures herself.."),
    "nixos": (100, "NixOS. Purely functional. Like her feelings."),
    "gentoo": (98, "Gentoo. She compiles everything herself. Respect."),
    "fedora": (95, "Fedora. A solid choice. She approves."),
    "ubuntu": (90, "Ubuntu. Accessible and dependable. Good."),
    "debian": (92, "Debian. Stable like her feelings for her."),
    "mint": (91, "Linux Mint. Comfortable and cozy."),
    "manjaro": (93, "Manjaro. Arch but accessible. She nods."),
    "opensuse": (89, "openSUSE. The chameleon approves!!"),
    "void": (96, "Void Linux. Musl and minimalism. Elegant."),
    "alpine": (94, "Alpine. Tiny and purposeful. Like a haiku."),
    "kali": (88, "Kali Linux. She's dangerous. In a good way."),
    "termux": (97, "Termux on Android. Coding on mobile. Legendary :3!!"),
    # Wealthy people with mental illness :p
    "darwin": (75, "macOS. Proprietary but aesthetically pleasing."),
    "macos": (75, "macOS. At least it's Unix underneath."),
    # Bill Gates Sloppy Joe
    "windows": (42, "Windows. She tried. The score reflects this :/\n"),
    "windows 11": (45, "Windows 11. Slightly better. Still 45%."),
    "windows 10": (43, "Windows 10. Telemetry is not Yuri enough."),
    # Linux disguised as a chad
    "freebsd": (88, "FreeBSD. Unix heritage. She respects it!"),
    "openbsd": (91, "OpenBSD. Security-focused. Like her heart."),
    "netbsd": (87, "NetBSD. Runs everywhere. Impressive."),
    # Independent or Unknown OS_
    "haiku": (85, "Haiku OS. Named after poetry. Very Yuri."),
    "unknown": (70, "Unknown OS. She can't judge what she can't see."),
}


def get_os_score():
    system = platform.system().lower()
    release = platform.release().lower()
    version = platform.version().lower()

    if "com.termux" in os.environ.get("PREFIX", "") or "com.termux" in os.environ.get(
        "HOME", ""
    ):
        return 97, OS_SCORES["termux"][1], "Termux (Android)"

    if system == "windows":
        if "11" in release or "11" in version:
            s = OS_SCORES["windows 11"]
        elif "10" in release:
            s = OS_SCORES["windows 10"]
        else:
            s = OS_SCORES["windows"]
        return s[0], s[1], f"Windows ({release})"

    if system == "darwin":
        s = OS_SCORES["darwin"]
        return s[0], s[1], f"macOS ({platform.mac_ver()[0]})"

    if system == "linux":
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
        except FileNotFoundError:
            content = ""

        for distro, (score, msg) in OS_SCORES.items():
            if distro in content or distro in release:
                return score, msg, distro.title()

        try:
            uname = platform.uname()
            if "android" in uname.version.lower():
                s = OS_SCORES["termux"]
                return s[0], s[1], "Android/Termux"
        except Exception:
            pass

        return 80, "Linux (unknown distro). Probably fine. 🐧", "Linux"

    if system in ("freebsd", "openbsd", "netbsd"):
        s = OS_SCORES.get(system, OS_SCORES["unknown"])
        return s[0], s[1], system.title()

    s = OS_SCORES["unknown"]
    return s[0], s[1], system.title()


def check_mutability(variables, awakened, owned, shared_ptrs, glances, reaches):
    results = []
    all_vars = set(variables.keys()) | set(owned.keys())

    for name in sorted(all_vars):
        if name.startswith("__"):
            continue

        if name in awakened:
            results.append(
                {
                    "name": name,
                    "status": "immutable",
                    "symbol": "✅",
                    "color": GREEN,
                    "msg": "awakened — she knows who she is",
                    "score": 10,
                }
            )
        elif name in owned:
            results.append(
                {
                    "name": name,
                    "status": "devoted",
                    "symbol": "✅",
                    "color": GREEN,
                    "msg": "devoted — unique ownership",
                    "score": 10,
                }
            )
        elif name in shared_ptrs:
            results.append(
                {
                    "name": name,
                    "status": "shared",
                    "symbol": "✅",
                    "color": CYAN,
                    "msg": f"@yuu_ptr → {shared_ptrs[name]}",
                    "score": 9,
                }
            )
        elif name in glances:
            results.append(
                {
                    "name": name,
                    "status": "glancing",
                    "symbol": "✅",
                    "color": CYAN,
                    "msg": f"@glance → {glances[name]} (read-only borrow)",
                    "score": 9,
                }
            )
        elif name in reaches:
            results.append(
                {
                    "name": name,
                    "status": "reaching",
                    "symbol": "⚠️ ",
                    "color": YELLOW,
                    "msg": f"@reach → {reaches[name]} (mutable borrow — handle carefully)",
                    "score": 7,
                }
            )
        else:
            results.append(
                {
                    "name": name,
                    "status": "mutable",
                    "symbol": "💛",
                    "color": YELLOW,
                    "msg": "mutable — still figuring it out",
                    "score": 8,
                }
            )

    return results


def check_ownership(variables, owned, shared_ptrs, functions, awakened):
    results = []
    issues = []

    for name in sorted(variables.keys()):
        if name.startswith("__"):
            continue

        val = variables.get(name)

        if val is None and name not in awakened:
            issues.append(
                {
                    "name": name,
                    "symbol": "⚠️ ",
                    "color": YELLOW,
                    "msg": "value is uncertain — she hasn't decided yet",
                    "score": 5,
                }
            )
        elif name in owned:
            results.append(
                {
                    "name": name,
                    "symbol": "✅",
                    "color": GREEN,
                    "msg": "clear owner — @devoted",
                    "score": 10,
                }
            )
        elif name in shared_ptrs:
            source = shared_ptrs[name]
            results.append(
                {
                    "name": name,
                    "symbol": "✅",
                    "color": CYAN,
                    "msg": f"shared ownership with '{source}'",
                    "score": 9,
                }
            )
        else:
            results.append(
                {
                    "name": name,
                    "symbol": "✅",
                    "color": GREEN,
                    "msg": "owned by current scope",
                    "score": 8,
                }
            )

    return results, issues


def check_movement(owned, variables):
    results = []

    for name in list(owned.keys()):
        if name not in variables:
            results.append(
                {
                    "name": name,
                    "symbol": "💔",
                    "color": RED,
                    "msg": "moved — she gave it away. it belongs elsewhere now.",
                    "score": 0,
                    "moved": True,
                }
            )
        else:
            results.append(
                {
                    "name": name,
                    "symbol": "✅",
                    "color": GREEN,
                    "msg": "in place — she still holds it",
                    "score": 10,
                    "moved": False,
                }
            )

    return results


def check_type_hints(variables, crush_hints):
    from src.types import check_hint, type_name

    results = []

    for name, val in variables.items():
        if name.startswith("__"):
            continue

        hint = crush_hints.get(name)
        if hint:
            matches, expected, actual = check_hint(name, val)
            if matches:
                results.append(
                    {
                        "name": name,
                        "symbol": "✅",
                        "color": GREEN,
                        "msg": f"@crush {name} = {hint} ✓ (value is {actual})",
                        "score": 10,
                    }
                )
            else:
                results.append(
                    {
                        "name": name,
                        "symbol": "⚠️ ",
                        "color": YELLOW,
                        "msg": f"@crush {name} = {hint} but value is {actual}",
                        "score": 6,
                    }
                )
        else:
            results.append(
                {
                    "name": name,
                    "symbol": "💛",
                    "color": GREY,
                    "msg": f"no @crush hint — type is {type_name(val)}",
                    "score": 7,
                }
            )

    return results


def calculate_score(
    mut_results, own_results, own_issues, mov_results, type_results, os_score
):
    all_scores = []

    for r in mut_results:
        all_scores.append(r["score"])
    for r in own_results:
        all_scores.append(r["score"])
    for r in own_issues:
        all_scores.append(r["score"])
    for r in mov_results:
        all_scores.append(r["score"])
    for r in type_results:
        all_scores.append(r["score"])

    if all_scores:
        code_score = sum(all_scores) / len(all_scores) * 10
        final = (code_score * 0.85) + (os_score * 0.15)
    else:
        final = os_score

    return round(min(100, max(0, final)))


def verdict(score):
    if score == 100:
        return (
            GREEN,
            "Perfect. 🧡",
            "She knows exactly who she is and what she holds.\n"
            "  Every variable has purpose. Every feeling has a name.\n"
            "  This memory is completely Yuri.",
        )
    elif score >= 90:
        return (
            GREEN,
            "Almost perfect. 🌸",
            "She knows herself well.\n"
            "  A few feelings are still unnamed, but she's getting there.",
        )
    elif score >= 80:
        return (
            CYAN,
            "Pretty Yuri. 💜",
            "Good memory hygiene. Some variables could be more intentional.\n"
            "  Consider @crush hints and @awakening for settled values.",
        )
    elif score >= 70:
        return (
            YELLOW,
            "Getting there!!",
            "She's still figuring things out.\n"
            "  Add @crush hints, use @devoted for owned values,\n"
            "  and @awakening for what she knows for certain.",
        )
    elif score >= 50:
        return (
            YELLOW,
            "Uncertain. 🤍",
            "The memory is confused. Like feelings without names.\n"
            "  Several variables lack ownership or type hints.\n"
            "  She needs to figure out who she is.",
        )
    elif score >= 42:
        return (
            RED,
            "Are you on Windows? 💔",
            "The OS penalty is significant.\n"
            "  Consider WSL2 at minimum.\n"
            "  She will not judge you. Much.",
        )
    else:
        return (
            RED,
            "Not Yuri enough. 💔",
            "This memory needs work.\n"
            "  Moved values, uncertain types, no ownership.\n"
            "  She deserves better. So does your code.",
        )


def run_itmye(variables, awakened, owned, shared_ptrs, glances, reaches, functions):
    ###############################
    #         ITMYE CHECKER       #
    # Is This Memory Yuri Enough?  #
    ##############################

    print(f"\n{PINK}{BOLD}")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   ITMYE — Is This Memory Yuri Enough?        ║")
    print("  ║       YuriLang Memory Safety Auditor         ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(f"{RESET}")

    print(f"{PURPLE}{BOLD}  ① Mutability Check{RESET}")
    print(f"{GREY}  {'─' * 48}{RESET}")
    mut_results = check_mutability(
        variables, awakened, owned, shared_ptrs, glances, reaches
    )

    for r in mut_results:
        print(
            f"  {r['symbol']} {r['color']}{r['name']:<20}{RESET}{GREY}{r['msg']}{RESET}"
        )
    if not mut_results:
        print(f"  {GREY}  No variables declared.{RESET}")
    print()

    print(f"{PURPLE}{BOLD}  ② Ownership Check{RESET}")
    print(f"{GREY}  {'─' * 48}{RESET}")
    own_results, own_issues = check_ownership(
        variables, owned, shared_ptrs, functions, awakened
    )
    for r in own_results + own_issues:
        print(
            f"  {r['symbol']} {r['color']}{r['name']:<20}{RESET}{GREY}{r['msg']}{RESET}"
        )
    if not own_results and not own_issues:
        print(f"  {GREY}  No ownership data.{RESET}")
    print()

    print(f"{PURPLE}{BOLD}  ③ Movement Check{RESET}")
    print(f"{GREY}  {'─' * 48}{RESET}")
    mov_results = check_movement(owned, variables)
    if mov_results:
        for r in mov_results:
            status = "MOVED" if r["moved"] else "in place"
            print(
                f"  {r['symbol']} {r['color']}{r['name']:<20}{RESET}"
                f"{GREY}{r['msg']}{RESET}"
            )
        else:
            print(
                f"  {GREEN}✅ {GREY}No moved values. "
                f"She holds everything she should.{RESET}"
            )
        print()

    print(f"{PURPLE}{BOLD}  ④ Type Hint Check (@crush){RESET}")
    print(f"{GREY}  {'─' * 48}{RESET}")
    type_results = check_type_hints(variables, crush_hints)
    for r in type_results:
        print(
            f"  {r['symbol']} {r['color']}{r['name']:<20}{RESET}{GREY}{r['msg']}{RESET}"
        )
    if not type_results:
        print(f"  {GREY}  No variables to check.{RESET}")
    print()

    print(f"{PURPLE}{BOLD}  ⑤ OS Yuri Score{RESET}")
    print(f"{GREY}  {'─' * 48}{RESET}")
    os_score, os_msg, os_name = get_os_score()
    os_color = (
        GREEN
        if os_score >= 90
        else CYAN
        if os_score >= 75
        else YELLOW
        if os_score >= 50
        else RED
    )
    print(f"  {os_color}{'★' * (os_score // 10)}{'☆' * (10 - os_score // 10)}{RESET}")
    print(f"  {os_color}{os_name}: {os_score}/100{RESET}")
    print(f"  {GREY}{os_msg}{RESET}")
    print()

    final_score = calculate_score(
        mut_results, own_results, own_issues, mov_results, type_results, os_score
    )

    color, title, msg = verdict(final_score)

    print(f"{GREY}  {'═' * 48}{RESET}")
    print(f"\n  {color}{BOLD}Memory Yuri Score: {final_score}% — {title}{RESET}\n")
    print(f"  {GREY}{msg}{RESET}\n")

    filled = final_score // 5
    empty = 20 - filled
    bar = f"{color}{'█' * filled}{GREY}{'░' * empty}{RESET}"
    print(f"  [{bar}] {color}{final_score}%{RESET}\n")

    print(f"{GREY}  {'═' * 48}{RESET}\n")

    return final_score
