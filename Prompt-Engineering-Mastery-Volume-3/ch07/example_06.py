"""
Surgical Delta Patch Engine: Applies structured search-and-replace modifications
to prevent full-file regeneration regressions during self-refinement turns.
"""

from typing import List, Dict, Any, Tuple


class SurgicalDeltaPatchEngine:
    """Applies structured replacement chunks to existing source files."""

    @staticmethod
    def apply_patches(original_source: str, patches: List[Dict[str, str]]) -> Tuple[bool, str, List[str]]:
        """
        Applies a list of search-and-replace patches.
        Each patch requires: {'target_string': '...', 'replacement_string': '...'}
        Returns: (all_applied, modified_source, error_log)
        """
        modified = original_source
        errors = []

        for i, patch in enumerate(patches):
            target = patch.get("target_string", "")
            replacement = patch.get("replacement_string", "")

            if not target:
                errors.append(f"Patch {i}: Empty target string.")
                continue

            if target not in modified:
                errors.append(f"Patch {i}: Target string not found in source text: '{target[:40]}...'")
                continue

            occurrences = modified.count(target)
            if occurrences > 1:
                errors.append(
                    f"Patch {i}: Ambiguous target string. Found {occurrences} occurrences. "
                    f"Target must be unique."
                )
                continue

            modified = modified.replace(target, replacement, 1)

        success = len(errors) == 0
        return success, modified, errors
