#!/usr/bin/env python3
"""
Scout v1: Conference Talk Format Discovery

Based on confirmed 2014 format:
- Paragraphs: <p data-aid="NNNNNNNN" id="pN">content</p>
- Sequential IDs: p1, p2, p3... (may have gaps)
- Speaker: <p class="author-name"> and <p class="author-role">
- API: /study/api/v3/language-pages/type/content?lang=eng&uri=/general-conference/{year}/{month}/{talk-id}

Purpose: Run against all years 2014-2025 to find format breakpoints.
"""

import requests
import re
import json
import time
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


@dataclass
class TalkProbeResult:
    """Result of probing a single talk."""
    year: int
    month: str  # "04" or "10"
    talk_uri: str
    success: bool

    # Format detection
    paragraph_count: int = 0
    paragraph_id_format: str = ""  # "sequential", "hash", "none", "mixed"
    sample_paragraph_ids: list = None
    has_data_aid: bool = False
    sample_data_aids: list = None

    # Speaker detection
    has_author_name: bool = False
    has_author_role: bool = False
    author_name_class: str = ""
    speaker_name: str = ""

    # Errors
    error: str = ""
    http_status: int = 0

    def __post_init__(self):
        if self.sample_paragraph_ids is None:
            self.sample_paragraph_ids = []
        if self.sample_data_aids is None:
            self.sample_data_aids = []


@dataclass
class ConferenceProbeResult:
    """Result of probing a conference."""
    year: int
    month: str
    talk_count: int = 0
    talk_uris: list = None
    sample_talk: Optional[TalkProbeResult] = None
    error: str = ""

    def __post_init__(self):
        if self.talk_uris is None:
            self.talk_uris = []


