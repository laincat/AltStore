#!/usr/bin/env python3
"""Validate every client representation before publishing apps.json."""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse

TRACKS = {"stable", "alpha", "nightly", "local", "unknown"}
CRITICAL = ("version", "date", "downloadURL", "size", "minOSVersion", "buildVersion",
            "buildNumber", "releaseTag", "source", "publishedAt")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def https(value):
    if not text(value) or any(c.isspace() or ord(c) < 32 for c in value):
        return False
    try:
        u = urllib.parse.urlsplit(value)
        return (u.scheme == "https" and bool(u.hostname) and u.username is None
                and u.password is None and u.port in (None, 443)
                and bool(re.fullmatch(r"[A-Za-z0-9.-]+", u.hostname))
                and not u.hostname.startswith(".") and ".." not in u.hostname)
    except ValueError:
        return False


def identity(v):
    return tuple(v.get(k) for k in ("version", "buildVersion", "downloadURL", "releaseTag", "date"))


def fingerprint(v):
    return json.dumps({k: v.get(k) for k in CRITICAL}, sort_keys=True)


def validate(src, min_apps=1):
    errors = []
    def fail(where, message):
        errors.append("%s: %s" % (where, message))

    def release(v, where):
        if not isinstance(v, dict):
            fail(where, "release must be an object")
            return False
        for k in ("version", "date", "downloadURL", "minOSVersion"):
            if not text(v.get(k)):
                fail(where, "%s must be a nonempty string" % k)
        if not https(v.get("downloadURL")):
            fail(where, "downloadURL must have a valid HTTPS host")
        if type(v.get("size")) is not int or v["size"] <= 0:
            fail(where, "size must be a positive integer")
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v.get("date", ""))):
                raise ValueError()
            datetime.date.fromisoformat(v["date"])
        except (ValueError, TypeError):
            fail(where, "invalid calendar date")
        if "publishedAt" in v:
            try:
                stamp = datetime.datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00"))
                if stamp.tzinfo is None or stamp.date().isoformat() != v.get("date"):
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                fail(where, "publishedAt must be a timezone-aware timestamp matching date")
        for k in ("buildVersion", "buildNumber", "releaseTag", "source"):
            if k in v and not text(v[k]):
                fail(where, "%s must be a nonempty string" % k)
        if "source" in v and not https(v["source"]):
            fail(where, "invalid source URL")
        if "buildNumber" in v and v["buildNumber"] != v.get("buildVersion"):
            fail(where, "buildNumber differs from buildVersion")
        return True

    if not isinstance(src, dict):
        return ["source must be an object"]
    for k in ("name", "identifier"):
        if not text(src.get(k)):
            fail("source", "%s must be a nonempty string" % k)
    apps = src.get("apps")
    if not isinstance(apps, list):
        return errors + ["apps must be an array"]
    if len(apps) < min_apps:
        fail("source", "too few apps: %d < %d" % (len(apps), min_apps))
    seen = set()
    for index, a in enumerate(apps):
        where = "app[%d]" % index
        if not isinstance(a, dict):
            fail(where, "must be an object")
            continue
        for k in ("name", "bundleIdentifier", "developerName", "localizedDescription", "iconURL", "tintColor", "category"):
            if not text(a.get(k)):
                fail(where, "%s must be a nonempty string" % k)
        if not https(a.get("iconURL")):
            fail(where, "invalid iconURL")
        bid = a.get("bundleIdentifier")
        if text(bid):
            if bid in seen:
                fail(where, "duplicate bundleIdentifier")
            seen.add(bid)
        chans, flat = a.get("releaseChannels"), a.get("versions")
        if not isinstance(chans, list) or not chans or not isinstance(flat, list) or not flat:
            fail(where, "releaseChannels and versions must be nonempty arrays")
            continue
        tracks, all_releases, beta = [], [], []
        for c in chans:
            if not isinstance(c, dict):
                fail(where, "channel must be an object")
                continue
            track = c.get("track")
            if not isinstance(track, str) or track not in TRACKS:
                fail(where, "invalid track")
            tracks.append(str(track))
            rels = c.get("releases")
            if not isinstance(rels, list) or not rels:
                fail(where, "channel releases must be a nonempty array")
                continue
            valid = [v for v in rels if release(v, where)]
            if len({fingerprint(v) for v in valid}) != len(valid):
                fail(where, "duplicate channel release")
            all_releases.extend(valid)
            if track != "stable":
                beta.extend(valid)
        if len(set(tracks)) != len(tracks) or tracks.count("stable") != 1:
            fail(where, "tracks must be unique with exactly one stable")
        valid_flat = [v for v in flat if release(v, where)]
        if {fingerprint(v) for v in valid_flat} != {fingerprint(v) for v in all_releases}:
            fail(where, "flat/channel critical release payload mismatch")
        # JSON identities are safe even when malformed scalar values are containers.
        keys = [json.dumps(identity(v), sort_keys=True) for v in valid_flat]
        if len(keys) != len(set(keys)):
            fail(where, "duplicate flat release identity")
        if not errors:
            from build_source import sort_versions
            if valid_flat != sort_versions(valid_flat):
                fail(where, "versions are not ordered by timestamp/version/build")
        if "beta" in a and type(a["beta"]) is not bool:
            fail(where, "beta must be boolean")
        if valid_flat:
            expected = any(identity(valid_flat[0]) == identity(v) for v in beta)
            if bool(a.get("beta", False)) != expected:
                fail(where, "beta badge does not match first release identity")
        stable = next((c.get("releases") for c in chans if isinstance(c, dict) and c.get("track") == "stable"), [])
        if stable and isinstance(stable[0], dict):
            mapping = {"version": "version", "versionDate": "date", "downloadURL": "downloadURL",
                       "size": "size", "minOSVersion": "minOSVersion"}
            for old, new in mapping.items():
                if old in a and a[old] != stable[0].get(new):
                    fail(where, "legacy %s differs from stable head" % old)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=os.path.join(os.path.dirname(__file__), "..", "apps.json"))
    parser.add_argument("--min-apps", type=int, default=1)
    args = parser.parse_args()
    try:
        with open(args.file, encoding="utf-8") as stream:
            errors = validate(json.load(stream), args.min_apps)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("✗ " + error, file=sys.stderr)
    if not errors:
        print("✓ Source schema, identity and client payload validation passed")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
