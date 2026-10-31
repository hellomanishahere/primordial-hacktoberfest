"""Curated benchmark datasets for testing, evaluation, and instant demo loading."""
from __future__ import annotations

import re
from urllib.parse import urlsplit
from typing import Dict, List, Optional
from primordial.models import Discussion, Comment


SAMPLE_DISCUSSIONS: List[Dict] = [
    {
        "id": "gh:astral-sh/uv/issues/1042",
        "source_type": "github",
        "source_url": "https://github.com/astral-sh/uv/issues/1042",
        "title": "Decide on configuration file format: TOML vs YAML vs JSON",
        "description": "We need to finalize the configuration file format for project settings and dependency constraints. In python packaging, pyproject.toml is standard, but some contributors requested YAML for compatibility with existing CI templates. Let's debate the options and commit to a single standard.",
        "author": "charliermarsh",
        "created_at": "2024-03-12T14:20:00Z",
        "closed_at": "2024-03-15T18:30:00Z",
        "labels": ["rfc", "architecture", "configuration"],
        "metadata": {
            "repository": "astral-sh/uv",
            "issue_number": 1042,
            "stars": 42000,
            "target_files": ["pyproject.toml", "uv.toml", "crates/uv-settings/src/lib.rs"]
        },
        "comments": [
            {
                "id": "c-101",
                "author": "dev-contributor-alex",
                "created_at": "2024-03-12T15:10:00Z",
                "body": "I propose we use YAML (.uv.yaml). Almost all devops tools, GitHub Actions, and Kubernetes use YAML. Contributors are already familiar with the indentation syntax.",
                "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-101",
                "reply_to_id": None,
                "reactions": {"+1": 4, "-1": 8}
            },
            {
                "id": "c-102",
                "author": "security-auditor-eva",
                "created_at": "2024-03-12T16:45:00Z",
                "body": "I strongly object to YAML. YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers. Furthermore, the Norway problem ('NO' interpreted as boolean False) causes silent parsing bugs in configuration.",
                "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102",
                "reply_to_id": "c-101",
                "reactions": {"+1": 22, "heart": 5}
            },
            {
                "id": "c-103",
                "author": "frontend-dev-sam",
                "created_at": "2024-03-13T09:12:00Z",
                "body": "What about JSON? It has zero ambiguity, is supported natively in every programming language, and serde_json is blazing fast.",
                "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-103",
                "reply_to_id": None,
                "reactions": {"+1": 3, "-1": 12}
            },
            {
                "id": "c-104",
                "author": "maintainer-marcus",
                "created_at": "2024-03-13T10:30:00Z",
                "body": "JSON is disqualified because configuration files need comments. Forcing developers to maintain machine-only JSON with no comments for complex build options is a terrible developer experience.",
                "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104",
                "reply_to_id": "c-103",
                "reactions": {"+1": 35, "rocket": 10}
            },
            {
                "id": "c-105",
                "author": "charliermarsh",
                "created_at": "2024-03-14T11:00:00Z",
                "body": "I propose standardizing on TOML. It aligns with PEP 518/PEP 621 (pyproject.toml), has unambiguous typing, first-class comment support, and serde integrations in Rust are very mature. We will read from [tool.uv] in pyproject.toml and fallback to uv.toml.",
                "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-105",
                "reply_to_id": None,
                "reactions": {"+1": 48, "rocket": 15, "heart": 12}
            },
            {
                "id": "c-106",
                "author": "dev-contributor-alex",
                "created_at": "2024-03-14T14:20:00Z",
                "body": "Fair enough. Given the Python ecosystem conventions and security considerations Eva mentioned, TOML makes complete sense. I withdraw the YAML proposal.",
                "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-106",
                "reply_to_id": "c-105",
                "reactions": {"+1": 18, "eyes": 4}
            },
            {
                "id": "c-107",
                "author": "maintainer-marcus",
                "created_at": "2024-03-15T18:00:00Z",
                "body": "Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.",
                "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-107",
                "reply_to_id": None,
                "reactions": {"+1": 41, "hooray": 20}
            }
        ]
    },
    {
        "id": "dc:meta.discourse.org/t/embedded-cache-storage-engine/88219",
        "source_type": "discourse",
        "source_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219",
        "title": "Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)",
        "description": "We are designing the offline edge caching tier for distributed nodes. We need a fast, crash-resilient embedded store. The primary candidates are SQLite in WAL mode versus RocksDB. Let's review throughput, operational complexity, and binary footprint.",
        "author": "sam_saffron",
        "created_at": "2024-01-18T08:15:00Z",
        "closed_at": "2024-01-22T12:00:00Z",
        "labels": ["performance", "storage", "caching"],
        "metadata": {
            "discourse_instance": "meta.discourse.org",
            "topic_id": 88219,
            "category": "Architecture & Engineering",
            "target_files": ["lib/storage/edge_cache.rb", "config/storage.yml"]
        },
        "comments": [
            {
                "id": "post-201",
                "author": "dan_developer",
                "created_at": "2024-01-18T10:00:00Z",
                "body": "RocksDB provides LSM-tree architecture optimized for high write throughput. For edge telemetry ingestion, it will drastically outpace B-trees and avoid write amplification.",
                "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/2",
                "reply_to_id": None,
                "reactions": {"like": 6}
            },
            {
                "id": "post-202",
                "author": "sysadmin_claire",
                "created_at": "2024-01-18T14:30:00Z",
                "body": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
                "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3",
                "reply_to_id": "post-201",
                "reactions": {"like": 19}
            },
            {
                "id": "post-203",
                "author": "sam_saffron",
                "created_at": "2024-01-19T11:20:00Z",
                "body": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries. Furthermore, corruption recovery and backup tooling for SQLite is battle-tested over 20 years.",
                "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4",
                "reply_to_id": None,
                "reactions": {"like": 34}
            },
            {
                "id": "post-204",
                "author": "jeff_maintainer",
                "created_at": "2024-01-20T16:00:00Z",
                "body": "Agreed. RocksDB tuning parameters (memtable sizes, bloom filter bits, compaction threads) require a dedicated database engineer. SQLite 'just works' and fits in a 1MB embedded footprint.",
                "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/5",
                "reply_to_id": "post-203",
                "reactions": {"like": 28}
            },
            {
                "id": "post-205",
                "author": "sam_saffron",
                "created_at": "2024-01-22T11:45:00Z",
                "body": "Decision: We adopt SQLite in WAL mode. RocksDB is rejected due to excessive binary footprint (85MB), severe cross-compilation complexity on ARM, and maintenance overhead of LSM compaction tuning.",
                "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/6",
                "reply_to_id": None,
                "reactions": {"like": 42}
            }
        ]
    },
    {
        "id": "gh:encode/httpx/issues/780",
        "source_type": "github",
        "source_url": "https://github.com/encode/httpx/issues/780",
        "title": "Evaluate HTTP transport layer: Asyncio vs Trio native backend",
        "description": "We need to decide on our internal async transport abstraction. Should we maintain custom Trio and Curio backends or standardize on AnyIO as a unifying abstraction layer?",
        "author": "tomchristie",
        "created_at": "2023-11-05T12:00:00Z",
        "closed_at": "2023-11-08T15:00:00Z",
        "labels": ["rfc", "async", "networking"],
        "metadata": {
            "repository": "encode/httpx",
            "issue_number": 780,
            "stars": 14000,
            "target_files": ["httpx/_transports/default.py", "httpx/_transports/anyio.py"]
        },
        "comments": [
            {
                "id": "c-301",
                "author": "curio_advocate",
                "created_at": "2023-11-05T13:30:00Z",
                "body": "We should support native Curio alongside Asyncio. It provides the cleanest cooperative multitasking model in Python.",
                "url": "https://github.com/encode/httpx/issues/780#issuecomment-301",
                "reply_to_id": None,
                "reactions": {"+1": 2, "-1": 7}
            },
            {
                "id": "c-302",
                "author": "florimondmanca",
                "created_at": "2023-11-06T09:15:00Z",
                "body": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio. Maintaining a custom Curio transport branch is technical debt we cannot afford.",
                "url": "https://github.com/encode/httpx/issues/780#issuecomment-302",
                "reply_to_id": "c-301",
                "reactions": {"+1": 29}
            },
            {
                "id": "c-303",
                "author": "tomchristie",
                "created_at": "2023-11-07T14:00:00Z",
                "body": "Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.",
                "url": "https://github.com/encode/httpx/issues/780#issuecomment-303",
                "reply_to_id": None,
                "reactions": {"+1": 38, "rocket": 12}
            },
            {
                "id": "c-304",
                "author": "tomchristie",
                "created_at": "2023-11-08T14:45:00Z",
                "body": "Decision: Standardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.",
                "url": "https://github.com/encode/httpx/issues/780#issuecomment-304",
                "reply_to_id": None,
                "reactions": {"+1": 35}
            }
        ]
    },
    {
        "id": "dc:discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823",
        "source_type": "discourse",
        "source_url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823",
        "title": "PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)",
        "description": "Discussion on PEP 735 for standardizing dependency groups in pyproject.toml. We are debating whether development and lint dependencies should be specified in pyproject.toml or in external YAML / requirements files.",
        "author": "brettcannon",
        "created_at": "2024-01-15T10:00:00Z",
        "closed_at": "2024-02-01T16:00:00Z",
        "labels": ["pep", "packaging", "standards"],
        "metadata": {
            "discourse_instance": "discuss.python.org",
            "topic_id": 42823,
            "category": "Packaging",
            "target_files": ["pyproject.toml", "pip/_internal/req/req_file.py"]
        },
        "comments": [
            {
                "id": "post-401",
                "author": "ci_maintainer_dan",
                "created_at": "2024-01-15T12:00:00Z",
                "body": "Why not support external YAML files like dependencies.yaml? YAML is standard across GitHub Actions and GitLab CI matrices.",
                "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/2",
                "reply_to_id": None,
                "reactions": {"like": 3}
            },
            {
                "id": "post-402",
                "author": "pradyunsg",
                "created_at": "2024-01-15T15:30:00Z",
                "body": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
                "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3",
                "reply_to_id": "post-401",
                "reactions": {"like": 47}
            },
            {
                "id": "post-403",
                "author": "brettcannon",
                "created_at": "2024-01-16T09:00:00Z",
                "body": "Agreed. External YAML and non-standard requirements.txt fragments fracture project metadata. Having a single [dependency-groups] table in pyproject.toml provides clean standard tooling support.",
                "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/4",
                "reply_to_id": None,
                "reactions": {"like": 52}
            },
            {
                "id": "post-404",
                "author": "brettcannon",
                "created_at": "2024-02-01T15:45:00Z",
                "body": "Consensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.",
                "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/5",
                "reply_to_id": None,
                "reactions": {"like": 64}
            }
        ]
    }
]


