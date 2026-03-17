#!/usr/bin/env python3
"""Analyse which investigation tracks contribute to material findings.

Scans briefing markdown files to identify which tracks are cited in findings.
Tracks that never surface findings are candidates for pruning or replacement.

Usage: python scripts/track-contribution.py [briefings_dir]
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


# The 23 track IDs from domains/insurance/tracks.py
TRACK_IDS = [
    "channel_product_mix", "scheme_performance", "medical_profile",
    "cover_level_mix", "commission_partners", "discount_impact",
    "booking_source_device", "customer_age_band", "trip_duration_band",
    "days_to_travel", "seasonal_daily", "renewal_volume", "renewal_rate",
    "web_device_scheme_gp", "web_funnel_dropoff", "web_annual_single_conversion",
    "web_multi_search_impact", "web_medical_screening", "web_cover_level_outcome",
    "web_session_depth_outcome", "cost_decomposition", "conversion_gp_bridge",
    "customer_type_deep",
]


def analyze_briefings(briefings_dir):
    md_files = sorted(Path(briefings_dir).glob("2*.md"))
    if not md_files:
        print(f"No briefing markdown files found in {briefings_dir}")
        return

    track_mentions = defaultdict(int)
    total_briefings = 0

    # Also check HTML files which contain the investigation trail with track names
    html_files = sorted(Path(briefings_dir).glob("2*.html"))

    for md_file in md_files:
        content = md_file.read_text().lower()
        # Find matching HTML file for investigation trail data
        html_match = Path(briefings_dir) / (md_file.stem + ".html")
        if html_match.exists():
            content += html_match.read_text().lower()
        total_briefings += 1
        for track_id in TRACK_IDS:
            # Check multiple name variants
            readable = track_id.replace("_", " ")
            # Also try the track 'name' field style (e.g., "Channel × Product Matrix")
            variants = [track_id, readable]
            if any(v in content for v in variants):
                track_mentions[track_id] += 1

    print("=" * 60)
    print("INVESTIGATION TRACK CONTRIBUTION REPORT")
    print(f"Briefings analysed: {total_briefings}")
    print(f"Date range: {md_files[0].stem} → {md_files[-1].stem}")
    print("=" * 60)

    print(f"\n{'Track':<35} {'Mentions':>10} {'Hit Rate':>10}")
    print("-" * 58)

    for track_id in TRACK_IDS:
        count = track_mentions.get(track_id, 0)
        rate = f"{count / total_briefings * 100:.0f}%" if total_briefings > 0 else "N/A"
        flag = "  ⚠ never cited" if count == 0 else ""
        print(f"{track_id:<35} {count:>10} {rate:>10}{flag}")

    zero_tracks = [t for t in TRACK_IDS if track_mentions.get(t, 0) == 0]
    if zero_tracks:
        print(f"\n## Tracks that never contributed ({len(zero_tracks)}):")
        for t in zero_tracks:
            print(f"  - {t}")
        print("\nConsider: are these tracks querying the right dimensions?")
        print("They may be returning data that the AI never finds material.")


if __name__ == "__main__":
    briefings_dir = sys.argv[1] if len(sys.argv) > 1 else "briefings"
    analyze_briefings(briefings_dir)
