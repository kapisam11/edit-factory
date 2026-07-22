import json
from pathlib import Path
from typing import Optional, List
import json

# load optional weights config
WEIGHTS = {
    'faces_weight': 2.0,
    'motion_weight': 1.5,
    'match_weight': 1.0,
    'label_boost': 1.5,
    'center_boost': 2.0,
}
try:
    wpath = Path('hooks.weights.json')
    if wpath.exists():
        WEIGHTS.update(json.loads(wpath.read_text(encoding='utf-8')))
except Exception:
    pass


def load_visuals(pkg_dir: Path) -> List[dict]:
    vfile = pkg_dir / 'visuals' / 'visuals.json'
    if vfile.exists():
        try:
            return json.loads(vfile.read_text(encoding='utf-8'))
        except Exception:
            return []
    # fallback: aggregate visuals/*.json
    vis_dir = pkg_dir / 'visuals'
    items = []
    if vis_dir.exists():
        for p in sorted(vis_dir.glob('*.json')):
            try:
                j = json.loads(p.read_text(encoding='utf-8'))
                if isinstance(j, list):
                    items.extend(j)
                elif isinstance(j, dict):
                    items.append(j)
            except Exception:
                continue
    return items


def strongest_visual(visuals: List[dict]) -> Optional[dict]:
    if not visuals:
        return None
    # prefer visuals with faces_detected > 0 and high motion_score
    # also prefer faces near center (likely facing camera) and visuals with object labels
    def score(v):
        faces = v.get('faces_detected') or 0
        motion = v.get('motion_score') or 0.0
        match = v.get('match_score') or 0.0
        s = faces * float(WEIGHTS.get('faces_weight', 2.0)) + motion * float(WEIGHTS.get('motion_weight', 1.5)) + match * float(WEIGHTS.get('match_weight', 1.0))
        # object labels boost
        labels = v.get('object_labels') or v.get('labels') or []
        if labels:
            s += float(WEIGHTS.get('label_boost', 1.5))
        # prefer face near center if bbox and image dims provided
        try:
            bbox = v.get('face_box') or v.get('face_bbox')
            iw = v.get('image_width')
            ih = v.get('image_height')
            if bbox and iw and ih:
                # bbox may be [x,y,w,h]
                x, y, w, h = bbox
                cx = x + w / 2.0
                cy = y + h / 2.0
                # normalized distance from center
                dx = abs(cx - iw / 2.0) / (iw / 2.0)
                dy = abs(cy - ih / 2.0) / (ih / 2.0)
                dist = (dx + dy) / 2.0
                # closer to center -> higher score
                s += max(0, (1.0 - dist) * float(WEIGHTS.get('center_boost', 2.0)))
        except Exception:
            pass
        return s

    return max(visuals, key=score)


HOOK_TEMPLATES = [
    'His final choice',
    'Betrayal revealed',
    'Lost forever',
    'The real reason',
    'Nobody believed him',
    'The hidden reason',
    'Shocking moment',
]


def generate_from_visual(v: dict, personas: List[dict] = None) -> str:
    # If a persona name is present, use it in short hooks when possible
    name = None
    try:
        if personas:
            for p in personas:
                if p.get('name'):
                    name = p.get('name')
                    break
    except Exception:
        name = None

    faces = v.get('faces_detected') or 0
    motion = v.get('motion_score') or 0.0
    desc = v.get('description') or v.get('title') or ''

    # Heuristic selection
    if faces >= 1 and motion > 0.05:
        if name:
            # prefer including name when short
            if len(name.split()) <= 2:
                return f"{name}'s choice"
            return 'His final choice'
        # if face centered, use 'The real reason' variations
        return 'His final choice'
    if motion > 0.2:
        return 'Shocking moment'
    # prefer object-driven hooks
    labels = v.get('object_labels') or v.get('labels') or []
    if labels:
        # take the most prominent label
        lab = labels[0] if isinstance(labels, list) and labels else None
        if lab:
            lab = str(lab).title()
            return f"{lab} revealed" if len(lab.split()) <= 2 else 'Shocking moment'
    if 'betray' in desc.lower() or 'betray' in (v.get('tags') or []):
        return 'Betrayal revealed'
    if 'lost' in desc.lower():
        return 'Lost forever'
    # fallback: pick a short template closest to desired length
    for t in HOOK_TEMPLATES:
        if 2 <= len(t.split()) <= 5:
            return t
    return 'The real reason'


def generate_visual_hook(pkg_path: str) -> Optional[str]:
    pkg = Path(pkg_path)
    visuals = load_visuals(pkg)
    v = strongest_visual(visuals)
    personas = []
    try:
        pfile = pkg / 'personas.json'
        if pfile.exists():
            personas = json.loads(pfile.read_text(encoding='utf-8'))
    except Exception:
        personas = []
    if not v:
        return None
    return generate_from_visual(v, personas)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python tools/visual_hook_generator.py <package_path>')
        raise SystemExit(1)
    hook = generate_visual_hook(sys.argv[1])
    if hook:
        print(hook)
        raise SystemExit(0)
    else:
        raise SystemExit(2)
