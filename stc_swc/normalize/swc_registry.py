from pathlib import Path
import json
_REGISTRY = None
def _load():
    global _REGISTRY
    if _REGISTRY is not None: return
    p = Path(__file__).parent / "swc_registry_full.json"
    _REGISTRY = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
def get_swc_meta(swc_id: str):
    _load()
    if not swc_id: return None
    key = str(swc_id).replace("SWC-","")
    return _REGISTRY.get(key)
