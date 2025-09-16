# nlp_utils.py
import re
from typing import Tuple

# Primary explicit negative keywords
NEGATIVE_KEYWORDS = [
    r"\bno sponsorship\b",
    r"\bsponsorship not available\b",
    r"\bwe do not sponsor\b",
    r"\bunable to sponsor\b",
    r"\bcannot sponsor\b",
    r"\bno visa sponsorship\b",
    r"\bmust be authorized to work\b",
    r"\bUS citizens only\b",
    r"\bno H1B sponsorship\b",
    r"\bnot accepting candidates requiring sponsorship\b",
    r"\bemployer will not sponsor\b",
    r"\bmust currently be authorized\b",
]

# Positive-ish or ambiguous keywords that could indicate sponsorship willingness (or at least potential)
POSITIVE_KEYWORDS = [
    r"\bvisa sponsorship available\b",
    r"\bwill sponsor\b",
    r"\bH-1B\b",
    r"\bH1B\b",
    r"\bOPT\b",
    r"\bCPT\b",
    r"\bwork visa\b",
    r"\bauthorize sponsorship\b",
    r"\btransfer sponsorship\b",
    r"\bsponsor visas\b",
    r"\bsponsorship considered\b",
]

# Ambiguous phrases that require verification
AMBIGUOUS_KEYWORDS = [
    r"\bmust be authorized to work without sponsorship\b",
    r"\bmust be authorized to work for any employer\b",  # often used to say "we won't sponsor"
    r"\bauthorization to work in the U\.S\.\b",
]


def detect_sponsorship(text: str) -> Tuple[str, dict]:
    """
    Return a sponsorship classification and a diagnostic dict.
    classification: one of "no_sponsorship", "likely_sponsorship", "ambiguous", "unknown"
    """
    t = (text or "").lower()

    found_negative = []
    for pat in NEGATIVE_KEYWORDS:
        if re.search(pat, t):
            found_negative.append(pat)

    found_positive = []
    for pat in POSITIVE_KEYWORDS:
        if re.search(pat, t):
            found_positive.append(pat)

    found_ambiguous = []
    for pat in AMBIGUOUS_KEYWORDS:
        if re.search(pat, t):
            found_ambiguous.append(pat)

    # Decision logic (simple)
    if found_negative and not found_positive:
        classification = "no_sponsorship"
    elif found_positive and not found_negative:
        classification = "likely_sponsorship"
    elif found_positive and found_negative:
        classification = "ambiguous"
    elif found_ambiguous:
        classification = "ambiguous"
    else:
        classification = "unknown"

    diagnostic = {
        "negative_matches": found_negative,
        "positive_matches": found_positive,
        "ambiguous_matches": found_ambiguous,
    }
    return classification, diagnostic
