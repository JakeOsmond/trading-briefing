#!/usr/bin/env python3
"""Analyse calibration.jsonl — confidence tier accuracy vs verification verdicts.

Usage: python scripts/analyze-calibration.py [calibration.jsonl]

Produces a report showing:
- Accuracy by confidence tier (Very High → Very Low)
- Verification verdict distribution
- Findings with mismatched confidence vs verification
"""
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_entries(path):
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def analyze(entries):
    # Group by confidence tier
    by_tier = defaultdict(list)
    for e in entries:
        tier = e.get("confidence", "Unknown")
        by_tier[tier].append(e)

    tier_order = ["Very High", "High", "Medium", "Low", "Very Low", "Unknown"]

    print("=" * 60)
    print("CONFIDENCE CALIBRATION REPORT")
    print(f"Total entries: {len(entries)}")
    print(f"Date range: {entries[0]['date']} → {entries[-1]['date']}")
    print("=" * 60)

    print("\n## Accuracy by Confidence Tier\n")
    print(f"{'Tier':<15} {'Count':>6} {'Agreed':>8} {'Disputed':>10} {'Accuracy':>10}")
    print("-" * 55)

    for tier in tier_order:
        if tier not in by_tier:
            continue
        group = by_tier[tier]
        agreed = sum(1 for e in group if e.get("verification_verdict") in ("agree", "agree_with_caveat"))
        disputed = sum(1 for e in group if e.get("verification_verdict") == "disagree")
        no_verdict = sum(1 for e in group if e.get("verification_verdict") in ("none", "", None))
        total_verified = agreed + disputed
        accuracy = f"{agreed / total_verified * 100:.0f}%" if total_verified > 0 else "N/A"
        print(f"{tier:<15} {len(group):>6} {agreed:>8} {disputed:>10} {accuracy:>10}")

    print("\n## Verdict Distribution\n")
    verdict_counts = defaultdict(int)
    for e in entries:
        verdict_counts[e.get("verification_verdict", "none")] += 1
    for verdict, count in sorted(verdict_counts.items(), key=lambda x: -x[1]):
        print(f"  {verdict or 'none'}: {count}")

    # Flag mismatches: High/Very High confidence but disputed
    mismatches = [
        e for e in entries
        if e.get("confidence") in ("Very High", "High")
        and e.get("verification_verdict") == "disagree"
    ]
    if mismatches:
        print(f"\n## ⚠ High-Confidence Disputes ({len(mismatches)})\n")
        for e in mismatches:
            print(f"  {e['date']} | {e['driver'][:40]:<40} | {e['confidence']:<10} | concern: {e.get('verification_concern', 'N/A')[:60]}")

    # Flag: Low confidence but agreed
    underconfident = [
        e for e in entries
        if e.get("confidence") in ("Low", "Very Low")
        and e.get("verification_verdict") in ("agree", "agree_with_caveat")
    ]
    if underconfident:
        print(f"\n## 📈 Underconfident Findings ({len(underconfident)})\n")
        for e in underconfident:
            print(f"  {e['date']} | {e['driver'][:40]:<40} | {e['confidence']:<10} | verified correct")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "calibration.jsonl"
    if not Path(path).exists():
        print(f"No calibration data found at {path}")
        print("Calibration data is appended during each pipeline run.")
        print("Run the pipeline at least once, then re-run this script.")
        sys.exit(0)

    entries = load_entries(path)
    if not entries:
        print("Calibration file is empty.")
        sys.exit(0)

    analyze(entries)
