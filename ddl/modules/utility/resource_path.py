import os, sys

def resource_path(rel_path: str) -> str:
    """
    Resolve rel_path for both dev and PyInstaller one-file.
    Also try a few common project locations if not found in CWD.
    """
    candidates = []

    # 1) PyInstaller temp
    base = getattr(sys, "_MEIPASS", None)
    if base: candidates.append(os.path.join(base, rel_path))

    # 2) CWD (launcher.py chdir already)
    candidates.append(os.path.abspath(rel_path))

    # 3) Package root
    here = os.path.dirname(os.path.abspath(__file__))
    pkg_root = os.path.abspath(os.path.join(here, "..", ".."))
    candidates.append(os.path.join(pkg_root, rel_path))

    # 4) Project root (up one more)
    project_root = os.path.abspath(os.path.join(pkg_root, ".."))
    candidates.append(os.path.join(project_root, rel_path))

    for p in candidates:
        if os.path.exists(p):
            return p
    # fallback to original rel_path
    return rel_path
