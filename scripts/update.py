#!/usr/bin/env python3
"""
IPTV Playlist Aggregator

Fetches channels from multiple M3U sources, deduplicates, curates,
and outputs a single clean M3U playlist.
"""

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests


@dataclass
class Channel:
    """Represents a single TV channel."""
    name: str = ""
    tvg_id: str = ""
    tvg_name: str = ""
    tvg_logo: str = ""
    group_title: str = ""
    country: str = ""
    url: str = ""
    original_source: str = ""

    def to_m3u_line(self) -> str:
        """Convert channel to M3U EXTINF line."""
        attrs = []
        if self.tvg_id:
            attrs.append(f'tvg-id="{self.tvg_id}"')
        if self.tvg_name:
            attrs.append(f'tvg-name="{self.tvg_name}"')
        if self.tvg_logo:
            attrs.append(f'tvg-logo="{self.tvg_logo}"')
        if self.group_title:
            attrs.append(f'group-title="{self.group_title}"')

        extinf = f'#EXTINF:-1 {" ".join(attrs)}, {self.name}'
        return f"{extinf}\n{self.url}"

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_source(url: str, timeout: int = 30) -> Optional[str]:
    """Download content from a URL."""
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "IPTV-Aggregator/1.0"
        })
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return None


def parse_m3u(content: str) -> list[Channel]:
    """Parse M3U content into a list of Channel objects."""
    channels = []
    lines = content.strip().split("\n")
    current_channel = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            # Parse EXTINF metadata
            current_channel = Channel()

            # Extract attributes using regex
            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
            tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
            tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            group_title_match = re.search(r'group-title="([^"]*)"', line)

            if tvg_id_match:
                current_channel.tvg_id = tvg_id_match.group(1)
            if tvg_name_match:
                current_channel.tvg_name = tvg_name_match.group(1)

            if tvg_logo_match:
                current_channel.tvg_logo = tvg_logo_match.group(1)
            if group_title_match:
                current_channel.group_title = group_title_match.group(1)

            # Extract channel name (after the last comma)
            comma_idx = line.rfind(",")
            if comma_idx != -1:
                current_channel.name = line[comma_idx + 1:].strip()
                # Remove color tags and other formatting
                current_channel.name = re.sub(r'\[/?COLOR\s+\w+\]', '', current_channel.name).strip()

            # Extract country from name if it has a country indicator
            country_match = re.search(r'\|\s*(CL|AR|UY|PE|CO|MX|EC|VE|PY|BO|PY|PA|CR|SV|HN|GT|NI|DO|CU|PR|US|WW|Mundo)', current_channel.name)
            if country_match:
                current_channel.country = country_match.group(1)

        elif line and not line.startswith("#") and current_channel:
            # This is the URL line
            current_channel.url = line
            current_channel.original_source = ""  # Set by caller
            channels.append(current_channel)
            current_channel = None

        i += 1

    return channels


def extract_country_from_group(group: str) -> str:
    """Try to extract country code from group title."""
    if not group:
        return ""

    group_upper = group.upper()
    country_map = {
        "CHILE": "CL", "CHILI": "CL", "ARGENTINA": "AR", "ARGENTIN": "AR",
        "URUGUAY": "UY", "PERU": "PE", "COLOMBIA": "CO",
        "MEXICO": "MX", "ECUADOR": "EC", "VENEZUELA": "VE",
        "PARAGUAY": "PY", "BOLIVIA": "BO", "PANAMA": "PA", "COSTA RICA": "CR",
        "EL SALVADOR": "SV", "HONDURAS": "HN", "GUATEMALA": "GT",
        "NICARAGUA": "NI", "REPUBLICA DOMINICANA": "DO", "CUBA": "CU",
        "PUERTO RICO": "PR", "USA": "US", "UNITED STATES": "US",
        "BRASIL": "BR", "BRAZIL": "BR", "WORLD": "WW", "MUNDO": "WW",
        "INTERNATIONAL": "WW",
    }

    for key, country_code in country_map.items():
        if key in group_upper:
            return country_code

    return ""


def is_placeholder(channel: Channel) -> bool:
    """Detect placeholder/separator entries (not real channels)."""
    name = channel.name.lower().strip()
    # Separator entries like "-Chile-", "-Brasil-", "-Actualizado..."
    if re.match(r'^-.*-$', name):
        return True
    if "actualizado" in name or "ultima" in name:
        return True
    if not channel.url or "imgur.com" in channel.url and channel.url.endswith(".mp4"):
        return True
    return False


def normalize_url(url: str) -> str:
    """Normalize a stream URL for deduplication (scheme+host+path, no query)."""
    if not url:
        return ""
    parsed = urlparse(url)
    # Strip query string and fragment; normalize scheme and host to lowercase
    return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"


def deduplicate(channels: list[Channel]) -> list[Channel]:
    """Remove duplicate channels by URL, keeping the best quality entry."""
    seen = {}
    duplicates_removed = 0

    for ch in channels:
        key = normalize_url(ch.url)

        if key and key in seen:
            duplicates_removed += 1
            existing = seen[key]
            if (ch.tvg_id and not existing.tvg_id) or \
               (ch.tvg_logo and not existing.tvg_logo) or \
               (ch.group_title and not existing.group_title):
                seen[key] = ch
        elif key:
            seen[key] = ch

    result = list(seen.values())
    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicates")

    return result