def get_sample_discussions() -> List[Discussion]:
    """Return all sample discussions parsed into Discussion instances."""
    return [Discussion.from_dict(d) for d in SAMPLE_DISCUSSIONS]


def get_sample_discussion_by_id(discussion_id: str) -> Optional[Discussion]:
    """Find a sample discussion by id."""
    for d in SAMPLE_DISCUSSIONS:
        if d["id"] == discussion_id:
            return Discussion.from_dict(d)
    return None


def get_sample_discussion_by_url(url: str) -> Optional[Discussion]:
    """Return a fixture only when the URL identifies that exact benchmark item."""
    raw = url.strip()
    if not raw:
        return None
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/")

    github_match = re.fullmatch(r"/(?:([^/]+)/([^/]+))/(?:issues|pull)/(\d+)", path, re.IGNORECASE)
    if host in {"github.com", "www.github.com"} and github_match:
        owner, repo, number = github_match.groups()
        for d in SAMPLE_DISCUSSIONS:
            source = urlsplit(d["source_url"])
            match = re.fullmatch(r"/([^/]+)/([^/]+)/(?:issues|pull)/(\d+)", source.path.rstrip("/"), re.IGNORECASE)
            if match and source.hostname and source.hostname.lower() == host:
                if tuple(part.lower() for part in match.groups()[:2]) == (owner.lower(), repo.lower()) and match.group(3) == number:
                    return Discussion.from_dict(d)

    for d in SAMPLE_DISCUSSIONS:
        source = urlsplit(d["source_url"])
        if (source.hostname or "").lower() == host and source.path.rstrip("/").lower() == path.lower():
            return Discussion.from_dict(d)
    return None
