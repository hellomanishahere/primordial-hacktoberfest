"""Unit tests for GitHub URL Parser."""

import pytest
from app.core.exceptions import InvalidGitHubURLException
from app.github.parser import (
    GitHubResourceType,
    GitHubTarget,
    parse_github_url,
)


def test_valid_issue_url():
    url = "https://github.com/nodejs/node/issues/41749"
    target = parse_github_url(url)
    assert target.owner == "nodejs"
    assert target.repo == "node"
    assert target.entity_type == "issues"
    assert target.entity_number == 41749
    assert target.resource_type == GitHubResourceType.ISSUE
    assert target.is_issue is True
    assert target.is_pull_request is False
    assert target.repository == "nodejs/node"


def test_valid_pull_request_url():
    url = "https://github.com/facebook/react/pull/12345"
    target = parse_github_url(url)
    assert target.owner == "facebook"
    assert target.repo == "react"
    assert target.entity_type == "pull"
    assert target.entity_number == 12345
    assert target.resource_type == GitHubResourceType.PULL_REQUEST
    assert target.is_pull_request is True
    assert target.is_issue is False
    assert target.repository == "facebook/react"


def test_url_with_trailing_slash():
    url = "https://github.com/pallets/flask/pull/500/"
    target = parse_github_url(url)
    assert target.owner == "pallets"
    assert target.repo == "flask"
    assert target.entity_number == 500


def test_url_with_query_parameters_and_fragment():
    url = "https://github.com/django/django/pull/999?expanded=1&diff=unified#issuecomment-888"
    target = parse_github_url(url)
    assert target.owner == "django"
    assert target.repo == "django"
    assert target.entity_number == 999


def test_url_with_www_subdomain():
    url = "https://www.github.com/torvalds/linux/pull/1"
    target = parse_github_url(url)
    assert target.owner == "torvalds"
    assert target.repo == "linux"
    assert target.entity_number == 1


def test_url_with_http_scheme():
    url = "http://github.com/rust-lang/rust/issues/100"
    target = parse_github_url(url)
    assert target.owner == "rust-lang"
    assert target.repo == "rust"
    assert target.entity_number == 100


def test_url_with_dot_git_suffix():
    url = "https://github.com/torvalds/linux.git/pull/42"
    target = parse_github_url(url)
    assert target.repo == "linux"
    assert target.entity_number == 42


def test_reject_unsupported_host():
    with pytest.raises(InvalidGitHubURLException) as exc_info:
        parse_github_url("https://gitlab.com/owner/repo/issues/123")
    assert "Unsupported hostname" in exc_info.value.message
    assert exc_info.value.status_code == 400


def test_reject_unsupported_scheme():
    with pytest.raises(InvalidGitHubURLException) as exc_info:
        parse_github_url("ftp://github.com/owner/repo/issues/123")
    assert "Unsupported URL scheme" in exc_info.value.message


def test_reject_subdomain_spoofing():
    with pytest.raises(InvalidGitHubURLException) as exc_info:
        parse_github_url("https://evil-github.com/owner/repo/pull/1")
    assert "Unsupported hostname" in exc_info.value.message


def test_reject_empty_or_none():
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url("")
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url(None)  # type: ignore


def test_reject_malformed_path():
    # Missing entity number
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url("https://github.com/owner/repo/pull/")
    # Missing entity type
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url("https://github.com/owner/repo/123")
    # Unsupported resource (e.g. commits, releases)
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url("https://github.com/owner/repo/commit/abc1234")


def test_reject_invalid_entity_number():
    # Negative number
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url("https://github.com/owner/repo/issues/-10")
    # Zero
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url("https://github.com/owner/repo/issues/0")
    # Non-numeric string
    with pytest.raises(InvalidGitHubURLException):
        parse_github_url("https://github.com/owner/repo/issues/abc")

