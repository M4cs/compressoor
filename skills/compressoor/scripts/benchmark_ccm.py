#!/usr/bin/env python3
"""
Measure compression and verify exact preservation of protected atoms.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import tiktoken


CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
ENV_RE = re.compile(r"\$[A-Z][A-Z0-9_]*")
PATH_RE = re.compile(r"(?:\./|\../|/)[A-Za-z0-9._/\-]+")
VERSION_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\.[A-Za-z_][A-Za-z0-9_]{2,}\b")


def load_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def token_count(text: str, encoding_name: str) -> tuple[int, str]:
    try:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text)), encoding_name
    except Exception:
        # Offline fallback: keep the tool usable even when the tokenizer file
        # is not cached locally. This is coarse but directionally useful.
        approx = max(1, round(len(text.encode("utf-8")) / 4))
        return approx, f"approx_bytes_div_4:{encoding_name}"


def protected_atoms(text: str) -> list[str]:
    patterns = [
        CODE_BLOCK_RE,
        INLINE_CODE_RE,
        URL_RE,
        ENV_RE,
        PATH_RE,
        VERSION_RE,
        DATE_RE,
        IDENT_RE,
    ]
    atoms: list[str] = []
    for pattern in patterns:
        atoms.extend(pattern.findall(text))
    seen = set()
    ordered: list[str] = []
    for atom in atoms:
        if atom not in seen:
            ordered.append(atom)
            seen.add(atom)
    return ordered


def normalize_atom(atom: str) -> str:
    return atom.strip().strip("`").rstrip(".,;:")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark CCM compression.")
    parser.add_argument("source", help="Path to original text")
    parser.add_argument("candidate", help="Path to compressed text")
    parser.add_argument(
        "--encoding",
        default="o200k_base",
        help="tiktoken encoding name, default: o200k_base",
    )
    args = parser.parse_args()

    source = load_text(args.source)
    candidate = load_text(args.candidate)

    src_tokens, encoding_used = token_count(source, args.encoding)
    cand_tokens, _ = token_count(candidate, args.encoding)
    saved = src_tokens - cand_tokens
    pct = 0.0 if src_tokens == 0 else (saved / src_tokens) * 100

    atoms = [normalize_atom(atom) for atom in protected_atoms(source)]
    missing = [atom for atom in atoms if atom not in candidate]

    print(f"encoding_used: {encoding_used}")
    print(f"source_tokens: {src_tokens}")
    print(f"candidate_tokens: {cand_tokens}")
    print(f"saved_tokens: {saved}")
    print(f"saved_percent: {pct:.1f}")
    print(f"protected_atoms: {len(atoms)}")
    print(f"missing_atoms: {len(missing)}")

    if missing:
        print("missing_atom_samples:")
        for atom in missing[:20]:
            print(f"  - {atom}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
