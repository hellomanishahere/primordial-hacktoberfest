"""Bot identification and noise pattern definitions."""

import re
from typing import Optional, Set

# Known bot account logins (case-insensitive exact match)
KNOWN_BOT_ACCOUNTS: Set[str] = {
    "dependabot",
    "codecov",
    "stale",
    "github-actions",
    "greenkeeper",
    "renovate",
    "sonarcloud",
    "lgtm-com",
    "semantic-release-bot",
    "snyk-bot",
    "imgbot",
    "allcontributors",
    "coveralls",
    "mergify",
    "bors",
    "homu",
    "cla-assistant",
    "restyled-io",
    "web-flow",
}

# Regex for detecting bot suffixes
BOT_SUFFIX_REGEX = re.compile(r"\[bot\]$", re.IGNORECASE)

# Standalone reaction emoji and text patterns (+1, -1, :thumbsup:, 👍, etc.)
STANDALONE_REACTION_REGEX = re.compile(
    r"^[\s\r\n]*("
    r"\+1|-1|\+100|"
    r":\+1:|:-1:|:thumbsup:|:thumbsdown:|:heart:|:tada:|:rocket:|:eyes:|:smile:|:laughing:|:white_check_mark:|:heavy_check_mark:|:clap:|:pray:|:100:|"
    r"[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\U00002702-\U000027B0\U000024C2-\U0001F251\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]"
    r")[\s\r\n!.]*$",
    re.UNICODE | re.IGNORECASE,
)

# Automated CI/CD and bot notification signatures
CI_NOTIFICATION_PATTERNS = [
    re.compile(r"^\s*<!--\s*ci-comment\s*-->", re.IGNORECASE),
    re.compile(r"##\s*\[Codecov\]\(https://codecov\.io", re.IGNORECASE),
    re.compile(r"###\s*\[SonarQube\]|Quality Gate (passed|failed)", re.IGNORECASE),
    re.compile(r"Coverage\s*report:\s*\d+(\.\d+)?%", re.IGNORECASE),
    re.compile(r"\|\s*Impacted Files\s*\|\s*Coverage Δ\s*\|", re.IGNORECASE),
    re.compile(r"<!--\s*sticky-pull-request-comment\s*-->", re.IGNORECASE),
    re.compile(r"^\s*All checks have (passed|failed)", re.IGNORECASE),
    re.compile(r"^\s*Azure Pipelines successfully (started|completed)", re.IGNORECASE),
    re.compile(r"^\s*Build\s+#?\d+\s+(succeeded|passed|failed)", re.IGNORECASE),
    re.compile(r"^\s*KICS scan summary", re.IGNORECASE),
]

# Mobile email / client signature patterns
MOBILE_SIGNATURE_PATTERNS = [
    re.compile(r"(?:^|\n)\s*(?:--\s*\n)?\s*Sent from my (?:iPhone|iPad|Android|mobile|Galaxy|phone|handheld)[^\n]*\s*$", re.IGNORECASE),
    re.compile(r"(?:^|\n)\s*(?:--\s*\n)?\s*Get Outlook for (?:iOS|Android)[^\n]*\s*$", re.IGNORECASE),
]

# HTML comment blocks
HTML_COMMENT_REGEX = re.compile(r"<!--[\s\S]*?-->")

# Excessive consecutive blank lines (3 or more newlines)
EXCESSIVE_NEWLINES_REGEX = re.compile(r"\n{3,}")


def is_bot_author(author: Optional[str], author_association: Optional[str] = None) -> bool:
    """
    Determines if an author is a known bot or automated service.

    Precise rules:
    - Ends with '[bot]' (e.g. 'dependabot[bot]')
    - Exact match in KNOWN_BOT_ACCOUNTS (e.g. 'codecov', 'stale')
    - Author association explicitly flagged as 'BOT' by GitHub API

    Human maintainers whose names happen to contain the substring 'bot'
    (such as 'abbot', 'robotics', 'talbot', 'botanist') are NOT classified as bots.
    """
    if not author or not isinstance(author, str):
        return False

    clean_author = author.strip()
    lower_author = clean_author.lower()

    # Explicit GitHub author association
    if author_association and author_association.upper() == "BOT":
        return True

    # Ends in [bot]
    if BOT_SUFFIX_REGEX.search(clean_author):
        return True

    # Exact match in known bot list
    if lower_author in KNOWN_BOT_ACCOUNTS:
        return True

    return False

