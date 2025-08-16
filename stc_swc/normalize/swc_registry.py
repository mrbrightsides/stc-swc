from pathlib import Path
import json

_REGISTRY = None

def _load():
    global _REGISTRY
    if _REGISTRY is not None:
        return
    # Cache yang dibuat fetcher
    path = Path(__file__).parent / "swc_registry_full.json"
    if path.exists():
        _REGISTRY = json.loads(path.read_text(encoding="utf-8"))
    else:
        _REGISTRY = {}  # fallback kosong

def get_swc_meta(swc_id: str):
    """
    swc_id bisa '107' atau 'SWC-107'
    return dict: {title, severity, remediation, ...} atau None
    """
    _load()
    if not swc_id:
        return None
    key = str(swc_id).replace("SWC-", "")
    return _REGISTRY.get(key)