class ConferenceScout:
    """Scout for discovering conference talk formats."""

    BASE_URL = "https://www.churchofjesuschrist.org"
    API_PATH = "/study/api/v3/language-pages/type/content"

    def __init__(self, lang: str = "eng"):
        self.lang = lang
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Scripture-Search-Scout/1.0 (Educational Research)",
            "Accept": "application/json",
        })

    def fetch_conference_manifest(self, year: int, month: str) -> ConferenceProbeResult:
        """Fetch conference manifest to get list of talks."""
        result = ConferenceProbeResult(year=year, month=month)

        uri = f"/general-conference/{year}/{month}"
        url = f"{self.BASE_URL}{self.API_PATH}?lang={self.lang}&uri={uri}"

        try:
            resp = self.session.get(url, timeout=30)
            result.error = "" if resp.ok else f"HTTP {resp.status_code}"

            if not resp.ok:
                return result

            data = resp.json()
            body_html = data.get("content", {}).get("body", "")

            # Extract talk URIs from manifest
            # Pattern: href="/study/general-conference/YYYY/MM/TALKID?lang=eng"
            talk_pattern = rf'/study/general-conference/{year}/{month}/([^"?]+)'
            matches = re.findall(talk_pattern, body_html)

            # Dedupe while preserving order
            seen = set()
            talk_ids = []
            for m in matches:
                if m not in seen and not m.startswith("_"):  # Skip _manifest etc
                    seen.add(m)
                    talk_ids.append(m)

            result.talk_uris = talk_ids
            result.talk_count = len(talk_ids)

        except Exception as e:
            result.error = str(e)

        return result

    def fetch_talk(self, year: int, month: str, talk_id: str) -> TalkProbeResult:
        """Fetch and analyze a single talk."""
        uri = f"/general-conference/{year}/{month}/{talk_id}"
        result = TalkProbeResult(year=year, month=month, talk_uri=uri, success=False)

        url = f"{self.BASE_URL}{self.API_PATH}?lang={self.lang}&uri={uri}"

        try:
            resp = self.session.get(url, timeout=30)
            result.http_status = resp.status_code

            if not resp.ok:
                result.error = f"HTTP {resp.status_code}"
                return result

            data = resp.json()
            body_html = data.get("content", {}).get("body", "")

            if not body_html or len(body_html) < 500:
                result.error = "Body too short - likely manifest page"
                return result

            # Analyze paragraph structure
            self._analyze_paragraphs(body_html, result)

            # Analyze speaker metadata
            self._analyze_speaker(body_html, result)

            # Success if we found paragraphs
            result.success = result.paragraph_count > 5

        except json.JSONDecodeError as e:
            result.error = f"JSON parse error: {e}"
        except Exception as e:
            result.error = str(e)

        return result

    def _analyze_paragraphs(self, html: str, result: TalkProbeResult):
        """Analyze paragraph structure in HTML."""

        # Find all <p> tags with potential IDs
        # Pattern: <p ... id="XXX" ... data-aid="NNN" ...>
        p_pattern = r'<p[^>]*\bid=["\']([^"\']+)["\'][^>]*(?:data-aid=["\']([^"\']+)["\'])?[^>]*>'
        matches = re.findall(p_pattern, html)

        # Also try reverse order (data-aid before id)
        p_pattern_rev = r'<p[^>]*\bdata-aid=["\']([^"\']+)["\'][^>]*(?:id=["\']([^"\']+)["\'])?[^>]*>'
        matches_rev = re.findall(p_pattern_rev, html)

        # Combine and normalize: (id, data-aid) tuples
        all_matches = []
        for id_val, aid_val in matches:
            if id_val:
                all_matches.append((id_val, aid_val))
        for aid_val, id_val in matches_rev:
            if id_val and (id_val, aid_val) not in all_matches:
                all_matches.append((id_val, aid_val))

        result.paragraph_count = len(all_matches)

        if not all_matches:
            result.paragraph_id_format = "none"
            return

        # Sample first 5 IDs
        result.sample_paragraph_ids = [m[0] for m in all_matches[:5]]
        result.sample_data_aids = [m[1] for m in all_matches[:5] if m[1]]
        result.has_data_aid = bool(result.sample_data_aids)

        # Determine ID format
        sequential_pattern = re.compile(r'^p\d+$')
        hash_pattern = re.compile(r'^p_[a-zA-Z0-9]+$')

        sequential_count = sum(1 for id_val, _ in all_matches if sequential_pattern.match(id_val))
        hash_count = sum(1 for id_val, _ in all_matches if hash_pattern.match(id_val))

        if sequential_count > 0 and hash_count == 0:
            result.paragraph_id_format = "sequential"
        elif hash_count > 0 and sequential_count == 0:
            result.paragraph_id_format = "hash"
        elif sequential_count > 0 and hash_count > 0:
            result.paragraph_id_format = "mixed"
        else:
            result.paragraph_id_format = "other"

    def _analyze_speaker(self, html: str, result: TalkProbeResult):
        """Analyze speaker metadata in HTML."""

        # Look for author-name class
        author_name_match = re.search(
            r'<p[^>]*class=["\'][^"\']*author-name[^"\']*["\'][^>]*>([^<]+)</p>',
            html
        )
        if author_name_match:
            result.has_author_name = True
            result.author_name_class = "author-name"
            result.speaker_name = author_name_match.group(1).strip()

        # Look for author-role class
        if re.search(r'class=["\'][^"\']*author-role[^"\']*["\']', html):
            result.has_author_role = True

        # Try alternative: byline class
        if not result.has_author_name:
            byline_match = re.search(
                r'<(?:p|span)[^>]*class=["\'][^"\']*byline[^"\']*["\'][^>]*>([^<]+)',
                html
            )
            if byline_match:
                result.has_author_name = True
                result.author_name_class = "byline"
                result.speaker_name = byline_match.group(1).strip()

    def probe_all_conferences(self, start_year: int = 2014, end_year: int = 2025) -> list[ConferenceProbeResult]:
        """Probe all conferences in range."""
        results = []

        for year in range(start_year, end_year + 1):
            for month in ["04", "10"]:
                # Skip future conferences
                if year == 2025 and month == "10":
                    continue

                print(f"\n{'='*60}")
                print(f"Probing {year}/{month}...")

                # Get conference manifest
                conf_result = self.fetch_conference_manifest(year, month)

                if conf_result.error:
                    print(f"  ERROR: {conf_result.error}")
                    results.append(conf_result)
                    continue

                print(f"  Found {conf_result.talk_count} talks")

                # Probe first talk as sample
                if conf_result.talk_uris:
                    # Try to find a non-sustaining talk (usually 2nd or 3rd)
                    talk_idx = min(2, len(conf_result.talk_uris) - 1)
                    talk_id = conf_result.talk_uris[talk_idx]

                    print(f"  Sampling talk: {talk_id}")
                    time.sleep(0.5)  # Rate limit

                    talk_result = self.fetch_talk(year, month, talk_id)
                    conf_result.sample_talk = talk_result

                    if talk_result.success:
                        print(f"  SUCCESS: {talk_result.paragraph_count} paragraphs")
                        print(f"    ID format: {talk_result.paragraph_id_format}")
                        print(f"    Sample IDs: {talk_result.sample_paragraph_ids[:3]}")
                        print(f"    Has data-aid: {talk_result.has_data_aid}")
                        print(f"    Speaker: {talk_result.speaker_name}")
                    else:
                        print(f"  FAILED: {talk_result.error}")

                results.append(conf_result)
                time.sleep(0.5)  # Rate limit between conferences

        return results

    def generate_report(self, results: list[ConferenceProbeResult]) -> str:
        """Generate markdown report of findings."""
        lines = [
            "# Conference Format Scout Report",
            "",
            f"Scout version: v1 (2014 baseline)",
            f"Language: {self.lang}",
            f"Conferences probed: {len(results)}",
            "",
            "## Summary Table",
            "",
            "| Year | Month | Talks | Para Format | Para Count | Has data-aid | Speaker Class | Status |",
            "|------|-------|-------|-------------|------------|--------------|---------------|--------|",
        ]

        for conf in results:
            talk = conf.sample_talk
            if talk and talk.success:
                lines.append(
                    f"| {conf.year} | {conf.month} | {conf.talk_count} | "
                    f"{talk.paragraph_id_format} | {talk.paragraph_count} | "
                    f"{talk.has_data_aid} | {talk.author_name_class or 'none'} | OK |"
                )
            else:
                error = talk.error if talk else conf.error
                lines.append(
                    f"| {conf.year} | {conf.month} | {conf.talk_count} | "
                    f"- | - | - | - | FAIL: {error[:20]} |"
                )

        # Identify format transitions
        lines.extend([
            "",
            "## Format Transitions",
            "",
        ])

        prev_format = None
        for conf in results:
            if conf.sample_talk and conf.sample_talk.success:
                curr_format = conf.sample_talk.paragraph_id_format
                if prev_format and curr_format != prev_format:
                    lines.append(f"- **{conf.year}/{conf.month}**: Changed from `{prev_format}` to `{curr_format}`")
                prev_format = curr_format

        if not any("Changed" in line for line in lines):
            lines.append("- No format transitions detected")

        # Sample data section
        lines.extend([
            "",
            "## Sample Data",
            "",
        ])

        for conf in results:
            if conf.sample_talk and conf.sample_talk.success:
                talk = conf.sample_talk
                lines.extend([
                    f"### {conf.year}/{conf.month}",
                    f"- Talk: `{talk.talk_uri}`",
                    f"- Paragraph IDs: `{talk.sample_paragraph_ids}`",
                    f"- Data-aids: `{talk.sample_data_aids}`",
                    f"- Speaker: {talk.speaker_name}",
                    "",
                ])

        return "\n".join(lines)


