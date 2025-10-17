import os

def format_dir(base: str, fmt: str) -> str:
    fmt = fmt.lower()
    mapping = {
        "monotype":"monotype","ou":"ou","ubers":"ubers","uu":"uu",
        "ru":"ru","nu":"nu","pu":"pu","lc":"lc"
    }
    key = mapping.get(fmt, "monotype")
    path = os.path.join(base, key)
    if not os.path.isdir(path):
        raise RuntimeError(f"Missing packs for format '{fmt}' at {path}. Run tools/build_packs.py.")
    return path
