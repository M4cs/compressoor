#!/usr/bin/env python3
"""
Evaluate source -> packed -> unpacked preservation with simple local heuristics.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


PROTECTED_PATTERNS = [
    re.compile(r"```[\s\S]*?```"),
    re.compile(r"`[^`\n]+`"),
    re.compile(r"https?://[^\s)>\]]+"),
    re.compile(r"(?:\./|\../|/)?[\w.-]+(?:/[\w.-]+)+"),
    re.compile(r"\b[A-Z][A-Z0-9_]{1,}\b"),
    re.compile(r"\b\d+\.\d+(?:\.\d+)?\b"),
]
FACT_PATTERNS = {
    "api_contract_stable": [
        re.compile(r"\bdo not change (?:the )?api contract\b", re.I),
        re.compile(r"\bapi contract\b.*\b(stable|unchanged|same)\b", re.I),
        re.compile(r"\bno (?:api|contract) change\b", re.I),
        re.compile(r"\bapi stable\b", re.I),
    ],
    "error_message_exact": [
        re.compile(r"\berror message\b.*\b(exact|same|unchanged)\b", re.I),
        re.compile(r"\bkeep (?:the )?(?:current )?error message\b", re.I),
    ],
    "db_migration_blocked": [
        re.compile(r"\bdo not introduce (?:a )?(?:database )?migration\b", re.I),
        re.compile(r"\bno (?:db|database) mig(?:ration)?\b", re.I),
        re.compile(r"\bno migration\b", re.I),
    ],
    "boundary_test_required": [
        re.compile(r"\bboundary case\b", re.I),
        re.compile(r"\bboundary test\b", re.I),
        re.compile(r"\bupdate tests\b.*\bboundary\b", re.I),
    ],
    "auth_middleware_fix": [
        re.compile(r"\b(authentication|auth) middleware\b", re.I),
        re.compile(r"\bfix (?:the )?(?:authentication|auth) middleware\b", re.I),
    ],
    "payments_retry_helper": [
        re.compile(r"\bpayments? client\b", re.I),
        re.compile(r"\bretry logic\b.*\bsingle helper\b", re.I),
        re.compile(r"\bisolate retry logic\b", re.I),
    ],
    "payload_shape_stable": [
        re.compile(r"\brequest payload shapes\b", re.I),
        re.compile(r"\bpublic method names\b", re.I),
        re.compile(r"\bno change\b.*\bpayload\b", re.I),
    ],
    "retry_timeout_429_coverage": [
        re.compile(r"\btimeout\b", re.I),
        re.compile(r"\b429\b", re.I),
        re.compile(r"\bretry behavior\b", re.I),
        re.compile(r"\bunit coverage\b", re.I),
    ],
    "webhook_reconciliation_risk": [
        re.compile(r"\bwebhook reconciliation\b", re.I),
        re.compile(r"\berror wrapping\b", re.I),
        re.compile(r"\bmay depend on\b", re.I),
    ],
    "implemented_state": [
        re.compile(r"\bparser change is implemented\b", re.I),
        re.compile(r"\bimplemented in src/parser\.ts\b", re.I),
        re.compile(r"\bcurrent status\b.*\bimplemented\b", re.I),
        re.compile(r"\bcurrent status\b.*\bimplemented in src/[\w./-]+\b", re.I),
    ],
    "integration_tests_not_run": [
        re.compile(r"\bintegration tests (?:are )?not run yet\b", re.I),
        re.compile(r"\bintegration tests?\b.*\bnot run yet\b", re.I),
    ],
    "unit_tests_pass": [
        re.compile(r"\bunit tests pass\b", re.I),
        re.compile(r"\bunit tests?\b.*\bpass\b", re.I),
    ],
    "legacy_csv_risk": [
        re.compile(r"\blegacy csv imports\b", re.I),
        re.compile(r"\bdelimiter handling\b.*\bbreak\b", re.I),
    ],
    "next_steps_verify_fixture": [
        re.compile(r"\brun integration tests\b", re.I),
        re.compile(r"\bverify one old fixture\b", re.I),
        re.compile(r"\bbefore merging\b", re.I),
    ],
    "bun_scripts": [
        re.compile(r"\buses Bun for scripts\b", re.I),
        re.compile(r"\bBun\b.*\bscripts\b", re.I),
    ],
    "ripgrep_search": [
        re.compile(r"\bprefer ripgrep for search\b", re.I),
        re.compile(r"\bripgrep\b", re.I),
    ],
    "no_destructive_git": [
        re.compile(r"\bavoid destructive git commands\b", re.I),
        re.compile(r"\bgit reset --hard\b", re.I),
        re.compile(r"\bgit checkout --\b", re.I),
    ],
    "preserve_design_system": [
        re.compile(r"\bpreserve the existing design system\b", re.I),
        re.compile(r"\bdesign system\b", re.I),
        re.compile(r"\bfont stack\b", re.I),
    ],
}
STOP = {
    "the", "a", "an", "and", "or", "to", "for", "of", "in", "on", "is", "are",
    "be", "this", "that", "with", "without", "not", "do", "if", "we", "it",
    "as", "by", "at", "from", "but", "into", "than", "yet", "same",
}
WORD_RE = re.compile(r"\b[a-z][a-z0-9-]{2,}\b")
COMPARISON_RE = re.compile(r"(<=|>=|==|!=|<|>)")
COMPARISON_CANON = [
    (re.compile(r"\bless than or equal to\b", re.I), "<="),
    (re.compile(r"\bless than or equal\b", re.I), "<="),
    (re.compile(r"\bgreater than or equal to\b", re.I), ">="),
    (re.compile(r"\bgreater than or equal\b", re.I), ">="),
    (re.compile(r"\bless than\b", re.I), "<"),
    (re.compile(r"\bgreater than\b", re.I), ">"),
    (re.compile(r"\bequal to\b", re.I), "=="),
    (re.compile(r"\bnot equal to\b", re.I), "!="),
]


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def atoms(text: str) -> list[str]:
    out: list[str] = []
    seen = set()
    for pattern in PROTECTED_PATTERNS:
        for match in pattern.findall(text):
            if match not in seen:
                seen.add(match)
                out.append(match)
    return out


def normalize_atom(atom: str) -> str:
    return atom.strip().rstrip(".,;:")


def keywords(text: str) -> set[str]:
    return {
        word for word in WORD_RE.findall(text.lower())
        if word not in STOP
    }


def normalize_comparisons(text: str) -> str:
    result = text
    for pattern, replacement in COMPARISON_CANON:
        result = pattern.sub(replacement, result)
    return result


def semantic_facts(text: str) -> set[str]:
    facts = set()
    for fact_name, patterns in FACT_PATTERNS.items():
        if any(pattern.search(text) for pattern in patterns):
            facts.add(fact_name)
    for op in COMPARISON_RE.findall(normalize_comparisons(text.casefold())):
        facts.add(f"cmp:{op}")
    return facts


def run_unpack(packed_path: str, unpack_script: str) -> str:
    proc = subprocess.run(
        ["python3", unpack_script, packed_path],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def score(source: str, unpacked: str) -> tuple[float, float, float, list[str]]:
    src_atoms = [normalize_atom(atom) for atom in atoms(source)]
    unpacked_fold = unpacked.casefold()
    missing_atoms = [atom for atom in src_atoms if atom.casefold() not in unpacked_fold]
    atom_score = 1.0 if not src_atoms else 1 - (len(missing_atoms) / len(src_atoms))

    src_words = keywords(source)
    unpack_words = keywords(unpacked)
    word_score = 1.0 if not src_words else len(src_words & unpack_words) / len(src_words)

    src_facts = semantic_facts(source)
    unpack_facts = semantic_facts(unpacked)
    missing_facts = sorted(src_facts - unpack_facts)
    fact_weights = {
        "api_contract_stable": 3,
        "error_message_exact": 3,
        "db_migration_blocked": 3,
        "boundary_test_required": 2,
        "auth_middleware_fix": 2,
        "payments_retry_helper": 2,
        "payload_shape_stable": 2,
        "retry_timeout_429_coverage": 2,
        "webhook_reconciliation_risk": 2,
        "implemented_state": 2,
        "integration_tests_not_run": 3,
        "unit_tests_pass": 2,
        "legacy_csv_risk": 2,
        "next_steps_verify_fixture": 2,
        "bun_scripts": 2,
        "ripgrep_search": 2,
        "no_destructive_git": 3,
        "preserve_design_system": 3,
    }
    fact_weight = sum(fact_weights.get(fact, 1) for fact in src_facts)
    missing_weight = sum(fact_weights.get(fact, 1) for fact in missing_facts)
    fact_score = 1.0 if not src_facts else 1 - (missing_weight / fact_weight)

    return atom_score, word_score, fact_score, missing_facts


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CCM round-trip preservation.")
    parser.add_argument("source")
    parser.add_argument("packed")
    parser.add_argument(
        "--unpack-script",
        default=str(SKILL_ROOT / "scripts" / "unpack_ccm.py"),
    )
    args = parser.parse_args()

    source = read(args.source)
    unpacked = run_unpack(args.packed, args.unpack_script)
    atom_score, word_score, fact_score, missing_facts = score(source, unpacked)
    print(f"atom_score: {atom_score:.3f}")
    print(f"keyword_recall: {word_score:.3f}")
    print(f"semantic_fact_recall: {fact_score:.3f}")
    if missing_facts:
        print(f"missing_fact_count: {len(missing_facts)}")
        print("missing_fact_samples:")
        for fact in missing_facts[:10]:
            print(f"  - {fact}")
    roundtrip_ok = atom_score >= 1.0 and fact_score >= 0.90 and word_score >= 0.75
    print(f"roundtrip_ok: {'yes' if roundtrip_ok else 'review'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