def main():
    """Run the scout."""
    scout = ConferenceScout(lang="eng")

    print("Starting Conference Format Scout v1")
    print("Based on 2014 format assumptions")
    print("="*60)

    results = scout.probe_all_conferences(2014, 2025)

    # Generate and save report
    report = scout.generate_report(results)

    report_path = Path(__file__).parent.parent.parent / "planning" / "scout_v1_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)

    print(f"\n{'='*60}")
    print(f"Report saved to: {report_path}")

    # Also save raw JSON for further analysis
    json_path = report_path.with_suffix(".json")

    # Convert to serializable format
    raw_data = []
    for conf in results:
        conf_dict = {
            "year": conf.year,
            "month": conf.month,
            "talk_count": conf.talk_count,
            "talk_uris": conf.talk_uris[:5],  # First 5 only
            "error": conf.error,
        }
        if conf.sample_talk:
            conf_dict["sample_talk"] = asdict(conf.sample_talk)
        raw_data.append(conf_dict)

    json_path.write_text(json.dumps(raw_data, indent=2))
    print(f"Raw data saved to: {json_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print("="*60)

    success_count = sum(1 for r in results if r.sample_talk and r.sample_talk.success)
    fail_count = len(results) - success_count

    print(f"Successful probes: {success_count}")
    print(f"Failed probes: {fail_count}")

    # Show format distribution
    formats = {}
    for r in results:
        if r.sample_talk and r.sample_talk.success:
            fmt = r.sample_talk.paragraph_id_format
            formats[fmt] = formats.get(fmt, 0) + 1

    print(f"\nFormat distribution:")
    for fmt, count in formats.items():
        print(f"  {fmt}: {count} conferences")


if __name__ == "__main__":
    main()