def normalize_key(name: str) -> str:
    """Create a normalized key for deduplication."""
    if not name:
        return ""
    key = name.lower().strip()
    # Strip resolution suffixes: (1080p), (720p), (576i), (2160p), (480p)...
    key = re.sub(r'\s*\(\d+[ip]\)', '', key)
    # Strip availability/geo tags: [Not 24/7], [Geo-blocked]
    key = re.sub(r'\s*\[.*?\]', '', key)
    key = re.sub(r'[^\w\s-]', '', key)
    key = re.sub(r'\s+', ' ', key)
    return key.strip()


def filter_channels(
    channels: list[Channel],
    country: Optional[str] = None,
    groups: Optional[list[str]] = None,
) -> list[Channel]:
    """Filter channels by country and/or group.

    Channels without a country are assigned to 'Other' group.
    If a default country is specified, only channels matching that country
    or 'Other' are included.
    """
    # Do not prefix groups with "Other" for channels without a country
    # Channels without country pass through unchanged

    result = channels

    if country:
        result = [ch for ch in result if ch.country == country or ch.country == ""]

    if groups and groups != ["all"]:
        result = [ch for ch in result if ch.group_title in groups]

    return result


def sort_channels(channels: list[Channel]) -> list[Channel]:
    """Sort channels by group, then by name."""
    return sorted(channels, key=lambda ch: (
        ch.group_title or "ZZZ",
        ch.name.lower()
    ))


def write_m3u(channels: list[Channel], output_path: str, epg_urls: list[str] = None):
    """Write channels to an M3U file."""
    with open(output_path, "w", encoding="utf-8") as f:
        header = "#EXTM3U"
        if epg_urls:
            header += f' url-tvg="{",".join(epg_urls)}"'
        f.write(header + "\n\n")
        for ch in channels:
            f.write(ch.to_m3u_line() + "\n\n")


def load_sources(config_path: str) -> dict:
    """Load sources configuration."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """Main aggregation pipeline."""
    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "configs" / "sources.json"
    output_path = base_dir / "output" / "playlist.m3u"

    # Load config
    config = load_sources(str(config_path))
    sources = [s for s in config["sources"] if s.get("enabled", True)]
    default_country = config.get("default_country", "CL")
    enabled_groups = config.get("enabled_groups", ["all"])
    epg_urls = config.get("epg_urls", [])
    streams = config.get("streams", [])

    # Load EPG mapping (tvg-name → tvg-id)
    epg_mapping_path = base_dir / "configs" / "epg-mapping.json"
    epg_mapping = {}
    if epg_mapping_path.exists():
        with open(epg_mapping_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            epg_mapping = {k: v for k, v in raw.items() if not k.startswith("_")}

    print(f"{'='*50}")
    print(f"  IPTV Playlist Aggregator")
    print(f"{'='*50}")
    print(f"  Sources:      {len(sources)}")
    print(f"  Default country: {default_country}")
    print(f"  EPG URLs:     {epg_urls or 'none'}")
    print(f"{'='*50}")
    print()

    # Fetch and parse all sources
    all_channels = []
    for source in sorted(sources, key=lambda s: s.get("priority", 99)):
        print(f"Fetching: {source['name']}")
        content = fetch_source(source["url"])
        if content is None:
            print(f"  Skipped (fetch failed)")
            continue

        channels = parse_m3u(content)
        # Set source name
        for ch in channels:
            ch.original_source = source["name"]

        # Extract country from group titles
        for ch in channels:
            if not ch.country and ch.group_title:
                ch.country = extract_country_from_group(ch.group_title)

        print(f"  Found {len(channels)} channels")
        all_channels.extend(channels)

    print(f"\nTotal channels fetched: {len(all_channels)}")

    # Add individual streams
    if streams:
        print(f"\nAdding {len(streams)} streams")
        for s in streams:
            ch = Channel(
                name=s["name"],
                tvg_name=s.get("tvg_name", s["name"]),
                tvg_logo=s.get("tvg_logo", ""),
                group_title=s.get("group_title", ""),
                country=s.get("country", ""),
                url=s["url"],
            )
            all_channels.append(ch)

    # Deduplicate
    all_channels = deduplicate(all_channels)
    print(f"After dedup: {len(all_channels)}")

    # Filter placeholders
    all_channels = [ch for ch in all_channels if not is_placeholder(ch)]
    print(f"After placeholder filter: {len(all_channels)}")

    # Filter by country
    filtered = filter_channels(all_channels, default_country, enabled_groups)
    print(f"After filtering: {len(filtered)}")

    # Apply EPG mapping to channels missing tvg-id
    mapped = 0
    for ch in all_channels:
        if not ch.tvg_id:
            ch.tvg_id = epg_mapping.get(ch.tvg_name) or epg_mapping.get(ch.name, "")
            if ch.tvg_id:
                mapped += 1
    if mapped:
        print(f"EPG mapping applied to {mapped} channels")

    # Sort
    filtered = sort_channels(filtered)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_m3u(filtered, str(output_path), epg_urls)
    print(f"\n{'='*50}")
    print(f"  Output:  {output_path}")
    print(f"  Channels: {len(filtered)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
