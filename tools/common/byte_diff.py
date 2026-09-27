"""Shared diffing used by the wasm and php match tools, and by progress.py."""
import difflib


def diff_lines(target_lines, candidate_lines):
    """Ratio + unified diff between two plain line lists."""
    sm = difflib.SequenceMatcher(a=target_lines, b=candidate_lines, autojunk=False)
    ratio = sm.ratio()
    diff = list(
        difflib.unified_diff(target_lines, candidate_lines, fromfile="target", tofile="candidate", lineterm="")
    )
    return ratio, diff


def diff_instructions(target, candidate):
    """target/candidate: lists of (offset, hex_bytes, text) tuples from wasm-objdump."""
    t_bytes = [i[1] for i in target]
    c_bytes = [i[1] for i in candidate]
    sm = difflib.SequenceMatcher(a=t_bytes, b=c_bytes, autojunk=False)
    ratio = sm.ratio()

    t_lines = [f"{off} {hexb:<24} {txt}" for off, hexb, txt in target]
    c_lines = [f"{off} {hexb:<24} {txt}" for off, hexb, txt in candidate]
    _, diff = diff_lines(t_lines, c_lines)
    return ratio, diff


def is_exact(target, candidate):
    return [i[1] for i in target] == [i[1] for i in candidate]
