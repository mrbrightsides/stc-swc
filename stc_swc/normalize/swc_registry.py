# Placeholder SWC registry cache (v0.1)
# v0.2: tambahkan fetch/scrape resmi + penyimpanan JSON

SWC_REGISTRY_MINI = {
    "SWC-101": {"title": "Integer Overflow and Underflow", "severity": "high"},
    "SWC-107": {"title": "Reentrancy", "severity": "high"},
    "SWC-100": {"title": "Function Default Visibility", "severity": "medium"},
}

def get_swc_meta(swc_id: str):
    if not swc_id:
        return None
    return SWC_REGISTRY_MINI.get(swc_id)
