import json
from pathlib import Path

SWC_REGISTRY = {}

def load_registry():
    global SWC_REGISTRY
    registry_path = Path(__file__).parent / "swc_registry_full.json"
    if registry_path.exists():
        SWC_REGISTRY = json.loads(registry_path.read_text(encoding="utf-8"))

def get_swc_meta(swc_id: str):
    if not SWC_REGISTRY:
        load_registry()
    return SWC_REGISTRY.get(swc_id)
