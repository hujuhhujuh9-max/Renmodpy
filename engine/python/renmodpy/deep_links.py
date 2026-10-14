"""Canonical links to saved Records; links never select code, files or saves."""

import re


def package_scheme(package):
    if not isinstance(package, str) or re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){2,}", package) is None:
        raise ValueError("Use the application's lowercase Android package.")
    # '+' is a valid URI scheme character; '_' is not. Android packages
    # cannot contain '+', so this conversion preserves their identities.
    return package.replace("_", "+")


def record_uri(package, identifier):
    if not isinstance(identifier, str) or re.fullmatch(r"[0-9a-f]{32}", identifier) is None:
        raise ValueError("Choose a saved Record identifier.")
    return package_scheme(package) + "://records/" + identifier


def parse_record_uri(uri, package):
    """Return the exact Record ID, or None for any other URI (no decoding)."""
    if not isinstance(uri, str) or len(uri) > 256:
        return None
    match = re.fullmatch(re.escape(package_scheme(package)) + r"://records/([0-9a-f]{32})", uri)
    return match.group(1) if match else None
