# Verify ISO - Yurilang
# ISO9660 structural + deep hash verification
# Pure Python, no DLLs needed

import hashlib
import os

CHUNK_SIZE = 8 * 1024 * 1024


def _check_iso9660_magic(path):
    """Checks for the CD001 magic at the Primary Volume Descriptor (sector 16 / offset 0x8000)."""
    try:
        with open(path, "rb") as f:
            f.seek(0x8000 + 1)  # byte 0 is the descriptor type, "CD001" starts at byte 1
            return f.read(5) == b"CD001"
    except Exception:
        return False


def _hash_file(path, algorithm="sha256"):
    """Hashes a file in chunks with a progress indicator, safe for large ISOs."""
    hasher     = hashlib.new(algorithm)
    total_size = os.path.getsize(path)
    read_bytes = 0
    last_pct   = -1

    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
            read_bytes += len(chunk)

            if total_size > 0:
                pct = int((read_bytes / total_size) * 100)
                if pct != last_pct and pct % 5 == 0:
                    print(f"\rHashing... {pct}%", end="", flush=True)
                    last_pct = pct

    print("\rHashing... 100%")
    return hasher.hexdigest()


def verify_iso(path, expected_hash=None, algorithm="sha256"):
    """Verifies structure (CD001) and computes a deep hash. Prints a report."""
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        return {"valid_path": False}

    size = os.path.getsize(path)
    print(f"File: {path}")
    print(f"Size: {size / (1024 * 1024):.2f} MB")

    is_iso9660 = _check_iso9660_magic(path)
    print(f"ISO9660 structure: {'valid (CD001 found)' if is_iso9660 else 'NOT FOUND — may be corrupt, a raw/bin image, or a different format'}")

    print(f"Computing {algorithm.upper()}...")
    computed = _hash_file(path, algorithm)
    print(f"{algorithm.upper()}: {computed}")

    result = {
        "path": path, "size_bytes": size,
        "is_iso9660": is_iso9660,
        "hash": computed, "algorithm": algorithm,
    }

    if expected_hash:
        expected_hash = expected_hash.strip().lower()
        match = computed.lower() == expected_hash
        print(f"Expected: {expected_hash}")
        print(f"Match: {'YES ✅' if match else 'NO ❌'}")
        result["expected_hash"] = expected_hash
        result["match"] = match

    return result
