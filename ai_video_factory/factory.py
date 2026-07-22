"""Orchestrator for the AI Video Factory workflow."""
from typing import Optional
from .producer import produce_package
from .research import research_topic
from .plan import make_idea
from .thumbnail import make_thumbnail
from .output_packager import write_package
import os
from datetime import datetime
from . import policy
from . import learning


def create_package(topic: str, out_root: str = "output", thumbnail_subject: str = None, use_groq: bool = False, groq_api_key: Optional[str] = None, prune_min_match: float = 0.25, prune_min_motion: float = 0.07, prune_require_faces: Optional[list] = None, use_spacy_persona: bool = False, target_total_seconds: float = 45.0, config_path: Optional[str] = None) -> str:
    """Generate a full upload package for `topic` and return the package path.

    This function delegates the core production to `produce_package()` and
    preserves the previous policy and quality prediction steps. Groq
    enrichment is optional and controlled by `use_groq`/`groq_api_key`.
    """
    # delegate core package creation to the new producer pipeline
    pkg_dir = produce_package(topic, out_root=out_root, use_groq=use_groq, groq_api_key=groq_api_key, thumbnail_subject=thumbnail_subject, prune_min_match=prune_min_match, prune_min_motion=prune_min_motion, prune_require_faces=prune_require_faces, use_spacy_persona=use_spacy_persona, target_total_seconds=target_total_seconds, config_path=config_path)

    # run policy checks and attach report (best-effort)
    try:
        violations = policy.check_package(pkg_dir)
        with open(os.path.join(pkg_dir, "policy_violations.json"), "w", encoding="utf-8") as f:
            import json

            json.dump(violations, f, indent=2)
    except Exception:
        pass

    # compute quality prediction (heuristic or model)
    try:
        pred = learning.predict_quality(pkg_dir)
        with open(os.path.join(pkg_dir, "quality_prediction.json"), "w", encoding="utf-8") as f:
            import json

            json.dump(pred, f, indent=2)
    except Exception:
        pass

    # final human-like checks
    try:
        from .quality_control import run_final_checks

        final_checks = run_final_checks(pkg_dir)
        with open(os.path.join(pkg_dir, "final_checks.json"), "w", encoding="utf-8") as f:
            import json

            json.dump(final_checks, f, indent=2)
    except Exception:
        pass

    return pkg_dir
