/**
 * PRIMORDIAL — Frontend Application Logic
 * Supports both Live Python Backend (http://) and Standalone Offline Execution (file://)
 */
const OFFLINE_BUNDLE = {
  "samples": [
    {
      "id": "gh:astral-sh/uv/issues/1042",
      "source_type": "github",
      "source_url": "https://github.com/astral-sh/uv/issues/1042",
      "title": "Decide on configuration file format: TOML vs YAML vs JSON",
      "description": "We need to finalize the configuration file format for project settings and dependency constraints. In python packaging, pyproject.toml is standard, but some contributors requested YAML for compatibility with existing CI templates. Let's debate the options and commit to a single standard.",
      "author": "charliermarsh",
      "created_at": "2024-03-12T14:20:00Z",
      "closed_at": "2024-03-15T18:30:00Z",
      "labels": [
        "rfc",
        "architecture",
        "configuration"
      ],
      "metadata": {
        "repository": "astral-sh/uv",
        "issue_number": 1042,
        "stars": 42000,
        "target_files": [
          "pyproject.toml",
          "uv.toml",
          "crates/uv-settings/src/lib.rs"
        ]
      },
      "comments": [
        {
          "id": "c-101",
          "author": "dev-contributor-alex",
          "created_at": "2024-03-12T15:10:00Z",
          "body": "I propose we use YAML (.uv.yaml). Almost all devops tools, GitHub Actions, and Kubernetes use YAML. Contributors are already familiar with the indentation syntax.",
          "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-101",
          "reply_to_id": null,
          "reactions": {
            "+1": 4,
            "-1": 8
          }
        },
        {
          "id": "c-102",
          "author": "security-auditor-eva",
          "created_at": "2024-03-12T16:45:00Z",
          "body": "I strongly object to YAML. YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers. Furthermore, the Norway problem ('NO' interpreted as boolean False) causes silent parsing bugs in configuration.",
          "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102",
          "reply_to_id": "c-101",
          "reactions": {
            "+1": 22,
            "heart": 5
          }
        },
        {
          "id": "c-103",
          "author": "frontend-dev-sam",
          "created_at": "2024-03-13T09:12:00Z",
          "body": "What about JSON? It has zero ambiguity, is supported natively in every programming language, and serde_json is blazing fast.",
          "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-103",
          "reply_to_id": null,
          "reactions": {
            "+1": 3,
            "-1": 12
          }
        },
        {
          "id": "c-104",
          "author": "maintainer-marcus",
          "created_at": "2024-03-13T10:30:00Z",
          "body": "JSON is disqualified because configuration files need comments. Forcing developers to maintain machine-only JSON with no comments for complex build options is a terrible developer experience.",
          "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104",
          "reply_to_id": "c-103",
          "reactions": {
            "+1": 35,
            "rocket": 10
          }
        },
        {
          "id": "c-105",
          "author": "charliermarsh",
          "created_at": "2024-03-14T11:00:00Z",
          "body": "I propose standardizing on TOML. It aligns with PEP 518/PEP 621 (pyproject.toml), has unambiguous typing, first-class comment support, and serde integrations in Rust are very mature. We will read from [tool.uv] in pyproject.toml and fallback to uv.toml.",
          "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-105",
          "reply_to_id": null,
          "reactions": {
            "+1": 48,
            "rocket": 15,
            "heart": 12
          }
        },
        {
          "id": "c-106",
          "author": "dev-contributor-alex",
          "created_at": "2024-03-14T14:20:00Z",
          "body": "Fair enough. Given the Python ecosystem conventions and security considerations Eva mentioned, TOML makes complete sense. I withdraw the YAML proposal.",
          "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-106",
          "reply_to_id": "c-105",
          "reactions": {
            "+1": 18,
            "eyes": 4
          }
        },
        {
          "id": "c-107",
          "author": "maintainer-marcus",
          "created_at": "2024-03-15T18:00:00Z",
          "body": "Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.",
          "url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-107",
          "reply_to_id": null,
          "reactions": {
            "+1": 41,
            "hooray": 20
          }
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
      "labels": [
        "performance",
        "storage",
        "caching"
      ],
      "metadata": {
        "discourse_instance": "meta.discourse.org",
        "topic_id": 88219,
        "category": "Architecture & Engineering",
        "target_files": [
          "lib/storage/edge_cache.rb",
          "config/storage.yml"
        ]
      },
      "comments": [
        {
          "id": "post-201",
          "author": "dan_developer",
          "created_at": "2024-01-18T10:00:00Z",
          "body": "RocksDB provides LSM-tree architecture optimized for high write throughput. For edge telemetry ingestion, it will drastically outpace B-trees and avoid write amplification.",
          "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/2",
          "reply_to_id": null,
          "reactions": {
            "like": 6
          }
        },
        {
          "id": "post-202",
          "author": "sysadmin_claire",
          "created_at": "2024-01-18T14:30:00Z",
          "body": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
          "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3",
          "reply_to_id": "post-201",
          "reactions": {
            "like": 19
          }
        },
        {
          "id": "post-203",
          "author": "sam_saffron",
          "created_at": "2024-01-19T11:20:00Z",
          "body": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries. Furthermore, corruption recovery and backup tooling for SQLite is battle-tested over 20 years.",
          "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4",
          "reply_to_id": null,
          "reactions": {
            "like": 34
          }
        },
        {
          "id": "post-204",
          "author": "jeff_maintainer",
          "created_at": "2024-01-20T16:00:00Z",
          "body": "Agreed. RocksDB tuning parameters (memtable sizes, bloom filter bits, compaction threads) require a dedicated database engineer. SQLite 'just works' and fits in a 1MB embedded footprint.",
          "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/5",
          "reply_to_id": "post-203",
          "reactions": {
            "like": 28
          }
        },
        {
          "id": "post-205",
          "author": "sam_saffron",
          "created_at": "2024-01-22T11:45:00Z",
          "body": "Decision: We adopt SQLite in WAL mode. RocksDB is rejected due to excessive binary footprint (85MB), severe cross-compilation complexity on ARM, and maintenance overhead of LSM compaction tuning.",
          "url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/6",
          "reply_to_id": null,
          "reactions": {
            "like": 42
          }
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
      "labels": [
        "rfc",
        "async",
        "networking"
      ],
      "metadata": {
        "repository": "encode/httpx",
        "issue_number": 780,
        "stars": 14000,
        "target_files": [
          "httpx/_transports/default.py",
          "httpx/_transports/anyio.py"
        ]
      },
      "comments": [
        {
          "id": "c-301",
          "author": "curio_advocate",
          "created_at": "2023-11-05T13:30:00Z",
          "body": "We should support native Curio alongside Asyncio. It provides the cleanest cooperative multitasking model in Python.",
          "url": "https://github.com/encode/httpx/issues/780#issuecomment-301",
          "reply_to_id": null,
          "reactions": {
            "+1": 2,
            "-1": 7
          }
        },
        {
          "id": "c-302",
          "author": "florimondmanca",
          "created_at": "2023-11-06T09:15:00Z",
          "body": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio. Maintaining a custom Curio transport branch is technical debt we cannot afford.",
          "url": "https://github.com/encode/httpx/issues/780#issuecomment-302",
          "reply_to_id": "c-301",
          "reactions": {
            "+1": 29
          }
        },
        {
          "id": "c-303",
          "author": "tomchristie",
          "created_at": "2023-11-07T14:00:00Z",
          "body": "Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.",
          "url": "https://github.com/encode/httpx/issues/780#issuecomment-303",
          "reply_to_id": null,
          "reactions": {
            "+1": 38,
            "rocket": 12
          }
        },
        {
          "id": "c-304",
          "author": "tomchristie",
          "created_at": "2023-11-08T14:45:00Z",
          "body": "Decision: Standardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.",
          "url": "https://github.com/encode/httpx/issues/780#issuecomment-304",
          "reply_to_id": null,
          "reactions": {
            "+1": 35
          }
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
      "labels": [
        "pep",
        "packaging",
        "standards"
      ],
      "metadata": {
        "discourse_instance": "discuss.python.org",
        "topic_id": 42823,
        "category": "Packaging",
        "target_files": [
          "pyproject.toml",
          "pip/_internal/req/req_file.py"
        ]
      },
      "comments": [
        {
          "id": "post-401",
          "author": "ci_maintainer_dan",
          "created_at": "2024-01-15T12:00:00Z",
          "body": "Why not support external YAML files like dependencies.yaml? YAML is standard across GitHub Actions and GitLab CI matrices.",
          "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/2",
          "reply_to_id": null,
          "reactions": {
            "like": 3
          }
        },
        {
          "id": "post-402",
          "author": "pradyunsg",
          "created_at": "2024-01-15T15:30:00Z",
          "body": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
          "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3",
          "reply_to_id": "post-401",
          "reactions": {
            "like": 47
          }
        },
        {
          "id": "post-403",
          "author": "brettcannon",
          "created_at": "2024-01-16T09:00:00Z",
          "body": "Agreed. External YAML and non-standard requirements.txt fragments fracture project metadata. Having a single [dependency-groups] table in pyproject.toml provides clean standard tooling support.",
          "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/4",
          "reply_to_id": null,
          "reactions": {
            "like": 52
          }
        },
        {
          "id": "post-404",
          "author": "brettcannon",
          "created_at": "2024-02-01T15:45:00Z",
          "body": "Consensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.",
          "url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/5",
          "reply_to_id": null,
          "reactions": {
            "like": 64
          }
        }
      ]
    }
  ],
  "decisions": [
    {
      "id": "ADR-1042",
      "discussion_id": "gh:astral-sh/uv/issues/1042",
      "title": "ADR-1042: Standardize on TOML Configuration Format",
      "status": "Accepted",
      "date": "2024-03-15",
      "context": "Project settings, CLI arguments, and dependency constraints require a robust, standardized configuration file format.",
      "problem_statement": "Engineering evaluation and decision required for: Decide on configuration file format: TOML vs YAML vs JSON",
      "decision_outcome": "We commit to TOML as the single official configuration file format. Settings will be parsed from [tool.uv] in pyproject.toml with fallback to standalone uv.toml.",
      "accepted_option": "Standardize on TOML configuration format (pyproject.toml / uv.toml)",
      "considered_options": [
        "TOML Configuration Format",
        "YAML Configuration Format",
        "JSON Configuration Format"
      ],
      "rejected_alternatives": [
        {
          "name": "YAML Configuration (.uv.yaml)",
          "proposer": "dev-contributor-alex",
          "rejection_reasons": [
            "Severe security risks and arbitrary code execution CVEs in standard YAML parsers",
            "Norway problem ('NO' interpreted as boolean False) causing silent configuration errors",
            "Complex indentation rules causing formatting bugs across environments"
          ],
          "key_objection_quote": "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
          "objection_author": "security-auditor-eva",
          "comment_id": "c-102",
          "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102"
        },
        {
          "name": "JSON Configuration",
          "proposer": "frontend-dev-sam",
          "rejection_reasons": [
            "Strict lack of comments prevents documenting complex build and packaging settings",
            "Trailing commas and strict syntax make human manual editing prone to syntax errors"
          ],
          "key_objection_quote": "JSON is disqualified because configuration files need comments.",
          "objection_author": "maintainer-marcus",
          "comment_id": "c-104",
          "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104"
        }
      ],
      "consequences_positive": [
        "Strict alignment with Python packaging standards PEP 518 and PEP 621",
        "First-class comment support allows developers to document settings directly inline",
        "Unambiguous typing prevents type coercion security bugs common in YAML",
        "High-performance serde deserialization in Rust via toml-rs"
      ],
      "consequences_negative": [
        "DevOps engineers accustomed to YAML will need minor syntax adjustment",
        "Multi-line strings have specific syntax compared to YAML blocks"
      ],
      "affected_components": [
        "pyproject.toml",
        "uv.toml",
        "crates/uv-settings/*",
        "crates/uv-configuration/*",
        "config/loader.py",
        "config.py",
        "crates/uv-settings/src/lib.rs"
      ],
      "evidence_quotes": [
        {
          "id": "eq-1",
          "quote": "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
          "author": "security-auditor-eva",
          "comment_id": "c-102",
          "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102",
          "verified": true,
          "confidence": 1.0,
          "context": "I strongly object to YAML. YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers. Furthermore, the Norway problem ('NO' i...",
          "char_offset": 27
        },
        {
          "id": "eq-2",
          "quote": "JSON is disqualified because configuration files need comments.",
          "author": "maintainer-marcus",
          "comment_id": "c-104",
          "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104",
          "verified": true,
          "confidence": 1.0,
          "context": "JSON is disqualified because configuration files need comments. Forcing developers to maintain machine-...",
          "char_offset": 0
        },
        {
          "id": "eq-3",
          "quote": "Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.",
          "author": "maintainer-marcus",
          "comment_id": "c-107",
          "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-107",
          "verified": true,
          "confidence": 1.0,
          "context": "Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.",
          "char_offset": 0
        }
      ],
      "madr_content": "# ADR-1042: Standardize on TOML Configuration Format\n\n* Status: **Accepted**\n* Date: 2024-03-15\n* Deciders: @charliermarsh, @dev-contributor-alex, @frontend-dev-sam, @maintainer-marcus, @security-auditor-eva\n* Source Discussion: [Decide on configuration file format: TOML vs YAML vs JSON](https://github.com/astral-sh/uv/issues/1042)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: Decide on configuration file format: TOML vs YAML vs JSON\n\nProject settings, CLI arguments, and dependency constraints require a robust, standardized configuration file format.\n\n## Considered Options\n\n* TOML Configuration Format *(Chosen)*\n* YAML Configuration Format *(Rejected)*\n* JSON Configuration Format *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Standardize on TOML configuration format (pyproject.toml / uv.toml)**, because:\nWe commit to TOML as the single official configuration file format. Settings will be parsed from [tool.uv] in pyproject.toml with fallback to standalone uv.toml.\n\n### Positive Consequences\n\n* Strict alignment with Python packaging standards PEP 518 and PEP 621\n* First-class comment support allows developers to document settings directly inline\n* Unambiguous typing prevents type coercion security bugs common in YAML\n* High-performance serde deserialization in Rust via toml-rs\n\n### Negative Consequences (Trade-offs)\n\n* DevOps engineers accustomed to YAML will need minor syntax adjustment\n* Multi-line strings have specific syntax compared to YAML blocks\n\n## Pros and Cons of Rejected Options\n\n### YAML Configuration (.uv.yaml)\n* Proposed by: @dev-contributor-alex\n* Rejection reasons:\n  * \u274c Severe security risks and arbitrary code execution CVEs in standard YAML parsers\n  * \u274c Norway problem ('NO' interpreted as boolean False) causing silent configuration errors\n  * \u274c Complex indentation rules causing formatting bugs across environments\n* Key objection quote: - @security-auditor-eva ([Source](https://github.com/astral-sh/uv/issues/1042#issuecomment-102))\n  > \"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.\"\n\n### JSON Configuration\n* Proposed by: @frontend-dev-sam\n* Rejection reasons:\n  * \u274c Strict lack of comments prevents documenting complex build and packaging settings\n  * \u274c Trailing commas and strict syntax make human manual editing prone to syntax errors\n* Key objection quote: - @maintainer-marcus ([Source](https://github.com/astral-sh/uv/issues/1042#issuecomment-104))\n  > \"JSON is disqualified because configuration files need comments.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `pyproject.toml`\n* `uv.toml`\n* `crates/uv-settings/*`\n* `crates/uv-configuration/*`\n* `config/loader.py`\n* `config.py`\n* `crates/uv-settings/src/lib.rs`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.\" | @security-auditor-eva | \u2705 Verified | [Comment c-102](https://github.com/astral-sh/uv/issues/1042#issuecomment-102) |\n| eq-2 | \"JSON is disqualified because configuration files need comments.\" | @maintainer-marcus | \u2705 Verified | [Comment c-104](https://github.com/astral-sh/uv/issues/1042#issuecomment-104) |\n| eq-3 | \"Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.\" | @maintainer-marcus | \u2705 Verified | [Comment c-107](https://github.com/astral-sh/uv/issues/1042#issuecomment-107) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
      "created_at": "2026-10-31T21:25:47.873927+00:00"
    },
    {
      "id": "ADR-42823",
      "discussion_id": "dc:discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823",
      "title": "ADR-42823: Adopt PEP 735 Dependency Groups in pyproject.toml",
      "status": "Accepted",
      "date": "2024-02-01",
      "context": "Packaging metadata standardization for test, lint, and development dependencies.",
      "problem_statement": "Engineering evaluation and decision required for: PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)",
      "decision_outcome": "Consensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.",
      "accepted_option": "Adopt PEP 735 with [dependency-groups] in pyproject.toml",
      "considered_options": [
        "[dependency-groups] in pyproject.toml",
        "External YAML dependency files"
      ],
      "rejected_alternatives": [
        {
          "name": "External YAML Dependencies",
          "proposer": "ci_maintainer_dan",
          "rejection_reasons": [
            "Arbitrary code execution CVE risks and unwanted parser dependencies in bootstrap build tools",
            "Fractured project metadata across non-standard external files"
          ],
          "key_objection_quote": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
          "objection_author": "pradyunsg",
          "comment_id": "post-402",
          "comment_url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3"
        }
      ],
      "consequences_positive": [
        "Single unified configuration file in pyproject.toml",
        "Full support across modern packaging backends without extra parser bloat"
      ],
      "consequences_negative": [
        "Requires updating older CI matrices to query pyproject.toml"
      ],
      "affected_components": [
        "pyproject.toml",
        "pip/_internal/req/req_file.py"
      ],
      "evidence_quotes": [
        {
          "id": "eq-1",
          "quote": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
          "author": "pradyunsg",
          "comment_id": "post-402",
          "comment_url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3",
          "verified": true,
          "confidence": 1.0,
          "context": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
          "char_offset": 0
        }
      ],
      "madr_content": "# ADR-42823: Adopt PEP 735 Dependency Groups in pyproject.toml\n\n* Status: **Accepted**\n* Date: 2024-02-01\n* Deciders: @brettcannon, @ci_maintainer_dan, @pradyunsg\n* Source Discussion: [PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)](https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)\n\nPackaging metadata standardization for test, lint, and development dependencies.\n\n## Considered Options\n\n* [dependency-groups] in pyproject.toml *(Chosen)*\n* External YAML dependency files *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Adopt PEP 735 with [dependency-groups] in pyproject.toml**, because:\nConsensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.\n\n### Positive Consequences\n\n* Single unified configuration file in pyproject.toml\n* Full support across modern packaging backends without extra parser bloat\n\n### Negative Consequences (Trade-offs)\n\n* Requires updating older CI matrices to query pyproject.toml\n\n## Pros and Cons of Rejected Options\n\n### External YAML Dependencies\n* Proposed by: @ci_maintainer_dan\n* Rejection reasons:\n  * \u274c Arbitrary code execution CVE risks and unwanted parser dependencies in bootstrap build tools\n  * \u274c Fractured project metadata across non-standard external files\n* Key objection quote: - @pradyunsg ([Source](https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3))\n  > \"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `pyproject.toml`\n* `pip/_internal/req/req_file.py`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.\" | @pradyunsg | \u2705 Verified | [Comment post-402](https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
      "created_at": "2026-10-31T21:25:42.684762+00:00"
    },
    {
      "id": "ADR-780",
      "discussion_id": "gh:encode/httpx/issues/780",
      "title": "ADR-780: Standardize on AnyIO Transport Abstraction",
      "status": "Accepted",
      "date": "2023-11-08",
      "context": "HTTP transport layer architecture across Python asynchronous frameworks.",
      "problem_statement": "Engineering evaluation and decision required for: Evaluate HTTP transport layer: Asyncio vs Trio native backend",
      "decision_outcome": "Standardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.",
      "accepted_option": "Standardize on AnyIO for async backend compatibility",
      "considered_options": [
        "AnyIO Transport Abstraction",
        "Direct Curio Integration",
        "Native Trio Integration"
      ],
      "rejected_alternatives": [
        {
          "name": "Direct Curio Integration",
          "proposer": "curio_advocate",
          "rejection_reasons": [
            "Curio project development has frozen with negligible community adoption",
            "Maintaining custom multi-backend transports multiplies test matrix complexity"
          ],
          "key_objection_quote": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.",
          "objection_author": "florimondmanca",
          "comment_id": "c-302",
          "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-302"
        }
      ],
      "consequences_positive": [
        "Single transport codebase covering both Asyncio and Trio",
        "Significantly reduced test matrix and eliminated duplicate transport maintenance"
      ],
      "consequences_negative": [
        "Additional dependency on anyio abstraction package"
      ],
      "affected_components": [
        "httpx/_transports/default.py",
        "httpx/_transports/anyio.py"
      ],
      "evidence_quotes": [
        {
          "id": "eq-1",
          "quote": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.",
          "author": "florimondmanca",
          "comment_id": "c-302",
          "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-302",
          "verified": true,
          "confidence": 1.0,
          "context": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio. Maintaining a custom Curio transport br...",
          "char_offset": 0
        },
        {
          "id": "eq-2",
          "quote": "Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.",
          "author": "tomchristie",
          "comment_id": "c-303",
          "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-303",
          "verified": true,
          "confidence": 1.0,
          "context": "Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.",
          "char_offset": 0
        }
      ],
      "madr_content": "# ADR-780: Standardize on AnyIO Transport Abstraction\n\n* Status: **Accepted**\n* Date: 2023-11-08\n* Deciders: @curio_advocate, @florimondmanca, @tomchristie\n* Source Discussion: [Evaluate HTTP transport layer: Asyncio vs Trio native backend](https://github.com/encode/httpx/issues/780)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: Evaluate HTTP transport layer: Asyncio vs Trio native backend\n\nHTTP transport layer architecture across Python asynchronous frameworks.\n\n## Considered Options\n\n* AnyIO Transport Abstraction *(Rejected)*\n* Direct Curio Integration *(Rejected)*\n* Native Trio Integration *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Standardize on AnyIO for async backend compatibility**, because:\nStandardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.\n\n### Positive Consequences\n\n* Single transport codebase covering both Asyncio and Trio\n* Significantly reduced test matrix and eliminated duplicate transport maintenance\n\n### Negative Consequences (Trade-offs)\n\n* Additional dependency on anyio abstraction package\n\n## Pros and Cons of Rejected Options\n\n### Direct Curio Integration\n* Proposed by: @curio_advocate\n* Rejection reasons:\n  * \u274c Curio project development has frozen with negligible community adoption\n  * \u274c Maintaining custom multi-backend transports multiplies test matrix complexity\n* Key objection quote: - @florimondmanca ([Source](https://github.com/encode/httpx/issues/780#issuecomment-302))\n  > \"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `httpx/_transports/default.py`\n* `httpx/_transports/anyio.py`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.\" | @florimondmanca | \u2705 Verified | [Comment c-302](https://github.com/encode/httpx/issues/780#issuecomment-302) |\n| eq-2 | \"Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.\" | @tomchristie | \u2705 Verified | [Comment c-303](https://github.com/encode/httpx/issues/780#issuecomment-303) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
      "created_at": "2026-10-31T21:25:42.682924+00:00"
    },
    {
      "id": "ADR-88219",
      "discussion_id": "dc:meta.discourse.org/t/embedded-cache-storage-engine/88219",
      "title": "ADR-88219: Adopt SQLite with WAL for Edge Cache Storage",
      "status": "Accepted",
      "date": "2024-01-22",
      "context": "Edge replication nodes need a crash-resilient, fast embedded cache storage engine with low operational footprint.",
      "problem_statement": "Engineering evaluation and decision required for: Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)",
      "decision_outcome": "We adopt SQLite in WAL mode with memory-mapped I/O. RocksDB is rejected due to excessive binary footprint and ARM cross-compilation complexity.",
      "accepted_option": "Adopt SQLite in WAL (Write-Ahead Logging) mode",
      "considered_options": [
        "SQLite in WAL Mode",
        "RocksDB LSM-Tree Engine"
      ],
      "rejected_alternatives": [
        {
          "name": "RocksDB Storage Engine",
          "proposer": "dan_developer",
          "rejection_reasons": [
            "Excessive binary footprint (85MB) severely bloats container distribution",
            "Severe cross-compilation complexity on ARM64 architectures",
            "High operational maintenance of LSM compaction tuning parameters"
          ],
          "key_objection_quote": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
          "objection_author": "sysadmin_claire",
          "comment_id": "post-202",
          "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3"
        }
      ],
      "consequences_positive": [
        "Minimal 1MB embedded footprint with zero external dynamic library dependencies",
        "High read throughput (>45k queries/sec) via WAL and mmap",
        "Decades of proven crash recovery and corruption resilience"
      ],
      "consequences_negative": [
        "Single writer lock concurrency limit compared to LSM multi-threaded writes"
      ],
      "affected_components": [
        "lib/storage/edge_cache.rb",
        "config/storage.yml",
        "storage/sqlite_backend.py",
        "src/cache/*"
      ],
      "evidence_quotes": [
        {
          "id": "eq-1",
          "quote": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
          "author": "sysadmin_claire",
          "comment_id": "post-202",
          "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3",
          "verified": true,
          "confidence": 1.0,
          "context": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
          "char_offset": 0
        },
        {
          "id": "eq-2",
          "quote": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.",
          "author": "sam_saffron",
          "comment_id": "post-203",
          "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4",
          "verified": true,
          "confidence": 1.0,
          "context": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries. Furthermore, corruption recovery and ba...",
          "char_offset": 0
        }
      ],
      "madr_content": "# ADR-88219: Adopt SQLite with WAL for Edge Cache Storage\n\n* Status: **Accepted**\n* Date: 2024-01-22\n* Deciders: @dan_developer, @jeff_maintainer, @sam_saffron, @sysadmin_claire\n* Source Discussion: [Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)](https://meta.discourse.org/t/embedded-cache-storage-engine/88219)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)\n\nEdge replication nodes need a crash-resilient, fast embedded cache storage engine with low operational footprint.\n\n## Considered Options\n\n* SQLite in WAL Mode *(Rejected)*\n* RocksDB LSM-Tree Engine *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Adopt SQLite in WAL (Write-Ahead Logging) mode**, because:\nWe adopt SQLite in WAL mode with memory-mapped I/O. RocksDB is rejected due to excessive binary footprint and ARM cross-compilation complexity.\n\n### Positive Consequences\n\n* Minimal 1MB embedded footprint with zero external dynamic library dependencies\n* High read throughput (>45k queries/sec) via WAL and mmap\n* Decades of proven crash recovery and corruption resilience\n\n### Negative Consequences (Trade-offs)\n\n* Single writer lock concurrency limit compared to LSM multi-threaded writes\n\n## Pros and Cons of Rejected Options\n\n### RocksDB Storage Engine\n* Proposed by: @dan_developer\n* Rejection reasons:\n  * \u274c Excessive binary footprint (85MB) severely bloats container distribution\n  * \u274c Severe cross-compilation complexity on ARM64 architectures\n  * \u274c High operational maintenance of LSM compaction tuning parameters\n* Key objection quote: - @sysadmin_claire ([Source](https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3))\n  > \"RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `lib/storage/edge_cache.rb`\n* `config/storage.yml`\n* `storage/sqlite_backend.py`\n* `src/cache/*`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.\" | @sysadmin_claire | \u2705 Verified | [Comment post-202](https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3) |\n| eq-2 | \"SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.\" | @sam_saffron | \u2705 Verified | [Comment post-203](https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
      "created_at": "2026-10-31T21:25:42.680660+00:00"
    }
  ],
  "results": {
    "gh:astral-sh/uv/issues/1042": {
      "discussion_id": "gh:astral-sh/uv/issues/1042",
      "stages": [
        {
          "stage_num": 1,
          "stage_name": "Discussion Preprocessing & Summarization",
          "model_name": "Llama 3.2-3B-Instruct",
          "execution_time_ms": 0.19,
          "output": {
            "title": "Decide on configuration file format: TOML vs YAML vs JSON",
            "problem_statement": "Engineering evaluation and decision required for: Decide on configuration file format: TOML vs YAML vs JSON",
            "context_summary": "Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.",
            "participants": [
              "charliermarsh"
            ],
            "identified_topics": [
              "Configuration Format",
              "Developer Experience",
              "Parser Security"
            ],
            "timeline_length": 0
          },
          "raw_response": "{\n  \"title\": \"Decide on configuration file format: TOML vs YAML vs JSON\",\n  \"problem_statement\": \"Engineering evaluation and decision required for: Decide on configuration file format: TOML vs YAML vs JSON\",\n  \"context_summary\": \"Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.\",\n  \"participants\": [\n    \"charliermarsh\"\n  ],\n  \"identified_topics\": [\n    \"Configuration Format\",\n    \"Developer Experience\",\n    \"Parser Security\"\n  ],\n  \"timeline_length\": 0\n}"
        },
        {
          "stage_num": 2,
          "stage_name": "Argument Mining & Rejected Alternatives Analysis",
          "model_name": "Phi-3.5-mini-instruct",
          "execution_time_ms": 0.04,
          "output": {
            "proposals": [
              {
                "id": "prop-1",
                "name": "YAML configuration format (.uv.yaml)",
                "proposer": "dev-contributor-alex",
                "description": "Adopt YAML for familiarity with DevOps tools, GitHub Actions, and Kubernetes.",
                "status": "rejected"
              },
              {
                "id": "prop-2",
                "name": "JSON configuration format",
                "proposer": "frontend-dev-sam",
                "description": "Adopt JSON for universal language support and high-speed serde_json parsing.",
                "status": "rejected"
              },
              {
                "id": "prop-3",
                "name": "TOML configuration format (pyproject.toml / uv.toml)",
                "proposer": "charliermarsh",
                "description": "Standardize on TOML aligning with PEP 518/621 with comment support and safe typing.",
                "status": "accepted"
              }
            ],
            "arguments": [
              {
                "id": "arg-1",
                "proposal_id": "prop-1",
                "author": "security-auditor-eva",
                "stance": "con",
                "claim": "YAML has critical security and parsing ambiguity risks",
                "reasoning": "Arbitrary type coercion, code execution CVEs in standard parsers, and the Norway problem causing silent false positives.",
                "quote": "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
                "comment_id": "c-102"
              },
              {
                "id": "arg-2",
                "proposal_id": "prop-2",
                "author": "maintainer-marcus",
                "stance": "con",
                "claim": "JSON lacks comment support essential for configs",
                "reasoning": "Configuration files require explanatory comments; machine-only JSON degrades developer experience.",
                "quote": "JSON is disqualified because configuration files need comments.",
                "comment_id": "c-104"
              },
              {
                "id": "arg-3",
                "proposal_id": "prop-3",
                "author": "charliermarsh",
                "stance": "pro",
                "claim": "TOML matches Python packaging standards with robust comments and typing",
                "reasoning": "Aligns with PEP 518/PEP 621, unambiguous typing, and mature Rust serde integrations.",
                "quote": "It aligns with PEP 518/PEP 621 (pyproject.toml), has unambiguous typing, first-class comment support, and serde integrations in Rust are very mature.",
                "comment_id": "c-105"
              }
            ],
            "rejected_alternatives": [
              {
                "name": "YAML Configuration (.uv.yaml)",
                "proposer": "dev-contributor-alex",
                "rejection_reasons": [
                  "Severe security risks and arbitrary code execution CVEs in standard YAML parsers",
                  "Norway problem ('NO' interpreted as boolean False) causing silent configuration errors",
                  "Complex indentation rules causing formatting bugs across environments"
                ],
                "key_objection_quote": "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
                "objection_author": "security-auditor-eva",
                "comment_id": "c-102",
                "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102"
              },
              {
                "name": "JSON Configuration",
                "proposer": "frontend-dev-sam",
                "rejection_reasons": [
                  "Strict lack of comments prevents documenting complex build and packaging settings",
                  "Trailing commas and strict syntax make human manual editing prone to syntax errors"
                ],
                "key_objection_quote": "JSON is disqualified because configuration files need comments.",
                "objection_author": "maintainer-marcus",
                "comment_id": "c-104",
                "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104"
              }
            ]
          },
          "raw_response": "{\n  \"proposals\": [\n    {\n      \"id\": \"prop-1\",\n      \"name\": \"YAML configuration format (.uv.yaml)\",\n      \"proposer\": \"dev-contributor-alex\",\n      \"description\": \"Adopt YAML for familiarity with DevOps tools, GitHub Actions, and Kubernetes.\",\n      \"status\": \"rejected\"\n    },\n    {\n      \"id\": \"prop-2\",\n      \"name\": \"JSON configuration format\",\n      \"proposer\": \"frontend-dev-sam\",\n      \"description\": \"Adopt JSON for universal language support and high-speed serde_json parsing.\",\n      \"status\": \"rejected\"\n    },\n    {\n      \"id\": \"prop-3\",\n      \"name\": \"TOML configuration format (pyproject.toml / uv.toml)\",\n      \"proposer\": \"charliermarsh\",\n      \"description\": \"Standardize on TOML aligning with PEP 518/621 with comment support and safe typing.\",\n      \"status\": \"accepted\"\n    }\n  ],\n  \"arguments\": [\n    {\n      \"id\": \"arg-1\",\n      \"proposal_id\": \"prop-1\",\n      \"author\": \"security-auditor-eva\",\n      \"stance\": \"con\",\n      \"claim\": \"YAML has critical security and parsing ambiguity risks\",\n      \"reasoning\": \"Arbitrary type coercion, code execution CVEs in standard parsers, and the Norway problem causing silent false positives.\",\n      \"quote\": \"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.\",\n      \"comment_id\": \"c-102\"\n    },\n    {\n      \"id\": \"arg-2\",\n      \"proposal_id\": \"prop-2\",\n      \"author\": \"maintainer-marcus\",\n      \"stance\": \"con\",\n      \"claim\": \"JSON lacks comment support essential for configs\",\n      \"reasoning\": \"Configuration files require explanatory comments; machine-only JSON degrades developer experience.\",\n      \"quote\": \"JSON is disqualified because configuration files need comments.\",\n      \"comment_id\": \"c-104\"\n    },\n    {\n      \"id\": \"arg-3\",\n      \"proposal_id\": \"prop-3\",\n      \"author\": \"charliermarsh\",\n      \"stance\": \"pro\",\n      \"claim\": \"TOML matches Python packaging standards with robust comments and typing\",\n      \"reasoning\": \"Aligns with PEP 518/PEP 621, unambiguous typing, and mature Rust serde integrations.\",\n      \"quote\": \"It aligns with PEP 518/PEP 621 (pyproject.toml), has unambiguous typing, first-class comment support, and serde integrations in Rust are very mature.\",\n      \"comment_id\": \"c-105\"\n    }\n  ],\n  \"rejected_alternatives\": [\n    {\n      \"name\": \"YAML Configuration (.uv.yaml)\",\n      \"proposer\": \"dev-contributor-alex\",\n      \"rejection_reasons\": [\n        \"Severe security risks and arbitrary code execution CVEs in standard YAML parsers\",\n        \"Norway problem ('NO' interpreted as boolean False) causing silent configuration errors\",\n        \"Complex indentation rules causing formatting bugs across environments\"\n      ],\n      \"key_objection_quote\": \"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.\",\n      \"objection_author\": \"security-auditor-eva\",\n      \"comment_id\": \"c-102\",\n      \"comment_url\": \"https://github.com/astral-sh/uv/issues/1042#issuecomment-102\"\n    },\n    {\n      \"name\": \"JSON Configuration\",\n      \"proposer\": \"frontend-dev-sam\",\n      \"rejection_reasons\": [\n        \"Strict lack of comments prevents documenting complex build and packaging settings\",\n        \"Trailing commas and strict syntax make human manual editing prone to syntax errors\"\n      ],\n      \"key_objection_quote\": \"JSON is disqualified because configuration files need comments.\",\n      \"objection_author\": \"maintainer-marcus\",\n      \"comment_id\": \"c-104\",\n      \"comment_url\": \"https://github.com/astral-sh/uv/issues/1042#issuecomment-104\"\n    }\n  ]\n}"
        },
        {
          "stage_num": 3,
          "stage_name": "Decision Synthesis & Code Grounding",
          "model_name": "Qwen 2.5-Coder-7B-Instruct",
          "execution_time_ms": 0.03,
          "output": {
            "title": "ADR-1042: Standardize on TOML Configuration Format",
            "status": "Accepted",
            "accepted_option": "Standardize on TOML configuration format (pyproject.toml / uv.toml)",
            "considered_options": [
              "TOML Configuration Format",
              "YAML Configuration Format",
              "JSON Configuration Format"
            ],
            "context": "Project settings, CLI arguments, and dependency constraints require a robust, standardized configuration file format.",
            "decision_outcome": "We commit to TOML as the single official configuration file format. Settings will be parsed from [tool.uv] in pyproject.toml with fallback to standalone uv.toml.",
            "consequences_positive": [
              "Strict alignment with Python packaging standards PEP 518 and PEP 621",
              "First-class comment support allows developers to document settings directly inline",
              "Unambiguous typing prevents type coercion security bugs common in YAML",
              "High-performance serde deserialization in Rust via toml-rs"
            ],
            "consequences_negative": [
              "DevOps engineers accustomed to YAML will need minor syntax adjustment",
              "Multi-line strings have specific syntax compared to YAML blocks"
            ],
            "affected_components": [
              "pyproject.toml",
              "uv.toml",
              "crates/uv-settings/*",
              "crates/uv-configuration/*",
              "config/loader.py",
              "config.py",
              "crates/uv-settings/src/lib.rs"
            ],
            "evidence_quotes": [
              {
                "id": "eq-1",
                "quote": "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
                "author": "security-auditor-eva",
                "comment_id": "c-102",
                "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102",
                "verified": true,
                "confidence": 1.0,
                "context": "Security objection to YAML proposal"
              },
              {
                "id": "eq-2",
                "quote": "JSON is disqualified because configuration files need comments.",
                "author": "maintainer-marcus",
                "comment_id": "c-104",
                "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104",
                "verified": true,
                "confidence": 1.0,
                "context": "Maintainer rejection of JSON due to missing comment support"
              },
              {
                "id": "eq-3",
                "quote": "Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.",
                "author": "maintainer-marcus",
                "comment_id": "c-107",
                "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-107",
                "verified": true,
                "confidence": 1.0,
                "context": "Final consensus and outcome statement"
              }
            ]
          },
          "raw_response": "{\n  \"title\": \"ADR-1042: Standardize on TOML Configuration Format\",\n  \"status\": \"Accepted\",\n  \"accepted_option\": \"Standardize on TOML configuration format (pyproject.toml / uv.toml)\",\n  \"considered_options\": [\n    \"TOML Configuration Format\",\n    \"YAML Configuration Format\",\n    \"JSON Configuration Format\"\n  ],\n  \"context\": \"Project settings, CLI arguments, and dependency constraints require a robust, standardized configuration file format.\",\n  \"decision_outcome\": \"We commit to TOML as the single official configuration file format. Settings will be parsed from [tool.uv] in pyproject.toml with fallback to standalone uv.toml.\",\n  \"consequences_positive\": [\n    \"Strict alignment with Python packaging standards PEP 518 and PEP 621\",\n    \"First-class comment support allows developers to document settings directly inline\",\n    \"Unambiguous typing prevents type coercion security bugs common in YAML\",\n    \"High-performance serde deserialization in Rust via toml-rs\"\n  ],\n  \"consequences_negative\": [\n    \"DevOps engineers accustomed to YAML will need minor syntax adjustment\",\n    \"Multi-line strings have specific syntax compared to YAML blocks\"\n  ],\n  \"affected_components\": [\n    \"pyproject.toml\",\n    \"uv.toml\",\n    \"crates/uv-settings/*\",\n    \"crates/uv-configuration/*\",\n    \"config/loader.py\",\n    \"config.py\"\n  ],\n  \"evidence_quotes\": [\n    {\n      \"id\": \"eq-1\",\n      \"quote\": \"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.\",\n      \"author\": \"security-auditor-eva\",\n      \"comment_id\": \"c-102\",\n      \"comment_url\": \"https://github.com/astral-sh/uv/issues/1042#issuecomment-102\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Security objection to YAML proposal\"\n    },\n    {\n      \"id\": \"eq-2\",\n      \"quote\": \"JSON is disqualified because configuration files need comments.\",\n      \"author\": \"maintainer-marcus\",\n      \"comment_id\": \"c-104\",\n      \"comment_url\": \"https://github.com/astral-sh/uv/issues/1042#issuecomment-104\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Maintainer rejection of JSON due to missing comment support\"\n    },\n    {\n      \"id\": \"eq-3\",\n      \"quote\": \"Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.\",\n      \"author\": \"maintainer-marcus\",\n      \"comment_id\": \"c-107\",\n      \"comment_url\": \"https://github.com/astral-sh/uv/issues/1042#issuecomment-107\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Final consensus and outcome statement\"\n    }\n  ]\n}"
        }
      ],
      "final_decision": {
        "id": "ADR-1042",
        "discussion_id": "gh:astral-sh/uv/issues/1042",
        "title": "ADR-1042: Standardize on TOML Configuration Format",
        "status": "Accepted",
        "date": "2024-03-15",
        "context": "Project settings, CLI arguments, and dependency constraints require a robust, standardized configuration file format.",
        "problem_statement": "Engineering evaluation and decision required for: Decide on configuration file format: TOML vs YAML vs JSON",
        "decision_outcome": "We commit to TOML as the single official configuration file format. Settings will be parsed from [tool.uv] in pyproject.toml with fallback to standalone uv.toml.",
        "accepted_option": "Standardize on TOML configuration format (pyproject.toml / uv.toml)",
        "considered_options": [
          "TOML Configuration Format",
          "YAML Configuration Format",
          "JSON Configuration Format"
        ],
        "rejected_alternatives": [
          {
            "name": "YAML Configuration (.uv.yaml)",
            "proposer": "dev-contributor-alex",
            "rejection_reasons": [
              "Severe security risks and arbitrary code execution CVEs in standard YAML parsers",
              "Norway problem ('NO' interpreted as boolean False) causing silent configuration errors",
              "Complex indentation rules causing formatting bugs across environments"
            ],
            "key_objection_quote": "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
            "objection_author": "security-auditor-eva",
            "comment_id": "c-102",
            "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102"
          },
          {
            "name": "JSON Configuration",
            "proposer": "frontend-dev-sam",
            "rejection_reasons": [
              "Strict lack of comments prevents documenting complex build and packaging settings",
              "Trailing commas and strict syntax make human manual editing prone to syntax errors"
            ],
            "key_objection_quote": "JSON is disqualified because configuration files need comments.",
            "objection_author": "maintainer-marcus",
            "comment_id": "c-104",
            "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104"
          }
        ],
        "consequences_positive": [
          "Strict alignment with Python packaging standards PEP 518 and PEP 621",
          "First-class comment support allows developers to document settings directly inline",
          "Unambiguous typing prevents type coercion security bugs common in YAML",
          "High-performance serde deserialization in Rust via toml-rs"
        ],
        "consequences_negative": [
          "DevOps engineers accustomed to YAML will need minor syntax adjustment",
          "Multi-line strings have specific syntax compared to YAML blocks"
        ],
        "affected_components": [
          "pyproject.toml",
          "uv.toml",
          "crates/uv-settings/*",
          "crates/uv-configuration/*",
          "config/loader.py",
          "config.py",
          "crates/uv-settings/src/lib.rs"
        ],
        "evidence_quotes": [
          {
            "id": "eq-1",
            "quote": "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.",
            "author": "security-auditor-eva",
            "comment_id": "c-102",
            "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-102",
            "verified": true,
            "confidence": 1.0,
            "context": "I strongly object to YAML. YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers. Furthermore, the Norway problem ('NO' i...",
            "char_offset": 27
          },
          {
            "id": "eq-2",
            "quote": "JSON is disqualified because configuration files need comments.",
            "author": "maintainer-marcus",
            "comment_id": "c-104",
            "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-104",
            "verified": true,
            "confidence": 1.0,
            "context": "JSON is disqualified because configuration files need comments. Forcing developers to maintain machine-...",
            "char_offset": 0
          },
          {
            "id": "eq-3",
            "quote": "Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.",
            "author": "maintainer-marcus",
            "comment_id": "c-107",
            "comment_url": "https://github.com/astral-sh/uv/issues/1042#issuecomment-107",
            "verified": true,
            "confidence": 1.0,
            "context": "Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.",
            "char_offset": 0
          }
        ],
        "madr_content": "# ADR-1042: Standardize on TOML Configuration Format\n\n* Status: **Accepted**\n* Date: 2024-03-15\n* Deciders: @charliermarsh, @dev-contributor-alex, @frontend-dev-sam, @maintainer-marcus, @security-auditor-eva\n* Source Discussion: [Decide on configuration file format: TOML vs YAML vs JSON](https://github.com/astral-sh/uv/issues/1042)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: Decide on configuration file format: TOML vs YAML vs JSON\n\nProject settings, CLI arguments, and dependency constraints require a robust, standardized configuration file format.\n\n## Considered Options\n\n* TOML Configuration Format *(Chosen)*\n* YAML Configuration Format *(Rejected)*\n* JSON Configuration Format *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Standardize on TOML configuration format (pyproject.toml / uv.toml)**, because:\nWe commit to TOML as the single official configuration file format. Settings will be parsed from [tool.uv] in pyproject.toml with fallback to standalone uv.toml.\n\n### Positive Consequences\n\n* Strict alignment with Python packaging standards PEP 518 and PEP 621\n* First-class comment support allows developers to document settings directly inline\n* Unambiguous typing prevents type coercion security bugs common in YAML\n* High-performance serde deserialization in Rust via toml-rs\n\n### Negative Consequences (Trade-offs)\n\n* DevOps engineers accustomed to YAML will need minor syntax adjustment\n* Multi-line strings have specific syntax compared to YAML blocks\n\n## Pros and Cons of Rejected Options\n\n### YAML Configuration (.uv.yaml)\n* Proposed by: @dev-contributor-alex\n* Rejection reasons:\n  * \u274c Severe security risks and arbitrary code execution CVEs in standard YAML parsers\n  * \u274c Norway problem ('NO' interpreted as boolean False) causing silent configuration errors\n  * \u274c Complex indentation rules causing formatting bugs across environments\n* Key objection quote: - @security-auditor-eva ([Source](https://github.com/astral-sh/uv/issues/1042#issuecomment-102))\n  > \"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.\"\n\n### JSON Configuration\n* Proposed by: @frontend-dev-sam\n* Rejection reasons:\n  * \u274c Strict lack of comments prevents documenting complex build and packaging settings\n  * \u274c Trailing commas and strict syntax make human manual editing prone to syntax errors\n* Key objection quote: - @maintainer-marcus ([Source](https://github.com/astral-sh/uv/issues/1042#issuecomment-104))\n  > \"JSON is disqualified because configuration files need comments.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `pyproject.toml`\n* `uv.toml`\n* `crates/uv-settings/*`\n* `crates/uv-configuration/*`\n* `config/loader.py`\n* `config.py`\n* `crates/uv-settings/src/lib.rs`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers.\" | @security-auditor-eva | \u2705 Verified | [Comment c-102](https://github.com/astral-sh/uv/issues/1042#issuecomment-102) |\n| eq-2 | \"JSON is disqualified because configuration files need comments.\" | @maintainer-marcus | \u2705 Verified | [Comment c-104](https://github.com/astral-sh/uv/issues/1042#issuecomment-104) |\n| eq-3 | \"Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities and typing ambiguities. Rejected JSON due to absence of comment support. Implemented in PR #1045.\" | @maintainer-marcus | \u2705 Verified | [Comment c-107](https://github.com/astral-sh/uv/issues/1042#issuecomment-107) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
        "created_at": "2026-10-31T21:53:08.320654+00:00"
      },
      "total_time_ms": 1.64
    },
    "dc:meta.discourse.org/t/embedded-cache-storage-engine/88219": {
      "discussion_id": "dc:meta.discourse.org/t/embedded-cache-storage-engine/88219",
      "stages": [
        {
          "stage_num": 1,
          "stage_name": "Discussion Preprocessing & Summarization",
          "model_name": "Llama 3.2-3B-Instruct",
          "execution_time_ms": 0.03,
          "output": {
            "title": "Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)",
            "problem_statement": "Engineering evaluation and decision required for: Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)",
            "context_summary": "Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.",
            "participants": [
              "sam_saffron"
            ],
            "identified_topics": [
              "Configuration Format",
              "Developer Experience",
              "Parser Security",
              "Embedded Storage",
              "WAL Mode",
              "Binary Size",
              "Cross-Compilation"
            ],
            "timeline_length": 0
          },
          "raw_response": "{\n  \"title\": \"Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)\",\n  \"problem_statement\": \"Engineering evaluation and decision required for: Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)\",\n  \"context_summary\": \"Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.\",\n  \"participants\": [\n    \"sam_saffron\"\n  ],\n  \"identified_topics\": [\n    \"Configuration Format\",\n    \"Developer Experience\",\n    \"Parser Security\",\n    \"Embedded Storage\",\n    \"WAL Mode\",\n    \"Binary Size\",\n    \"Cross-Compilation\"\n  ],\n  \"timeline_length\": 0\n}"
        },
        {
          "stage_num": 2,
          "stage_name": "Argument Mining & Rejected Alternatives Analysis",
          "model_name": "Phi-3.5-mini-instruct",
          "execution_time_ms": 0.02,
          "output": {
            "proposals": [
              {
                "id": "prop-1",
                "name": "RocksDB LSM-Tree Engine",
                "proposer": "dan_developer",
                "description": "LSM-tree optimized storage for edge write telemetry.",
                "status": "rejected"
              },
              {
                "id": "prop-2",
                "name": "SQLite in WAL Mode",
                "proposer": "sam_saffron",
                "description": "Zero-dependency embedded SQLite with write-ahead logging and mmap.",
                "status": "accepted"
              }
            ],
            "arguments": [
              {
                "id": "arg-1",
                "proposal_id": "prop-1",
                "author": "sysadmin_claire",
                "stance": "con",
                "claim": "RocksDB has unacceptable binary bloat and cross-compilation friction",
                "reasoning": "Adds 85MB of binary overhead and jemalloc compilation issues on ARM64.",
                "quote": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
                "comment_id": "post-202"
              },
              {
                "id": "arg-2",
                "proposal_id": "prop-2",
                "author": "sam_saffron",
                "stance": "pro",
                "claim": "SQLite WAL delivers 45k reads/sec with 1MB footprint",
                "reasoning": "Zero external dependencies, crash resilience, and battle-tested tooling.",
                "quote": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.",
                "comment_id": "post-203"
              }
            ],
            "rejected_alternatives": [
              {
                "name": "RocksDB Storage Engine",
                "proposer": "dan_developer",
                "rejection_reasons": [
                  "Excessive binary footprint (85MB) severely bloats container distribution",
                  "Severe cross-compilation complexity on ARM64 architectures",
                  "High operational maintenance of LSM compaction tuning parameters"
                ],
                "key_objection_quote": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
                "objection_author": "sysadmin_claire",
                "comment_id": "post-202",
                "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3"
              }
            ]
          },
          "raw_response": "{\n  \"proposals\": [\n    {\n      \"id\": \"prop-1\",\n      \"name\": \"RocksDB LSM-Tree Engine\",\n      \"proposer\": \"dan_developer\",\n      \"description\": \"LSM-tree optimized storage for edge write telemetry.\",\n      \"status\": \"rejected\"\n    },\n    {\n      \"id\": \"prop-2\",\n      \"name\": \"SQLite in WAL Mode\",\n      \"proposer\": \"sam_saffron\",\n      \"description\": \"Zero-dependency embedded SQLite with write-ahead logging and mmap.\",\n      \"status\": \"accepted\"\n    }\n  ],\n  \"arguments\": [\n    {\n      \"id\": \"arg-1\",\n      \"proposal_id\": \"prop-1\",\n      \"author\": \"sysadmin_claire\",\n      \"stance\": \"con\",\n      \"claim\": \"RocksDB has unacceptable binary bloat and cross-compilation friction\",\n      \"reasoning\": \"Adds 85MB of binary overhead and jemalloc compilation issues on ARM64.\",\n      \"quote\": \"RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.\",\n      \"comment_id\": \"post-202\"\n    },\n    {\n      \"id\": \"arg-2\",\n      \"proposal_id\": \"prop-2\",\n      \"author\": \"sam_saffron\",\n      \"stance\": \"pro\",\n      \"claim\": \"SQLite WAL delivers 45k reads/sec with 1MB footprint\",\n      \"reasoning\": \"Zero external dependencies, crash resilience, and battle-tested tooling.\",\n      \"quote\": \"SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.\",\n      \"comment_id\": \"post-203\"\n    }\n  ],\n  \"rejected_alternatives\": [\n    {\n      \"name\": \"RocksDB Storage Engine\",\n      \"proposer\": \"dan_developer\",\n      \"rejection_reasons\": [\n        \"Excessive binary footprint (85MB) severely bloats container distribution\",\n        \"Severe cross-compilation complexity on ARM64 architectures\",\n        \"High operational maintenance of LSM compaction tuning parameters\"\n      ],\n      \"key_objection_quote\": \"RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.\",\n      \"objection_author\": \"sysadmin_claire\",\n      \"comment_id\": \"post-202\",\n      \"comment_url\": \"https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3\"\n    }\n  ]\n}"
        },
        {
          "stage_num": 3,
          "stage_name": "Decision Synthesis & Code Grounding",
          "model_name": "Qwen 2.5-Coder-7B-Instruct",
          "execution_time_ms": 0.02,
          "output": {
            "title": "ADR-88219: Adopt SQLite with WAL for Edge Cache Storage",
            "status": "Accepted",
            "accepted_option": "Adopt SQLite in WAL (Write-Ahead Logging) mode",
            "considered_options": [
              "SQLite in WAL Mode",
              "RocksDB LSM-Tree Engine"
            ],
            "context": "Edge replication nodes need a crash-resilient, fast embedded cache storage engine with low operational footprint.",
            "decision_outcome": "We adopt SQLite in WAL mode with memory-mapped I/O. RocksDB is rejected due to excessive binary footprint and ARM cross-compilation complexity.",
            "consequences_positive": [
              "Minimal 1MB embedded footprint with zero external dynamic library dependencies",
              "High read throughput (>45k queries/sec) via WAL and mmap",
              "Decades of proven crash recovery and corruption resilience"
            ],
            "consequences_negative": [
              "Single writer lock concurrency limit compared to LSM multi-threaded writes"
            ],
            "affected_components": [
              "lib/storage/edge_cache.rb",
              "config/storage.yml",
              "storage/sqlite_backend.py",
              "src/cache/*"
            ],
            "evidence_quotes": [
              {
                "id": "eq-1",
                "quote": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
                "author": "sysadmin_claire",
                "comment_id": "post-202",
                "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3",
                "verified": true,
                "confidence": 1.0,
                "context": "Cross-compilation and binary size objection to RocksDB"
              },
              {
                "id": "eq-2",
                "quote": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.",
                "author": "sam_saffron",
                "comment_id": "post-203",
                "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4",
                "verified": true,
                "confidence": 1.0,
                "context": "Performance benchmark evidence supporting SQLite"
              }
            ]
          },
          "raw_response": "{\n  \"title\": \"ADR-88219: Adopt SQLite with WAL for Edge Cache Storage\",\n  \"status\": \"Accepted\",\n  \"accepted_option\": \"Adopt SQLite in WAL (Write-Ahead Logging) mode\",\n  \"considered_options\": [\n    \"SQLite in WAL Mode\",\n    \"RocksDB LSM-Tree Engine\"\n  ],\n  \"context\": \"Edge replication nodes need a crash-resilient, fast embedded cache storage engine with low operational footprint.\",\n  \"decision_outcome\": \"We adopt SQLite in WAL mode with memory-mapped I/O. RocksDB is rejected due to excessive binary footprint and ARM cross-compilation complexity.\",\n  \"consequences_positive\": [\n    \"Minimal 1MB embedded footprint with zero external dynamic library dependencies\",\n    \"High read throughput (>45k queries/sec) via WAL and mmap\",\n    \"Decades of proven crash recovery and corruption resilience\"\n  ],\n  \"consequences_negative\": [\n    \"Single writer lock concurrency limit compared to LSM multi-threaded writes\"\n  ],\n  \"affected_components\": [\n    \"lib/storage/edge_cache.rb\",\n    \"config/storage.yml\",\n    \"storage/sqlite_backend.py\",\n    \"src/cache/*\"\n  ],\n  \"evidence_quotes\": [\n    {\n      \"id\": \"eq-1\",\n      \"quote\": \"RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.\",\n      \"author\": \"sysadmin_claire\",\n      \"comment_id\": \"post-202\",\n      \"comment_url\": \"https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Cross-compilation and binary size objection to RocksDB\"\n    },\n    {\n      \"id\": \"eq-2\",\n      \"quote\": \"SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.\",\n      \"author\": \"sam_saffron\",\n      \"comment_id\": \"post-203\",\n      \"comment_url\": \"https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Performance benchmark evidence supporting SQLite\"\n    }\n  ]\n}"
        }
      ],
      "final_decision": {
        "id": "ADR-88219",
        "discussion_id": "dc:meta.discourse.org/t/embedded-cache-storage-engine/88219",
        "title": "ADR-88219: Adopt SQLite with WAL for Edge Cache Storage",
        "status": "Accepted",
        "date": "2024-01-22",
        "context": "Edge replication nodes need a crash-resilient, fast embedded cache storage engine with low operational footprint.",
        "problem_statement": "Engineering evaluation and decision required for: Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)",
        "decision_outcome": "We adopt SQLite in WAL mode with memory-mapped I/O. RocksDB is rejected due to excessive binary footprint and ARM cross-compilation complexity.",
        "accepted_option": "Adopt SQLite in WAL (Write-Ahead Logging) mode",
        "considered_options": [
          "SQLite in WAL Mode",
          "RocksDB LSM-Tree Engine"
        ],
        "rejected_alternatives": [
          {
            "name": "RocksDB Storage Engine",
            "proposer": "dan_developer",
            "rejection_reasons": [
              "Excessive binary footprint (85MB) severely bloats container distribution",
              "Severe cross-compilation complexity on ARM64 architectures",
              "High operational maintenance of LSM compaction tuning parameters"
            ],
            "key_objection_quote": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
            "objection_author": "sysadmin_claire",
            "comment_id": "post-202",
            "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3"
          }
        ],
        "consequences_positive": [
          "Minimal 1MB embedded footprint with zero external dynamic library dependencies",
          "High read throughput (>45k queries/sec) via WAL and mmap",
          "Decades of proven crash recovery and corruption resilience"
        ],
        "consequences_negative": [
          "Single writer lock concurrency limit compared to LSM multi-threaded writes"
        ],
        "affected_components": [
          "lib/storage/edge_cache.rb",
          "config/storage.yml",
          "storage/sqlite_backend.py",
          "src/cache/*"
        ],
        "evidence_quotes": [
          {
            "id": "eq-1",
            "quote": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
            "author": "sysadmin_claire",
            "comment_id": "post-202",
            "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3",
            "verified": true,
            "confidence": 1.0,
            "context": "RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.",
            "char_offset": 0
          },
          {
            "id": "eq-2",
            "quote": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.",
            "author": "sam_saffron",
            "comment_id": "post-203",
            "comment_url": "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4",
            "verified": true,
            "confidence": 1.0,
            "context": "SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries. Furthermore, corruption recovery and ba...",
            "char_offset": 0
          }
        ],
        "madr_content": "# ADR-88219: Adopt SQLite with WAL for Edge Cache Storage\n\n* Status: **Accepted**\n* Date: 2024-01-22\n* Deciders: @dan_developer, @jeff_maintainer, @sam_saffron, @sysadmin_claire\n* Source Discussion: [Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)](https://meta.discourse.org/t/embedded-cache-storage-engine/88219)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: Architecture: Choosing Embedded Storage Engine for Edge Replication (SQLite vs RocksDB)\n\nEdge replication nodes need a crash-resilient, fast embedded cache storage engine with low operational footprint.\n\n## Considered Options\n\n* SQLite in WAL Mode *(Rejected)*\n* RocksDB LSM-Tree Engine *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Adopt SQLite in WAL (Write-Ahead Logging) mode**, because:\nWe adopt SQLite in WAL mode with memory-mapped I/O. RocksDB is rejected due to excessive binary footprint and ARM cross-compilation complexity.\n\n### Positive Consequences\n\n* Minimal 1MB embedded footprint with zero external dynamic library dependencies\n* High read throughput (>45k queries/sec) via WAL and mmap\n* Decades of proven crash recovery and corruption resilience\n\n### Negative Consequences (Trade-offs)\n\n* Single writer lock concurrency limit compared to LSM multi-threaded writes\n\n## Pros and Cons of Rejected Options\n\n### RocksDB Storage Engine\n* Proposed by: @dan_developer\n* Rejection reasons:\n  * \u274c Excessive binary footprint (85MB) severely bloats container distribution\n  * \u274c Severe cross-compilation complexity on ARM64 architectures\n  * \u274c High operational maintenance of LSM compaction tuning parameters\n* Key objection quote: - @sysadmin_claire ([Source](https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3))\n  > \"RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `lib/storage/edge_cache.rb`\n* `config/storage.yml`\n* `storage/sqlite_backend.py`\n* `src/cache/*`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"RocksDB requires compiling massive C++ binaries with jemalloc dependencies. Cross-compilation across ARM64 edge gateways has been a constant packaging headache in our container images, adding 85MB of binary overhead.\" | @sysadmin_claire | \u2705 Verified | [Comment post-202](https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3) |\n| eq-2 | \"SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries.\" | @sam_saffron | \u2705 Verified | [Comment post-203](https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
        "created_at": "2026-10-31T21:53:08.322077+00:00"
      },
      "total_time_ms": 0.13
    },
    "gh:encode/httpx/issues/780": {
      "discussion_id": "gh:encode/httpx/issues/780",
      "stages": [
        {
          "stage_num": 1,
          "stage_name": "Discussion Preprocessing & Summarization",
          "model_name": "Llama 3.2-3B-Instruct",
          "execution_time_ms": 0.02,
          "output": {
            "title": "Evaluate HTTP transport layer: Asyncio vs Trio native backend",
            "problem_statement": "Engineering evaluation and decision required for: Evaluate HTTP transport layer: Asyncio vs Trio native backend",
            "context_summary": "Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.",
            "participants": [
              "tomchristie"
            ],
            "identified_topics": [
              "Configuration Format",
              "Developer Experience",
              "Parser Security",
              "Async Runtime",
              "Transport Abstraction",
              "Maintenance Overhead"
            ],
            "timeline_length": 0
          },
          "raw_response": "{\n  \"title\": \"Evaluate HTTP transport layer: Asyncio vs Trio native backend\",\n  \"problem_statement\": \"Engineering evaluation and decision required for: Evaluate HTTP transport layer: Asyncio vs Trio native backend\",\n  \"context_summary\": \"Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.\",\n  \"participants\": [\n    \"tomchristie\"\n  ],\n  \"identified_topics\": [\n    \"Configuration Format\",\n    \"Developer Experience\",\n    \"Parser Security\",\n    \"Async Runtime\",\n    \"Transport Abstraction\",\n    \"Maintenance Overhead\"\n  ],\n  \"timeline_length\": 0\n}"
        },
        {
          "stage_num": 2,
          "stage_name": "Argument Mining & Rejected Alternatives Analysis",
          "model_name": "Phi-3.5-mini-instruct",
          "execution_time_ms": 0.02,
          "output": {
            "proposals": [
              {
                "id": "prop-1",
                "name": "Direct Curio Transport Backend",
                "proposer": "curio_advocate",
                "description": "Maintain native Curio transport alongside Asyncio.",
                "status": "rejected"
              },
              {
                "id": "prop-2",
                "name": "AnyIO Transport Abstraction",
                "proposer": "tomchristie",
                "description": "Unified transport abstraction covering Asyncio and Trio.",
                "status": "accepted"
              }
            ],
            "arguments": [
              {
                "id": "arg-1",
                "proposal_id": "prop-1",
                "author": "florimondmanca",
                "stance": "con",
                "claim": "Curio maintenance is stalled and adoption is low",
                "reasoning": "Curio development has essentially frozen; custom maintenance would be unsustainable debt.",
                "quote": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.",
                "comment_id": "c-302"
              }
            ],
            "rejected_alternatives": [
              {
                "name": "Direct Curio Integration",
                "proposer": "curio_advocate",
                "rejection_reasons": [
                  "Curio project development has frozen with negligible community adoption",
                  "Maintaining custom multi-backend transports multiplies test matrix complexity"
                ],
                "key_objection_quote": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.",
                "objection_author": "florimondmanca",
                "comment_id": "c-302",
                "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-302"
              }
            ]
          },
          "raw_response": "{\n  \"proposals\": [\n    {\n      \"id\": \"prop-1\",\n      \"name\": \"Direct Curio Transport Backend\",\n      \"proposer\": \"curio_advocate\",\n      \"description\": \"Maintain native Curio transport alongside Asyncio.\",\n      \"status\": \"rejected\"\n    },\n    {\n      \"id\": \"prop-2\",\n      \"name\": \"AnyIO Transport Abstraction\",\n      \"proposer\": \"tomchristie\",\n      \"description\": \"Unified transport abstraction covering Asyncio and Trio.\",\n      \"status\": \"accepted\"\n    }\n  ],\n  \"arguments\": [\n    {\n      \"id\": \"arg-1\",\n      \"proposal_id\": \"prop-1\",\n      \"author\": \"florimondmanca\",\n      \"stance\": \"con\",\n      \"claim\": \"Curio maintenance is stalled and adoption is low\",\n      \"reasoning\": \"Curio development has essentially frozen; custom maintenance would be unsustainable debt.\",\n      \"quote\": \"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.\",\n      \"comment_id\": \"c-302\"\n    }\n  ],\n  \"rejected_alternatives\": [\n    {\n      \"name\": \"Direct Curio Integration\",\n      \"proposer\": \"curio_advocate\",\n      \"rejection_reasons\": [\n        \"Curio project development has frozen with negligible community adoption\",\n        \"Maintaining custom multi-backend transports multiplies test matrix complexity\"\n      ],\n      \"key_objection_quote\": \"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.\",\n      \"objection_author\": \"florimondmanca\",\n      \"comment_id\": \"c-302\",\n      \"comment_url\": \"https://github.com/encode/httpx/issues/780#issuecomment-302\"\n    }\n  ]\n}"
        },
        {
          "stage_num": 3,
          "stage_name": "Decision Synthesis & Code Grounding",
          "model_name": "Qwen 2.5-Coder-7B-Instruct",
          "execution_time_ms": 0.02,
          "output": {
            "title": "ADR-780: Standardize on AnyIO Transport Abstraction",
            "status": "Accepted",
            "accepted_option": "Standardize on AnyIO for async backend compatibility",
            "considered_options": [
              "AnyIO Transport Abstraction",
              "Direct Curio Integration",
              "Native Trio Integration"
            ],
            "context": "HTTP transport layer architecture across Python asynchronous frameworks.",
            "decision_outcome": "Standardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.",
            "consequences_positive": [
              "Single transport codebase covering both Asyncio and Trio",
              "Significantly reduced test matrix and eliminated duplicate transport maintenance"
            ],
            "consequences_negative": [
              "Additional dependency on anyio abstraction package"
            ],
            "affected_components": [
              "httpx/_transports/default.py",
              "httpx/_transports/anyio.py"
            ],
            "evidence_quotes": [
              {
                "id": "eq-1",
                "quote": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.",
                "author": "florimondmanca",
                "comment_id": "c-302",
                "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-302",
                "verified": true,
                "confidence": 1.0,
                "context": "Objection regarding Curio maintenance freeze"
              },
              {
                "id": "eq-2",
                "quote": "Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.",
                "author": "tomchristie",
                "comment_id": "c-303",
                "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-303",
                "verified": true,
                "confidence": 1.0,
                "context": "Consensus on AnyIO abstraction"
              }
            ]
          },
          "raw_response": "{\n  \"title\": \"ADR-780: Standardize on AnyIO Transport Abstraction\",\n  \"status\": \"Accepted\",\n  \"accepted_option\": \"Standardize on AnyIO for async backend compatibility\",\n  \"considered_options\": [\n    \"AnyIO Transport Abstraction\",\n    \"Direct Curio Integration\",\n    \"Native Trio Integration\"\n  ],\n  \"context\": \"HTTP transport layer architecture across Python asynchronous frameworks.\",\n  \"decision_outcome\": \"Standardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.\",\n  \"consequences_positive\": [\n    \"Single transport codebase covering both Asyncio and Trio\",\n    \"Significantly reduced test matrix and eliminated duplicate transport maintenance\"\n  ],\n  \"consequences_negative\": [\n    \"Additional dependency on anyio abstraction package\"\n  ],\n  \"affected_components\": [\n    \"httpx/_transports/default.py\",\n    \"httpx/_transports/anyio.py\"\n  ],\n  \"evidence_quotes\": [\n    {\n      \"id\": \"eq-1\",\n      \"quote\": \"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.\",\n      \"author\": \"florimondmanca\",\n      \"comment_id\": \"c-302\",\n      \"comment_url\": \"https://github.com/encode/httpx/issues/780#issuecomment-302\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Objection regarding Curio maintenance freeze\"\n    },\n    {\n      \"id\": \"eq-2\",\n      \"quote\": \"Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.\",\n      \"author\": \"tomchristie\",\n      \"comment_id\": \"c-303\",\n      \"comment_url\": \"https://github.com/encode/httpx/issues/780#issuecomment-303\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Consensus on AnyIO abstraction\"\n    }\n  ]\n}"
        }
      ],
      "final_decision": {
        "id": "ADR-780",
        "discussion_id": "gh:encode/httpx/issues/780",
        "title": "ADR-780: Standardize on AnyIO Transport Abstraction",
        "status": "Accepted",
        "date": "2023-11-08",
        "context": "HTTP transport layer architecture across Python asynchronous frameworks.",
        "problem_statement": "Engineering evaluation and decision required for: Evaluate HTTP transport layer: Asyncio vs Trio native backend",
        "decision_outcome": "Standardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.",
        "accepted_option": "Standardize on AnyIO for async backend compatibility",
        "considered_options": [
          "AnyIO Transport Abstraction",
          "Direct Curio Integration",
          "Native Trio Integration"
        ],
        "rejected_alternatives": [
          {
            "name": "Direct Curio Integration",
            "proposer": "curio_advocate",
            "rejection_reasons": [
              "Curio project development has frozen with negligible community adoption",
              "Maintaining custom multi-backend transports multiplies test matrix complexity"
            ],
            "key_objection_quote": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.",
            "objection_author": "florimondmanca",
            "comment_id": "c-302",
            "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-302"
          }
        ],
        "consequences_positive": [
          "Single transport codebase covering both Asyncio and Trio",
          "Significantly reduced test matrix and eliminated duplicate transport maintenance"
        ],
        "consequences_negative": [
          "Additional dependency on anyio abstraction package"
        ],
        "affected_components": [
          "httpx/_transports/default.py",
          "httpx/_transports/anyio.py"
        ],
        "evidence_quotes": [
          {
            "id": "eq-1",
            "quote": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.",
            "author": "florimondmanca",
            "comment_id": "c-302",
            "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-302",
            "verified": true,
            "confidence": 1.0,
            "context": "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio. Maintaining a custom Curio transport br...",
            "char_offset": 0
          },
          {
            "id": "eq-2",
            "quote": "Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.",
            "author": "tomchristie",
            "comment_id": "c-303",
            "comment_url": "https://github.com/encode/httpx/issues/780#issuecomment-303",
            "verified": true,
            "confidence": 1.0,
            "context": "Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.",
            "char_offset": 0
          }
        ],
        "madr_content": "# ADR-780: Standardize on AnyIO Transport Abstraction\n\n* Status: **Accepted**\n* Date: 2023-11-08\n* Deciders: @curio_advocate, @florimondmanca, @tomchristie\n* Source Discussion: [Evaluate HTTP transport layer: Asyncio vs Trio native backend](https://github.com/encode/httpx/issues/780)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: Evaluate HTTP transport layer: Asyncio vs Trio native backend\n\nHTTP transport layer architecture across Python asynchronous frameworks.\n\n## Considered Options\n\n* AnyIO Transport Abstraction *(Rejected)*\n* Direct Curio Integration *(Rejected)*\n* Native Trio Integration *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Standardize on AnyIO for async backend compatibility**, because:\nStandardize on AnyIO for async backend compatibility. Reject direct Curio integration due to abandoned maintenance and low adoption. Reject duplicate native Trio transports in favour of AnyIO abstraction.\n\n### Positive Consequences\n\n* Single transport codebase covering both Asyncio and Trio\n* Significantly reduced test matrix and eliminated duplicate transport maintenance\n\n### Negative Consequences (Trade-offs)\n\n* Additional dependency on anyio abstraction package\n\n## Pros and Cons of Rejected Options\n\n### Direct Curio Integration\n* Proposed by: @curio_advocate\n* Rejection reasons:\n  * \u274c Curio project development has frozen with negligible community adoption\n  * \u274c Maintaining custom multi-backend transports multiplies test matrix complexity\n* Key objection quote: - @florimondmanca ([Source](https://github.com/encode/httpx/issues/780#issuecomment-302))\n  > \"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `httpx/_transports/default.py`\n* `httpx/_transports/anyio.py`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio.\" | @florimondmanca | \u2705 Verified | [Comment c-302](https://github.com/encode/httpx/issues/780#issuecomment-302) |\n| eq-2 | \"Instead of multiple custom transport implementations, using AnyIO gives us first-class support for both Asyncio and Trio with a single codebase. It drastically reduces our test matrix.\" | @tomchristie | \u2705 Verified | [Comment c-303](https://github.com/encode/httpx/issues/780#issuecomment-303) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
        "created_at": "2026-10-31T21:53:08.322205+00:00"
      },
      "total_time_ms": 0.1
    },
    "dc:discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823": {
      "discussion_id": "dc:discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823",
      "stages": [
        {
          "stage_num": 1,
          "stage_name": "Discussion Preprocessing & Summarization",
          "model_name": "Llama 3.2-3B-Instruct",
          "execution_time_ms": 0.02,
          "output": {
            "title": "PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)",
            "problem_statement": "Engineering evaluation and decision required for: PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)",
            "context_summary": "Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.",
            "participants": [
              "brettcannon"
            ],
            "identified_topics": [
              "Configuration Format",
              "Developer Experience",
              "Parser Security"
            ],
            "timeline_length": 0
          },
          "raw_response": "{\n  \"title\": \"PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)\",\n  \"problem_statement\": \"Engineering evaluation and decision required for: PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)\",\n  \"context_summary\": \"Discussion among 1 core contributors evaluating competing technical approaches and trade-offs.\",\n  \"participants\": [\n    \"brettcannon\"\n  ],\n  \"identified_topics\": [\n    \"Configuration Format\",\n    \"Developer Experience\",\n    \"Parser Security\"\n  ],\n  \"timeline_length\": 0\n}"
        },
        {
          "stage_num": 2,
          "stage_name": "Argument Mining & Rejected Alternatives Analysis",
          "model_name": "Phi-3.5-mini-instruct",
          "execution_time_ms": 0.01,
          "output": {
            "proposals": [
              {
                "id": "prop-1",
                "name": "External YAML dependency files",
                "proposer": "ci_maintainer_dan",
                "description": "Store test and CI dependencies in external dependencies.yaml.",
                "status": "rejected"
              },
              {
                "id": "prop-2",
                "name": "PEP 735 [dependency-groups] in pyproject.toml",
                "proposer": "brettcannon",
                "description": "Standardize dependency groups directly in pyproject.toml using standard TOML format.",
                "status": "accepted"
              }
            ],
            "arguments": [
              {
                "id": "arg-1",
                "proposal_id": "prop-1",
                "author": "pradyunsg",
                "stance": "con",
                "claim": "YAML introduces security CVEs and build frontend dependency",
                "reasoning": "Unwanted parser dependency and arbitrary code execution risk.",
                "quote": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools.",
                "comment_id": "post-402"
              }
            ],
            "rejected_alternatives": [
              {
                "name": "External YAML Dependencies",
                "proposer": "ci_maintainer_dan",
                "rejection_reasons": [
                  "Arbitrary code execution CVE risks and unwanted parser dependencies in bootstrap build tools",
                  "Fractured project metadata across non-standard external files"
                ],
                "key_objection_quote": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
                "objection_author": "pradyunsg",
                "comment_id": "post-402",
                "comment_url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3"
              }
            ]
          },
          "raw_response": "{\n  \"proposals\": [\n    {\n      \"id\": \"prop-1\",\n      \"name\": \"External YAML dependency files\",\n      \"proposer\": \"ci_maintainer_dan\",\n      \"description\": \"Store test and CI dependencies in external dependencies.yaml.\",\n      \"status\": \"rejected\"\n    },\n    {\n      \"id\": \"prop-2\",\n      \"name\": \"PEP 735 [dependency-groups] in pyproject.toml\",\n      \"proposer\": \"brettcannon\",\n      \"description\": \"Standardize dependency groups directly in pyproject.toml using standard TOML format.\",\n      \"status\": \"accepted\"\n    }\n  ],\n  \"arguments\": [\n    {\n      \"id\": \"arg-1\",\n      \"proposal_id\": \"prop-1\",\n      \"author\": \"pradyunsg\",\n      \"stance\": \"con\",\n      \"claim\": \"YAML introduces security CVEs and build frontend dependency\",\n      \"reasoning\": \"Unwanted parser dependency and arbitrary code execution risk.\",\n      \"quote\": \"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools.\",\n      \"comment_id\": \"post-402\"\n    }\n  ],\n  \"rejected_alternatives\": [\n    {\n      \"name\": \"External YAML Dependencies\",\n      \"proposer\": \"ci_maintainer_dan\",\n      \"rejection_reasons\": [\n        \"Arbitrary code execution CVE risks and unwanted parser dependencies in bootstrap build tools\",\n        \"Fractured project metadata across non-standard external files\"\n      ],\n      \"key_objection_quote\": \"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.\",\n      \"objection_author\": \"pradyunsg\",\n      \"comment_id\": \"post-402\",\n      \"comment_url\": \"https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3\"\n    }\n  ]\n}"
        },
        {
          "stage_num": 3,
          "stage_name": "Decision Synthesis & Code Grounding",
          "model_name": "Qwen 2.5-Coder-7B-Instruct",
          "execution_time_ms": 0.01,
          "output": {
            "title": "ADR-42823: Adopt PEP 735 Dependency Groups in pyproject.toml",
            "status": "Accepted",
            "accepted_option": "Adopt PEP 735 with [dependency-groups] in pyproject.toml",
            "considered_options": [
              "[dependency-groups] in pyproject.toml",
              "External YAML dependency files"
            ],
            "context": "Packaging metadata standardization for test, lint, and development dependencies.",
            "decision_outcome": "Consensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.",
            "consequences_positive": [
              "Single unified configuration file in pyproject.toml",
              "Full support across modern packaging backends without extra parser bloat"
            ],
            "consequences_negative": [
              "Requires updating older CI matrices to query pyproject.toml"
            ],
            "affected_components": [
              "pyproject.toml",
              "pip/_internal/req/req_file.py"
            ],
            "evidence_quotes": [
              {
                "id": "eq-1",
                "quote": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
                "author": "pradyunsg",
                "comment_id": "post-402",
                "comment_url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3",
                "verified": true,
                "confidence": 1.0,
                "context": "Objection rejecting YAML for dependency specification"
              }
            ]
          },
          "raw_response": "{\n  \"title\": \"ADR-42823: Adopt PEP 735 Dependency Groups in pyproject.toml\",\n  \"status\": \"Accepted\",\n  \"accepted_option\": \"Adopt PEP 735 with [dependency-groups] in pyproject.toml\",\n  \"considered_options\": [\n    \"[dependency-groups] in pyproject.toml\",\n    \"External YAML dependency files\"\n  ],\n  \"context\": \"Packaging metadata standardization for test, lint, and development dependencies.\",\n  \"decision_outcome\": \"Consensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.\",\n  \"consequences_positive\": [\n    \"Single unified configuration file in pyproject.toml\",\n    \"Full support across modern packaging backends without extra parser bloat\"\n  ],\n  \"consequences_negative\": [\n    \"Requires updating older CI matrices to query pyproject.toml\"\n  ],\n  \"affected_components\": [\n    \"pyproject.toml\",\n    \"pip/_internal/req/req_file.py\"\n  ],\n  \"evidence_quotes\": [\n    {\n      \"id\": \"eq-1\",\n      \"quote\": \"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.\",\n      \"author\": \"pradyunsg\",\n      \"comment_id\": \"post-402\",\n      \"comment_url\": \"https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3\",\n      \"verified\": true,\n      \"confidence\": 1.0,\n      \"context\": \"Objection rejecting YAML for dependency specification\"\n    }\n  ]\n}"
        }
      ],
      "final_decision": {
        "id": "ADR-42823",
        "discussion_id": "dc:discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823",
        "title": "ADR-42823: Adopt PEP 735 Dependency Groups in pyproject.toml",
        "status": "Accepted",
        "date": "2024-02-01",
        "context": "Packaging metadata standardization for test, lint, and development dependencies.",
        "problem_statement": "Engineering evaluation and decision required for: PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)",
        "decision_outcome": "Consensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.",
        "accepted_option": "Adopt PEP 735 with [dependency-groups] in pyproject.toml",
        "considered_options": [
          "[dependency-groups] in pyproject.toml",
          "External YAML dependency files"
        ],
        "rejected_alternatives": [
          {
            "name": "External YAML Dependencies",
            "proposer": "ci_maintainer_dan",
            "rejection_reasons": [
              "Arbitrary code execution CVE risks and unwanted parser dependencies in bootstrap build tools",
              "Fractured project metadata across non-standard external files"
            ],
            "key_objection_quote": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
            "objection_author": "pradyunsg",
            "comment_id": "post-402",
            "comment_url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3"
          }
        ],
        "consequences_positive": [
          "Single unified configuration file in pyproject.toml",
          "Full support across modern packaging backends without extra parser bloat"
        ],
        "consequences_negative": [
          "Requires updating older CI matrices to query pyproject.toml"
        ],
        "affected_components": [
          "pyproject.toml",
          "pip/_internal/req/req_file.py"
        ],
        "evidence_quotes": [
          {
            "id": "eq-1",
            "quote": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
            "author": "pradyunsg",
            "comment_id": "post-402",
            "comment_url": "https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3",
            "verified": true,
            "confidence": 1.0,
            "context": "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.",
            "char_offset": 0
          }
        ],
        "madr_content": "# ADR-42823: Adopt PEP 735 Dependency Groups in pyproject.toml\n\n* Status: **Accepted**\n* Date: 2024-02-01\n* Deciders: @brettcannon, @ci_maintainer_dan, @pradyunsg\n* Source Discussion: [PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)](https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823)\n\n## Context and Problem Statement\n\nEngineering evaluation and decision required for: PEP 735: Dependency groups in pyproject.toml (TOML arrays vs external YAML/requirements.txt)\n\nPackaging metadata standardization for test, lint, and development dependencies.\n\n## Considered Options\n\n* [dependency-groups] in pyproject.toml *(Chosen)*\n* External YAML dependency files *(Rejected)*\n\n## Decision Outcome\n\nChosen option: **Adopt PEP 735 with [dependency-groups] in pyproject.toml**, because:\nConsensus accepted: Adopt PEP 735 with [dependency-groups] in pyproject.toml. Reject external YAML dependency files due to security parser vulnerabilities and fragmentation.\n\n### Positive Consequences\n\n* Single unified configuration file in pyproject.toml\n* Full support across modern packaging backends without extra parser bloat\n\n### Negative Consequences (Trade-offs)\n\n* Requires updating older CI matrices to query pyproject.toml\n\n## Pros and Cons of Rejected Options\n\n### External YAML Dependencies\n* Proposed by: @ci_maintainer_dan\n* Rejection reasons:\n  * \u274c Arbitrary code execution CVE risks and unwanted parser dependencies in bootstrap build tools\n  * \u274c Fractured project metadata across non-standard external files\n* Key objection quote: - @pradyunsg ([Source](https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3))\n  > \"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.\"\n\n## Code Grounding & Impacted Components\n\nThe following files, modules, and directories are bound to this decision:\n\n* `pyproject.toml`\n* `pip/_internal/req/req_file.py`\n\n## Verified Evidence Citations\n\n| ID | Quote | Author | Verified | Source |\n|---|---|---|:---:|---|\n| eq-1 | \"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces arbitrary code execution CVE risks into packaging tools. Python packaging strictly standardized on TOML.\" | @pradyunsg | \u2705 Verified | [Comment post-402](https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3) |\n\n---\n*Generated by PRIMORDIAL Decision Intelligence Platform \u2014 Hacktoberfest 2026*",
        "created_at": "2026-10-31T21:53:08.322309+00:00"
      },
      "total_time_ms": 0.07
    }
  }
};

let currentDiscussion = null;
let currentPipelineResult = null;
let sampleDiscussions = OFFLINE_BUNDLE.samples || [];
let allDecisions = OFFLINE_BUNDLE.decisions || [];

// DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initHealthCheck();
  initSourceExplorer();
  initDecisionLibrary();
  initPRRadar();
  initEvaluation();
});

// Toast Notification System (Replaces all modal alerts!)
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icons = {
    success: "✔",
    warning: "⚠️",
    error: "❌",
    info: "ℹ️",
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || "ℹ️"}</span>
    <span class="toast-msg">${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "fadeOutToast 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards";
    setTimeout(() => {
      if (toast.parentElement) toast.parentElement.removeChild(toast);
    }, 300);
  }, 3500);
}

// 1. Navigation Tabs
function initNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const tabId = tab.dataset.tab;
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-tab").forEach((t) => t.classList.remove("active"));
  document.querySelectorAll(".tab-view").forEach((v) => v.classList.remove("active"));

  const targetTab = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  const targetView = document.getElementById(`tab-${tabId}`);
  if (targetTab && targetView) {
    targetTab.classList.add("active");
    targetView.classList.add("active");
  }

  // Trigger tab-specific refresh if needed
  if (tabId === "library") {
    loadDecisions();
  } else if (tabId === "evaluation") {
    runEvaluationBenchmark(false);
  }
}

// 2. Health Check & AI Engine Status
async function initHealthCheck() {
  const statusLabel = document.getElementById("ai-status-label");
  const statusPill = document.getElementById("ai-status-pill");

  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error("Health check failed");
    const data = await res.json();

    const engine = data.ai_engine || {};
    if (engine.connected && engine.adapter === "OllamaAdapter") {
      const installed = engine.installed_models || [];
      const required = Object.values(engine.required_stage_models || {});
      const missing = required.filter((tag) => !installed.some((name) => name === tag || name.startsWith(`${tag.split(":")[0]}:`)));
      statusLabel.textContent = missing.length
        ? `Ollama connected · missing ${missing.join(", ")}`
        : `Ollama model inference`;
      statusPill.className = "status-pill status-ready";
    } else if (engine.adapter === "HeuristicFallbackAdapter") {
      statusLabel.textContent = `Heuristic fallback · no model inference`;
      statusPill.className = "status-pill";
    } else {
      statusLabel.textContent = `Inference engine unavailable`;
      statusPill.className = "status-pill";
    }
  } catch (err) {
    statusLabel.textContent = `Inference engine unavailable`;
    statusPill.className = "status-pill";
  }
}

// 3. Source Explorer
async function initSourceExplorer() {
  // Load sample discussions
  try {
    const res = await fetch("/api/samples");
    if (res.ok) {
      sampleDiscussions = await res.json();
    }
  } catch (err) {
    // Offline mode: use built-in samples
  }
  if (sampleDiscussions.length > 0) {
    displayDiscussion(sampleDiscussions[0]);
  }

  // Quick preset buttons
  const chipButtons = document.querySelectorAll(".quick-buttons .btn-chip");
  chipButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.sampleIdx, 10);
      if (sampleDiscussions[idx]) {
        const disc = sampleDiscussions[idx];
        document.getElementById("discussion-url-input").value = disc.source_url;
        displayDiscussion(disc);
        showToast(`Loaded benchmark thread: ${disc.title.slice(0, 50)}...`, "info");
      }
    });
  });

  // Fetch button
  const btnFetch = document.getElementById("btn-fetch");
  btnFetch.addEventListener("click", async () => {
    const url = document.getElementById("discussion-url-input").value.trim();
    if (!url) {
      showToast("Please enter a discussion URL or topic keyword", "warning");
      return;
    }

    btnFetch.disabled = true;
    btnFetch.innerHTML = `<span class="btn-icon">⏳</span> Fetching...`;

    try {
      const res = await fetch("/api/discussions/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody({ url }),
      });
      if (res.ok) {
        const disc = await res.json();
        displayDiscussion(disc);
        showToast(`Loaded: ${disc.title}`, "success");
        return;
      }
    } catch (e) {
      // Offline fallback: match by keyword or URL
    } finally {
      btnFetch.disabled = false;
      btnFetch.innerHTML = `<span class="btn-icon">⚡</span> Fetch Discussion`;
    }

    // Offline matching logic (works on file:// and without live server)
    const q = url.toLowerCase();
    let matched = sampleDiscussions[0];
    if (q.includes("python") || q.includes("pep") || q.includes("42823") || q.includes("discuss")) {
      matched = sampleDiscussions.find((d) => d.id && d.id.includes("42823")) || sampleDiscussions[3] || matched;
    } else if (q.includes("88219") || q.includes("discourse") || q.includes("rocksdb") || q.includes("sqlite") || q.includes("cache")) {
      matched = sampleDiscussions.find((d) => d.id && d.id.includes("88219")) || sampleDiscussions[1] || matched;
    } else if (q.includes("780") || q.includes("httpx") || q.includes("anyio") || q.includes("curio") || q.includes("async")) {
      matched = sampleDiscussions.find((d) => d.id && d.id.includes("780")) || sampleDiscussions[2] || matched;
    } else if (q.includes("1042") || q.includes("uv") || q.includes("toml") || q.includes("yaml")) {
      matched = sampleDiscussions.find((d) => d.id && d.id.includes("1042")) || sampleDiscussions[0] || matched;
    }
    displayDiscussion(matched);
    showToast(`Loaded: ${matched.title}`, "success");
  });

  // Run Pipeline Button
  const btnPipeline = document.getElementById("btn-run-pipeline");
  btnPipeline.addEventListener("click", runPipeline);
}

function displayDiscussion(disc) {
  currentDiscussion = disc;

  document.getElementById("disc-source-type").textContent = disc.source_type;
  document.getElementById("disc-title").textContent = disc.title;
  document.getElementById("disc-author").textContent = `@${disc.author}`;
  document.getElementById("disc-date").textContent = disc.created_at ? disc.created_at.slice(0, 10) : "";
  document.getElementById("disc-messages-count").textContent = `${disc.comments ? disc.comments.length : 0} comments`;

  const link = document.getElementById("disc-url-link");
  link.href = disc.source_url;
  link.textContent = `${disc.source_type === "github" ? "GitHub" : "Discourse"} Thread ↗`;

  // Labels
  const labelsContainer = document.getElementById("disc-labels-container");
  labelsContainer.innerHTML = "";
  (disc.labels || []).forEach((label) => {
    const span = document.createElement("span");
    span.className = "badge badge-neutral";
    span.textContent = label;
    labelsContainer.appendChild(span);
  });

  // Comments stream
  const stream = document.getElementById("discussion-comments-list");
  stream.innerHTML = "";

  // OP Card
  const opCard = document.createElement("div");
  opCard.className = "comment-card is-op";
  opCard.innerHTML = `
    <div class="comment-header">
      <div class="author-wrap">
        <span class="badge badge-source">TOPIC OP</span>
        <span class="author-name">@${disc.author}</span>
      </div>
      <span class="comment-date">${disc.created_at ? disc.created_at.replace("T", " ").replace("Z", "") : ""}</span>
    </div>
    <div class="comment-body">${escapeHtml(disc.description)}</div>
  `;
  stream.appendChild(opCard);

  // Subsequent comments
  (disc.comments || []).forEach((c) => {
    const card = document.createElement("div");
    card.className = "comment-card";
    card.innerHTML = `
      <div class="comment-header">
        <div class="author-wrap">
          <span class="author-name">@${c.author}</span>
          <span class="badge badge-neutral">${c.id}</span>
        </div>
        <span class="comment-date">${c.created_at ? c.created_at.replace("T", " ").replace("Z", "") : ""}</span>
      </div>
      <div class="comment-body">${escapeHtml(c.body)}</div>
    `;
    stream.appendChild(card);
  });
}

// 4. Run Multi-Stage Pipeline
async function runPipeline() {
  if (!currentDiscussion) return;

  const btn = document.getElementById("btn-run-pipeline");
  btn.disabled = true;
  btn.innerHTML = `<span class="btn-icon">⏳</span> Executing Pipeline...`;

  // Switch to Discussion Intelligence tab
  switchTab("intelligence");

  // Animate stages
  setStageState(1, "running", "Processing discussion thread...");
  setStageState(2, "pending", "Waiting for stage 1...");
  setStageState(3, "pending", "Waiting for stage 2...");

  try {
    const res = await fetch("/api/pipeline/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonBody({ discussion_id: currentDiscussion.id }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Pipeline error");
    }

    const result = await res.json();
    currentPipelineResult = result;

    // Update stages display
    result.stages.forEach((st) => {
      const modelLabel = document.getElementById(`stage${st.stage_num}-model`);
      if (modelLabel) modelLabel.textContent = st.model_name;
      setStageState(st.stage_num, "completed", "Done", `${st.execution_time_ms} ms`);
    });

    document.getElementById("pipeline-total-time").innerHTML = `
      <span>⏱️ Total Pipeline Time: <strong>${result.total_time_ms} ms</strong></span>
    `;

    renderIntelligenceView(result);
    showToast(`Decision recovered in ${result.total_time_ms} ms!`, "success");
  } catch (err) {
    currentPipelineResult = null;
    document.getElementById("pipeline-total-time").innerHTML = `
      <span>⏱️ Total Pipeline Time: <strong>Not run</strong></span>
    `;
    showToast(`Pipeline failed: ${err.message}. No cached result was substituted.`, "warning");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="btn-icon">🧠</span> Run 3-Stage Decision Pipeline`;
  }
}

function setStageState(stageNum, state, statusText, timeText = "") {
  const card = document.getElementById(`stage-card-${stageNum}`);
  const statusEl = document.getElementById(`stage${stageNum}-status`);
  const timeEl = document.getElementById(`stage${stageNum}-time`);

  card.classList.remove("running", "completed");
  if (state === "running") card.classList.add("running");
  if (state === "completed") card.classList.add("completed");

  statusEl.textContent = state === "completed" ? "✔ Done" : (state === "running" ? "● Analyzing..." : "○ Ready");
  statusEl.className = `stage-status ${state === "completed" ? "done" : ""}`;
  if (timeText) timeEl.textContent = timeText;
}

// Render Discussion Intelligence View
function renderIntelligenceView(pipelineResult) {
  const s1 = pipelineResult.stages.find((s) => s.stage_num === 1)?.output || {};
  const s2 = pipelineResult.stages.find((s) => s.stage_num === 2)?.output || {};
  const decision = pipelineResult.final_decision || {};

  // Overview
  document.getElementById("intel-problem-statement").textContent =
    s1.problem_statement || decision.problem_statement || "Technical debate";
  document.getElementById("intel-context").textContent =
    s1.context_summary || decision.context || "";

  // Participants
  const participantsWrap = document.getElementById("intel-participants-pills");
  participantsWrap.innerHTML = "";
  (s1.participants || currentDiscussion?.participants || []).forEach((p) => {
    const pill = document.createElement("span");
    pill.className = "participant-pill";
    pill.textContent = `@${p}`;
    participantsWrap.appendChild(pill);
  });

  // Proposals
  const propList = document.getElementById("proposals-list");
  propList.innerHTML = "";
  const proposals = s2.proposals || [];
  document.getElementById("proposals-count").textContent = `${proposals.length} proposals`;

  proposals.forEach((p) => {
    const item = document.createElement("div");
    const isAccepted = p.status === "accepted";
    item.className = `proposal-item ${isAccepted ? "accepted" : "rejected"}`;
    item.innerHTML = `
      <div class="prop-title-row">
        <span class="prop-title">${escapeHtml(p.name)}</span>
        <span class="badge ${isAccepted ? "badge-accepted" : "badge-danger"}">${p.status}</span>
      </div>
      <p class="prop-desc">${escapeHtml(p.description)}</p>
      <span class="stream-hint">Proposed by @${p.proposer}</span>
    `;
    propList.appendChild(item);
  });

  // REJECTED ALTERNATIVES (PS 06 Centerpiece!)
  const rejectedList = document.getElementById("rejected-alternatives-list");
  rejectedList.innerHTML = "";
  const rejectedAlts = s2.rejected_alternatives || decision.rejected_alternatives || [];
  document.getElementById("rejected-count").textContent = `${rejectedAlts.length} rejected`;

  if (rejectedAlts.length === 0) {
    rejectedList.innerHTML = `<p class="stream-hint">No rejected alternatives extracted for this thread.</p>`;
  } else {
    rejectedAlts.forEach((ra) => {
      const card = document.createElement("div");
      card.className = "rejected-card";

      const reasonsHtml = (ra.rejection_reasons || [])
        .map((r) => `<li><span>❌</span> <span>${escapeHtml(r)}</span></li>`)
        .join("");

      card.innerHTML = `
        <div class="rejected-header">
          <div>
            <h4 class="rejected-name">${escapeHtml(ra.name)}</h4>
            <span class="rejected-proposer">Proposed by @${ra.proposer}</span>
          </div>
          <span class="badge badge-danger">Rejected Option</span>
        </div>

        <div class="reasons-title">Recovered Engineering Reasons:</div>
        <ul class="reasons-list">
          ${reasonsHtml}
        </ul>

        ${
          ra.key_objection_quote
            ? `
          <div class="objection-quote-box">
            "${escapeHtml(ra.key_objection_quote)}"
            <span class="objection-by">— @${ra.objection_author || "maintainer"} ${
                ra.comment_url
                  ? `(<a href="${ra.comment_url}" target="_blank" class="external-link">View in Source</a>)`
                  : ""
              }</span>
          </div>
        `
            : ""
        }
      `;
      rejectedList.appendChild(card);
    });
  }
}

// 5. Decision Library
async function initDecisionLibrary() {
  const searchInput = document.getElementById("library-search-input");
  const filterSelect = document.getElementById("library-status-filter");

  searchInput.addEventListener("input", debounce(() => loadDecisions(), 250));
  filterSelect.addEventListener("change", () => loadDecisions());

  // Modal close
  document.getElementById("btn-close-modal").addEventListener("click", () => {
    document.getElementById("decision-modal").classList.add("hidden");
  });

  // Modal tabs
  const modalTabs = document.querySelectorAll(".modal-tab");
  modalTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      modalTabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".modal-tab-content").forEach((c) => c.classList.remove("active"));

      tab.classList.add("active");
      const targetContent = document.getElementById(`modal-tab-${tab.dataset.modaltab}`);
      if (targetContent) targetContent.classList.add("active");
    });
  });

  // Copy MADR button
  document.getElementById("btn-copy-madr").addEventListener("click", () => {
    const text = document.getElementById("modal-madr-code").textContent;
    navigator.clipboard.writeText(text).then(() => {
      const btn = document.getElementById("btn-copy-madr");
      btn.textContent = "✔ Copied!";
      showToast("MADR markdown copied to clipboard", "success");
      setTimeout(() => (btn.textContent = "📋 Copy Markdown"), 2000);
    });
  });

  await loadDecisions();
}

async function loadDecisions() {
  const q = document.getElementById("library-search-input")?.value || "";
  const status = document.getElementById("library-status-filter")?.value || "";

  try {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status) params.set("status", status);

    const res = await fetch(`/api/decisions?${params.toString()}`);
    if (res.ok) {
      allDecisions = await res.json();
      renderDecisionsGrid(allDecisions);
      return;
    }
  } catch (err) {
    // Offline fallback
  }

  // Filter in memory
  let filtered = (OFFLINE_BUNDLE.decisions || []);
  if (status) filtered = filtered.filter(d => d.status.toLowerCase() === status.toLowerCase());
  if (q) {
    const term = q.toLowerCase();
    filtered = filtered.filter(d =>
      d.title.toLowerCase().includes(term) ||
      d.decision_outcome.toLowerCase().includes(term) ||
      (d.rejected_alternatives || []).some(ra => ra.name.toLowerCase().includes(term))
    );
  }
  allDecisions = filtered;
  renderDecisionsGrid(allDecisions);
}

function renderDecisionsGrid(decisions) {
  const grid = document.getElementById("decisions-grid");
  grid.innerHTML = "";

  if (decisions.length === 0) {
    grid.innerHTML = `<div class="stream-hint" style="grid-column: 1/-1; padding: 2rem; text-align: center;">No decision records match your query.</div>`;
    return;
  }

  decisions.forEach((dec) => {
    const card = document.createElement("div");
    card.className = "decision-card";

    const rejectedPills = (dec.rejected_alternatives || [])
      .map((ra) => `<span class="rejected-tag">Rejected: ${escapeHtml(ra.name)}</span>`)
      .join("");

    card.innerHTML = `
      <div>
        <div class="dec-header">
          <span class="badge badge-accepted">${dec.status}</span>
          <span class="stream-hint">${dec.id}</span>
        </div>
        <h4 class="dec-title">${escapeHtml(dec.title)}</h4>
        <p class="dec-outcome">${escapeHtml(dec.decision_outcome ? dec.decision_outcome.slice(0, 160) + "..." : "")}</p>
        <div class="dec-rejected-pills">${rejectedPills}</div>
      </div>
      <div class="dec-footer">
        <span>📅 ${dec.date || "Recent"}</span>
        <span class="external-link">View Full ADR →</span>
      </div>
    `;

    card.addEventListener("click", () => openDecisionModal(dec));
    grid.appendChild(card);
  });
}

function openDecisionModal(dec) {
  document.getElementById("modal-adr-badge").textContent = dec.status;
  document.getElementById("modal-adr-title").textContent = dec.title;
  document.getElementById("modal-context-text").textContent = dec.context || dec.problem_statement;
  document.getElementById("modal-outcome-text").textContent = dec.decision_outcome;

  // Positives & Negatives
  const posList = document.getElementById("modal-positives-list");
  posList.innerHTML = (dec.consequences_positive || []).map((p) => `<li>${escapeHtml(p)}</li>`).join("");

  const negList = document.getElementById("modal-negatives-list");
  negList.innerHTML = (dec.consequences_negative || []).map((n) => `<li>${escapeHtml(n)}</li>`).join("");

  // Affected components
  const compWrap = document.getElementById("modal-components-pills");
  compWrap.innerHTML = (dec.affected_components || [])
    .map((c) => `<span class="component-pill">${escapeHtml(c)}</span>`)
    .join("");

  // Rejected alternatives
  const rejCards = document.getElementById("modal-rejected-cards");
  rejCards.innerHTML = (dec.rejected_alternatives || [])
    .map(
      (ra) => `
    <div class="rejected-card" style="margin-bottom: 0.75rem;">
      <div class="rejected-header">
        <h5 class="rejected-name">${escapeHtml(ra.name)}</h5>
        <span class="badge badge-danger">Rejected</span>
      </div>
      <ul class="reasons-list">
        ${(ra.rejection_reasons || []).map((r) => `<li>❌ ${escapeHtml(r)}</li>`).join("")}
      </ul>
      ${ra.key_objection_quote ? `<div class="objection-quote-box">"${escapeHtml(ra.key_objection_quote)}"</div>` : ""}
    </div>
  `
    )
    .join("");

  // MADR View
  document.getElementById("modal-madr-code").textContent = dec.madr_content || "MADR content unavailable";

  // Evidence Quotes View
  const evidenceWrap = document.getElementById("modal-evidence-table");
  evidenceWrap.innerHTML = (dec.evidence_quotes || [])
    .map(
      (eq) => `
    <div class="evidence-quote-item">
      <div class="evidence-top">
        <span class="badge ${eq.verified ? "badge-accepted" : "badge-neutral"}">
          ${eq.verified ? "✔ Verified Grounded Quote" : "⚠ Paraphrased"}
        </span>
        <span class="stream-hint">Confidence: ${(eq.confidence * 100).toFixed(0)}%</span>
      </div>
      <div class="evidence-quote-text">"${escapeHtml(eq.quote)}"</div>
      <div class="evidence-bottom">
        <span>By @${eq.author} (${eq.comment_id})</span>
        ${eq.comment_url ? `<a href="${eq.comment_url}" target="_blank" class="external-link">Inspect Source ↗</a>` : ""}
      </div>
    </div>
  `
    )
    .join("");

  // JSON View
  document.getElementById("modal-json-code").textContent = JSON.stringify(dec, null, 2);

  // Show modal
  document.getElementById("decision-modal").classList.remove("hidden");
}

// 6. Historical PR Decision Radar
function initPRRadar() {
  const btnScan = document.getElementById("btn-scan-radar");
  const btnYaml = document.getElementById("btn-preset-yaml");
  const btnRocks = document.getElementById("btn-preset-rocksdb");
  const btnClean = document.getElementById("btn-preset-clean");

  // Automatically populate AND immediately scan on preset click!
  btnYaml.addEventListener("click", () => {
    document.getElementById("pr-title-input").value = "Add YAML parser support for CI workflow templates";
    document.getElementById("pr-desc-input").value =
      "This pull request adds PyYAML dependency so users can configure uv using YAML format (.uv.yaml) directly inside their CI matrices.";
    document.getElementById("pr-files-input").value = "uv.yaml\nconfig/loader.py\ncrates/uv-settings/src/yaml_parser.rs";
    document.getElementById("pr-diff-input").value = "+ import yaml\n+ def load_yaml_config(path):\n+     with open(path) as f:\n+         return yaml.safe_load(f)";
    runPRScan();
  });

  btnRocks.addEventListener("click", () => {
    document.getElementById("pr-title-input").value = "Add RocksDB storage backend for edge telemetry cache";
    document.getElementById("pr-desc-input").value =
      "Replaces the default SQLite cache with RocksDB LSM-tree to improve peak write throughput for distributed edge nodes.";
    document.getElementById("pr-files-input").value = "lib/storage/edge_cache.rb\nconfig/storage.yml\nsrc/storage/rocksdb_driver.cc";
    document.getElementById("pr-diff-input").value = "+ require 'rocksdb'\n+ class EdgeCache::RocksBackend\n+   def initialize\n+     @db = RocksDB.open('/var/data/edge')";
    runPRScan();
  });

  btnClean.addEventListener("click", () => {
    document.getElementById("pr-title-input").value = "Bump toml-rs version and optimize TOML parser buffer";
    document.getElementById("pr-desc-input").value = "Updates the TOML deserializer crate to latest version and optimizes memory allocations.";
    document.getElementById("pr-files-input").value = "Cargo.toml\ncrates/uv-settings/Cargo.toml";
    document.getElementById("pr-diff-input").value = "- toml = \"0.8.0\"\n+ toml = \"0.8.10\"";
    runPRScan();
  });

  btnScan.addEventListener("click", runPRScan);
}

async function runPRScan() {
  const title = document.getElementById("pr-title-input").value.trim();
  const description = document.getElementById("pr-desc-input").value.trim();
  const filesRaw = document.getElementById("pr-files-input").value.trim();
  const diff = document.getElementById("pr-diff-input").value.trim();

  const changed_files = filesRaw.split("\n").map((f) => f.trim()).filter(Boolean);

  const btn = document.getElementById("btn-scan-radar");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-icon">⏳</span> Scanning PR...`;
  }

  try {
    const res = await fetch("/api/radar/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonBody({
        pr_id: "PR-simulated-01",
        title,
        description,
        changed_files,
        patch_diff: diff,
      }),
    });

    if (res.ok) {
      const result = await res.json();
      renderRadarAlerts(result);
      if ((result.alerts || []).length > 0) {
        showToast(`Radar Conflict Detected: ${result.alerts[0].rejected_alternative || "Architectural constraint"}`, "warning");
      } else {
        showToast("Radar Scan Clean: No regressions or rejected alternatives detected", "success");
      }
      return;
    }
  } catch (e) {
    // Offline simulation mode (when opened directly via file://)
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span class="btn-icon">🛰️</span> Run Radar Scan`;
    }
  }

  // Client-side radar analysis
  const checkText = `${title} ${description} ${diff}`.toLowerCase();
  let alerts = [];

  if (checkText.includes("rocksdb")) {
    alerts.push({
      id: "alert-rocksdb-88219",
      severity: "high",
      matched_decision_id: "ADR-88219",
      matched_decision_title: "ADR-88219: Adopt SQLite with WAL for Edge Cache Storage",
      conflict_type: "resurrected_rejected_alternative",
      rejected_alternative: "RocksDB Storage Engine",
      message: "⚠️ Caution: PR appears to re-propose or introduce 'RocksDB Storage Engine', which was previously DEBATED AND REJECTED in ADR-88219.",
      historical_context: "In ADR-88219: Adopt SQLite with WAL for Edge Cache Storage (Decided: 2024-01-22), the team rejected 'RocksDB Engine' for the following reasons: 85MB binary bloat in distribution images; Severe ARM64 cross-compilation & jemalloc build failures; Operational maintenance of LSM compaction tuning.",
      matched_files: changed_files.filter(f => f.includes("edge_cache") || f.includes("storage") || f.includes("rocksdb")),
      evidence_link: "https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3"
    });
  } else if (checkText.includes("yaml")) {
    alerts.push({
      id: "alert-yaml-1042",
      severity: "high",
      matched_decision_id: "ADR-1042",
      matched_decision_title: "ADR-1042: Standardize on TOML Configuration Format",
      conflict_type: "resurrected_rejected_alternative",
      rejected_alternative: "YAML Configuration (.uv.yaml)",
      message: "⚠️ Caution: PR appears to re-propose or introduce 'YAML Configuration (.uv.yaml)', which was previously DEBATED AND REJECTED in ADR-1042.",
      historical_context: "In ADR-1042: Standardize on TOML Configuration Format (Decided: 2024-03-15), the team rejected 'YAML Configuration (.uv.yaml)' for the following reasons: Severe security risks and arbitrary code execution CVEs in standard YAML parsers; Norway problem ('NO' interpreted as boolean False) causing silent configuration errors.",
      matched_files: changed_files.filter(f => f.includes("yaml") || f.includes("loader") || f.includes("config")),
      evidence_link: "https://github.com/astral-sh/uv/issues/1042#issuecomment-102"
    });
  } else if (checkText.includes("curio")) {
    alerts.push({
      id: "alert-curio-780",
      severity: "high",
      matched_decision_id: "ADR-780",
      matched_decision_title: "ADR-780: Adopt AnyIO Multi-Backend Async Transport Layer",
      conflict_type: "resurrected_rejected_alternative",
      rejected_alternative: "Curio Async Kernel",
      message: "⚠️ Caution: PR appears to re-propose or introduce 'Curio Async Kernel', which was previously DEBATED AND REJECTED in ADR-780.",
      historical_context: "In ADR-780: Adopt AnyIO Multi-Backend Async Transport Layer (Decided: 2023-11-14), the team rejected 'Curio Kernel' for the following reasons: Upstream maintenance stalled; missing nursery cancellation semantics compared to Trio/AnyIO; incompatible with modern Python 3.12 exception groups.",
      matched_files: changed_files.filter(f => f.includes("curio") || f.includes("transport") || f.includes("async")),
      evidence_link: "https://github.com/encode/httpx/issues/780#issuecomment-780"
    });
  }

  const result = {
    pr_id: "PR-simulated-01",
    title,
    scanned_decisions_count: 4,
    alerts_count: alerts.length,
    alerts
  };

  renderRadarAlerts(result);
  if (alerts.length > 0) {
    showToast(`Radar Conflict Detected: ${alerts[0].rejected_alternative}`, "warning");
  } else {
    showToast("Radar Scan Clean: No regressions detected", "success");
  }
}

function renderRadarAlerts(result) {
  const emptyState = document.getElementById("radar-empty-state");
  const alertsContainer = document.getElementById("radar-alerts-container");
  const badge = document.getElementById("radar-alerts-badge");

  const alerts = result.alerts || [];
  badge.textContent = `${alerts.length} alert${alerts.length === 1 ? "" : "s"}`;
  badge.className = `badge ${alerts.length > 0 ? "badge-danger" : "badge-accepted"}`;

  emptyState.classList.add("hidden");
  alertsContainer.classList.remove("hidden");
  alertsContainer.innerHTML = "";

  if (alerts.length === 0) {
    alertsContainer.innerHTML = `
      <div class="glass-card" style="text-align: center; padding: 2.5rem; border-color: var(--border-emerald);">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✅</div>
        <h4 style="color: var(--accent-emerald); font-size: 1.15rem; margin-bottom: 0.5rem;">No Architectural Regressions Detected</h4>
        <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 440px; margin: 0 auto;">
          This pull request does not re-introduce any previously rejected alternatives or violate governed architectural constraints.
        </p>
      </div>
    `;
    return;
  }

  alerts.forEach((alert) => {
    const card = document.createElement("div");
    const isHigh = alert.severity === "high";
    card.className = `radar-alert-card ${isHigh ? "alert-high" : "alert-medium"}`;

    const filesPills = (alert.matched_files || [])
      .map((f) => `<span class="file-pill">${escapeHtml(f)}</span>`)
      .join("");

    card.innerHTML = `
      <div class="alert-header">
        <div class="alert-title-wrap">
          <span class="alert-icon">${isHigh ? "🚨" : "ℹ️"}</span>
          <span class="alert-headline">${isHigh ? "CRITICAL: Resurrected Rejected Alternative" : "Architectural Notice"}</span>
        </div>
        <span class="badge ${isHigh ? "badge-danger" : "badge-neutral"}">${alert.matched_decision_id}</span>
      </div>

      <div class="alert-message">${escapeHtml(alert.message)}</div>

      <div class="alert-context-box">
        <strong>Historical Precedent:</strong> ${escapeHtml(alert.historical_context)}
      </div>

      <div class="alert-files-row">
        <span>Matched files:</span>
        ${filesPills}
      </div>
    `;
    alertsContainer.appendChild(card);
  });
}

// 7. Evaluation & Benchmarks
let currentMetricFilter = "summary";
let lastEvaluationMetrics = null;

function initEvaluation() {
  const btnRun = document.getElementById("btn-run-eval");
  if (btnRun) {
    btnRun.addEventListener("click", () => runEvaluationBenchmark(true));
  }

  // Interactive toggle on all 4 metric cards!
  const metricCards = document.querySelectorAll(".metric-card");
  metricCards.forEach((card) => {
    card.addEventListener("click", () => {
      const metricType = card.dataset.metric;
      if (!metricType) return;

      if (card.classList.contains("active") && currentMetricFilter === metricType) {
        // Toggle OFF to full overview summary!
        card.classList.remove("active");
        currentMetricFilter = "summary";
        renderEvaluationView("summary");
        showToast("Restored full benchmark summary overview", "info");
        return;
      }

      metricCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      currentMetricFilter = metricType;

      renderEvaluationView(currentMetricFilter);
      const label = card.querySelector(".metric-label")?.textContent || "Metric";
      showToast(`Filter: ${label}`, "info");
    });
  });

  const filterBadge = document.getElementById("eval-table-filter-badge");
  if (filterBadge) {
    filterBadge.addEventListener("click", () => {
      metricCards.forEach((c) => c.classList.remove("active"));
      currentMetricFilter = "summary";
      renderEvaluationView("summary");
      showToast("Showing benchmark summary", "info");
    });
  }
}

function renderEvaluationView(metricType) {
  const thead = document.getElementById("evaluation-table-head");
  const tbody = document.getElementById("evaluation-table-body");
  const heading = document.getElementById("eval-table-heading");
  const subheading = document.getElementById("eval-table-subheading");
  const filterBadge = document.getElementById("eval-table-filter-badge");

  if (!thead || !tbody) return;

  if (metricType === "summary") {
    heading.textContent = "Curated Architectural Benchmarks";
    if (subheading) subheading.textContent = "";
    filterBadge.textContent = "4 Curated Cases";
    filterBadge.className = "badge badge-source";

    thead.innerHTML = `
      <tr>
        <th>Benchmark Case</th>
        <th>Source Domain</th>
        <th>Accepted Outcome</th>
        <th>Target Rejected Alternatives</th>
        <th>Evidence Verification</th>
        <th>Status</th>
      </tr>
    `;

    tbody.innerHTML = `
      <tr>
        <td><strong>uv: Config Format Selection</strong></td>
        <td><a href="https://github.com/astral-sh/uv/issues/1042" target="_blank" class="external-link">astral-sh/uv#1042 ↗</a></td>
        <td><span class="badge badge-accepted">TOML</span></td>
        <td><span class="badge badge-danger">YAML (CVEs/Norway)</span> <span class="badge badge-danger">JSON (No comments)</span></td>
        <td>3 fixture quote checks</td>
        <td><span class="badge badge-source">Fixture</span></td>
      </tr>
      <tr>
        <td><strong>Discourse: Edge Cache Storage</strong></td>
        <td><a href="https://meta.discourse.org/t/embedded-cache-storage-engine/88219" target="_blank" class="external-link">meta.discourse.org#88219 ↗</a></td>
        <td><span class="badge badge-accepted">SQLite WAL</span></td>
        <td><span class="badge badge-danger">RocksDB (85MB Bloat/ARM)</span></td>
        <td>2 fixture quote checks</td>
        <td><span class="badge badge-source">Fixture</span></td>
      </tr>
      <tr>
        <td><strong>httpx: Async Transport Layer</strong></td>
        <td><a href="https://github.com/encode/httpx/issues/780" target="_blank" class="external-link">encode/httpx#780 ↗</a></td>
        <td><span class="badge badge-accepted">AnyIO Abstraction</span></td>
        <td><span class="badge badge-danger">Curio (Frozen maintenance)</span></td>
        <td>2 fixture quote checks</td>
        <td><span class="badge badge-source">Fixture</span></td>
      </tr>
      <tr>
        <td><strong>Python: PEP 735 Groups</strong></td>
        <td><a href="https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823" target="_blank" class="external-link">discuss.python.org#42823 ↗</a></td>
        <td><span class="badge badge-accepted">pyproject.toml</span></td>
        <td><span class="badge badge-danger">YAML Files</span></td>
        <td>1 fixture quote check</td>
        <td><span class="badge badge-source">Fixture</span></td>
      </tr>
    `;
    return;
  }

  if (metricType === "decisions") {
    heading.textContent = "Accepted Decisions & Consensus Outcomes";
    if (subheading) subheading.textContent = "";
    filterBadge.textContent = "Curated fixture cases";
    filterBadge.className = "badge badge-source";

    thead.innerHTML = `
      <tr>
        <th>Benchmark Case</th>
        <th>Source Discussion</th>
        <th>Problem Statement</th>
        <th>Accepted Consensus Outcome</th>
        <th>Status</th>
      </tr>
    `;

    tbody.innerHTML = `
      <tr>
        <td><strong>uv: Config Format Selection</strong></td>
        <td><a href="https://github.com/astral-sh/uv/issues/1042" target="_blank" class="external-link">astral-sh/uv#1042 ↗</a></td>
        <td>Standardize configuration file format across CLI & project settings</td>
        <td><span class="badge badge-accepted">TOML (pyproject.toml / uv.toml)</span></td>
        <td><span class="badge badge-source">Expected fixture outcome</span></td>
      </tr>
      <tr>
        <td><strong>Discourse: Edge Cache Storage</strong></td>
        <td><a href="https://meta.discourse.org/t/embedded-cache-storage-engine/88219" target="_blank" class="external-link">meta.discourse.org#88219 ↗</a></td>
        <td>Crash-resilient embedded store with low binary footprint</td>
        <td><span class="badge badge-accepted">SQLite in WAL Mode</span></td>
        <td><span class="badge badge-source">Expected fixture outcome</span></td>
      </tr>
      <tr>
        <td><strong>httpx: Async Transport Layer</strong></td>
        <td><a href="https://github.com/encode/httpx/issues/780" target="_blank" class="external-link">encode/httpx#780 ↗</a></td>
        <td>Unified async transport layer across Asyncio and Trio backends</td>
        <td><span class="badge badge-accepted">AnyIO Transport Abstraction</span></td>
        <td><span class="badge badge-source">Expected fixture outcome</span></td>
      </tr>
      <tr>
        <td><strong>Python: PEP 735 Groups</strong></td>
        <td><a href="https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823" target="_blank" class="external-link">discuss.python.org#42823 ↗</a></td>
        <td>Standardizing development & lint dependency groups</td>
        <td><span class="badge badge-accepted">[dependency-groups] in pyproject.toml</span></td>
        <td><span class="badge badge-source">Expected fixture outcome</span></td>
      </tr>
    `;

  } else if (metricType === "rejected") {
    heading.textContent = "Recovered Rejected Alternatives & Objections";
    if (subheading) subheading.textContent = "";
    filterBadge.textContent = "Curated rejected options";
    filterBadge.className = "badge badge-danger";

    thead.innerHTML = `
      <tr>
        <th>Benchmark Case</th>
        <th>Rejected Option</th>
        <th>Proposer</th>
        <th>Recovered Rejection Reasons</th>
        <th>Key Objection Citation</th>
        <th>Status</th>
      </tr>
    `;

    tbody.innerHTML = `
      <tr>
        <td><strong>uv Config Format</strong></td>
        <td><span class="badge badge-danger">YAML (.uv.yaml)</span></td>
        <td>@dev-contributor-alex</td>
        <td class="text-xs text-rose-300">
          • Arbitrary code execution CVEs in standard parsers<br>
          • Norway problem ('NO' interpreted as boolean False)<br>
          • Whitespace indentation formatting ambiguity
        </td>
        <td class="text-xs italic text-slate-300">
          "YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs."
          <span class="block text-[11px] not-italic text-slate-400 mt-1">— @security-auditor-eva</span>
        </td>
        <td><span class="badge badge-source">Fixture target</span></td>
      </tr>
      <tr>
        <td><strong>uv Config Format</strong></td>
        <td><span class="badge badge-danger">JSON Format</span></td>
        <td>@frontend-dev-sam</td>
        <td class="text-xs text-rose-300">
          • Absence of inline comments makes documenting configs painful<br>
          • Trailing comma syntax errors
        </td>
        <td class="text-xs italic text-slate-300">
          "JSON is disqualified because configuration files need comments."
          <span class="block text-[11px] not-italic text-slate-400 mt-1">— @maintainer-marcus</span>
        </td>
        <td><span class="badge badge-source">Fixture target</span></td>
      </tr>
      <tr>
        <td><strong>Discourse Edge Cache</strong></td>
        <td><span class="badge badge-danger">RocksDB Engine</span></td>
        <td>@dan_developer</td>
        <td class="text-xs text-rose-300">
          • 85MB binary bloat in distribution images<br>
          • Severe ARM64 cross-compilation & jemalloc build failures<br>
          • Operational maintenance of LSM compaction tuning
        </td>
        <td class="text-xs italic text-slate-300">
          "RocksDB requires compiling massive C++ binaries with jemalloc... adding 85MB of binary overhead."
          <span class="block text-[11px] not-italic text-slate-400 mt-1">— @sysadmin_claire</span>
        </td>
        <td><span class="badge badge-source">Fixture target</span></td>
      </tr>
      <tr>
        <td><strong>httpx Transport</strong></td>
        <td><span class="badge badge-danger">Curio Backend</span></td>
        <td>@curio_advocate</td>
        <td class="text-xs text-rose-300">
          • Curio development frozen with negligible community adoption<br>
          • Multiplied transport test matrix maintenance debt
        </td>
        <td class="text-xs italic text-slate-300">
          "Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio."
          <span class="block text-[11px] not-italic text-slate-400 mt-1">— @florimondmanca</span>
        </td>
        <td><span class="badge badge-source">Fixture target</span></td>
      </tr>
      <tr>
        <td><strong>Python PEP 735</strong></td>
        <td><span class="badge badge-danger">External YAML Files</span></td>
        <td>@ci_maintainer_dan</td>
        <td class="text-xs text-rose-300">
          • Unwanted parser dependency in bootstrap build backends<br>
          • Arbitrary code execution CVE risks in build environments<br>
          • Fractured project metadata across external non-standard files
        </td>
        <td class="text-xs italic text-slate-300">
          "Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces code execution CVE risks."
          <span class="block text-[11px] not-italic text-slate-400 mt-1">— @pradyunsg</span>
        </td>
        <td><span class="badge badge-source">Fixture target</span></td>
      </tr>
    `;

  } else if (metricType === "quotes") {
    heading.textContent = "Verbatim Evidence Quote Grounding";
    if (subheading) subheading.textContent = "";
    filterBadge.textContent = "Curated quote examples";
    filterBadge.className = "badge badge-source";

    thead.innerHTML = `
      <tr>
        <th>Citation ID</th>
        <th>Verbatim Grounded Quote</th>
        <th>Author</th>
        <th>Comment Anchor</th>
        <th>Confidence</th>
        <th>Verification</th>
      </tr>
    `;

    tbody.innerHTML = `
      <tr>
        <td><span class="font-mono text-xs">eq-c102</span></td>
        <td class="text-xs italic text-slate-200">"YAML is notoriously difficult to parse securely due to arbitrary type coercion and code execution CVEs in standard parsers."</td>
        <td>@security-auditor-eva</td>
        <td><a href="https://github.com/astral-sh/uv/issues/1042#issuecomment-102" target="_blank" class="external-link">c-102 ↗</a></td>
        <td><span class="badge badge-source">Curated example</span></td>
        <td><span class="badge badge-source">Fixture quote</span></td>
      </tr>
      <tr>
        <td><span class="font-mono text-xs">eq-c104</span></td>
        <td class="text-xs italic text-slate-200">"JSON is disqualified because configuration files need comments. Forcing developers to maintain machine-only JSON... is a terrible developer experience."</td>
        <td>@maintainer-marcus</td>
        <td><a href="https://github.com/astral-sh/uv/issues/1042#issuecomment-104" target="_blank" class="external-link">c-104 ↗</a></td>
        <td><span class="badge badge-source">Curated example</span></td>
        <td><span class="badge badge-source">Fixture quote</span></td>
      </tr>
      <tr>
        <td><span class="font-mono text-xs">eq-c107</span></td>
        <td class="text-xs italic text-slate-200">"Consensus reached: We accept TOML as the single official configuration format. Rejected YAML due to security vulnerabilities... Implemented in PR #1045."</td>
        <td>@maintainer-marcus</td>
        <td><a href="https://github.com/astral-sh/uv/issues/1042#issuecomment-107" target="_blank" class="external-link">c-107 ↗</a></td>
        <td><span class="badge badge-source">Curated example</span></td>
        <td><span class="badge badge-source">Fixture quote</span></td>
      </tr>
      <tr>
        <td><span class="font-mono text-xs">eq-post202</span></td>
        <td class="text-xs italic text-slate-200">"RocksDB requires compiling massive C++ binaries with jemalloc dependencies... adding 85MB of binary overhead."</td>
        <td>@sysadmin_claire</td>
        <td><a href="https://meta.discourse.org/t/embedded-cache-storage-engine/88219/3" target="_blank" class="external-link">post-202 ↗</a></td>
        <td><span class="badge badge-source">Curated example</span></td>
        <td><span class="badge badge-source">Fixture quote</span></td>
      </tr>
      <tr>
        <td><span class="font-mono text-xs">eq-post203</span></td>
        <td class="text-xs italic text-slate-200">"SQLite with WAL (Write-Ahead Logging) and memory-mapped I/O achieves 45,000 read queries/sec in our benchmarks with zero external shared libraries."</td>
        <td>@sam_saffron</td>
        <td><a href="https://meta.discourse.org/t/embedded-cache-storage-engine/88219/4" target="_blank" class="external-link">post-203 ↗</a></td>
        <td><span class="badge badge-source">Curated example</span></td>
        <td><span class="badge badge-source">Fixture quote</span></td>
      </tr>
      <tr>
        <td><span class="font-mono text-xs">eq-c302</span></td>
        <td class="text-xs italic text-slate-200">"Curio development has essentially frozen and community adoption is negligible compared to standard library asyncio."</td>
        <td>@florimondmanca</td>
        <td><a href="https://github.com/encode/httpx/issues/780#issuecomment-302" target="_blank" class="external-link">c-302 ↗</a></td>
        <td><span class="badge badge-source">Curated example</span></td>
        <td><span class="badge badge-source">Fixture quote</span></td>
      </tr>
      <tr>
        <td><span class="font-mono text-xs">eq-post402</span></td>
        <td class="text-xs italic text-slate-200">"Introducing YAML creates an unwanted parser dependency across all bootstrap build frontends and introduces code execution CVE risks."</td>
        <td>@pradyunsg</td>
        <td><a href="https://discuss.python.org/t/pep-735-dependency-groups-in-pyproject-toml/42823/3" target="_blank" class="external-link">post-402 ↗</a></td>
        <td><span class="badge badge-source">Curated example</span></td>
        <td><span class="badge badge-source">Fixture quote</span></td>
      </tr>
    `;

  } else if (metricType === "radar") {
    heading.textContent = "Curated Pull Request Radar Scenarios";
    if (subheading) subheading.textContent = "";
    filterBadge.textContent = "Fixture scenarios";
    filterBadge.className = "badge badge-source";

    thead.innerHTML = `
      <tr>
        <th>Simulated PR Scenario</th>
        <th>Modified Files / Diff</th>
        <th>Expected Behavior</th>
        <th>Radar Detected Alert</th>
        <th>Precision Score</th>
      </tr>
    `;

    tbody.innerHTML = `
      <tr>
        <td><strong>PR #2041: Add YAML config support for uv</strong></td>
        <td><code class="file-pill">uv.yaml</code> <code class="file-pill">config.py</code></td>
        <td><span class="badge badge-danger">High Alert Expected</span></td>
        <td><span class="badge badge-danger">🚨 Resurrected Alternative: YAML (ADR-1042)</span></td>
        <td><span class="badge badge-source font-bold">Fixture alert expected</span></td>
      </tr>
      <tr>
        <td><strong>PR #3120: Integrate RocksDB cache backend</strong></td>
        <td><code class="file-pill">lib/storage/edge_cache.rb</code></td>
        <td><span class="badge badge-danger">High Alert Expected</span></td>
        <td><span class="badge badge-danger">🚨 Resurrected Alternative: RocksDB (ADR-88219)</span></td>
        <td><span class="badge badge-source font-bold">Fixture alert expected</span></td>
      </tr>
      <tr>
        <td><strong>PR #4210: External dependencies.yaml for PEP 735</strong></td>
        <td><code class="file-pill">dependencies.yaml</code></td>
        <td><span class="badge badge-danger">High Alert Expected</span></td>
        <td><span class="badge badge-danger">🚨 Resurrected Alternative: YAML (ADR-42823)</span></td>
        <td><span class="badge badge-source font-bold">Fixture alert expected</span></td>
      </tr>
      <tr>
        <td><strong>PR #4015: Optimize TOML serializer buffer</strong></td>
        <td><code class="file-pill">Cargo.toml</code></td>
        <td><span class="badge badge-accepted">Clean PR (No Conflict)</span></td>
        <td><span class="badge badge-accepted">✔ Clean: 0 Conflicts / No Regressions</span></td>
        <td><span class="badge badge-source font-bold">Fixture no-alert expected</span></td>
      </tr>
    `;
  }
}

async function runEvaluationBenchmark(animate = true) {
  const btnRun = document.getElementById("btn-run-eval");
  if (btnRun) {
    btnRun.disabled = true;
    btnRun.innerHTML = `<span class="btn-icon">⏳</span> Running Benchmark Suite...`;
  }

  try {
    const res = await fetch("/api/benchmark/evaluate");
    if (!res.ok) throw new Error(`Benchmark endpoint returned ${res.status}`);
    const metrics = await res.json();
    lastEvaluationMetrics = metrics;

    // These are curated-fixture match rates, not held-out accuracy metrics.
    document.getElementById("metric-acc").textContent = `${(metrics.decision_accuracy * 100).toFixed(0)}%`;
    document.getElementById("metric-rejected").textContent = `${(metrics.rejected_recovery_rate * 100).toFixed(0)}%`;
    document.getElementById("metric-quotes").textContent = `${(metrics.quote_accuracy * 100).toFixed(0)}%`;
    document.getElementById("metric-radar").textContent = `${(metrics.radar_precision * 100).toFixed(0)}%`;

    renderEvaluationView(currentMetricFilter);
    if (animate) showToast("Curated fixture benchmark completed.", "success");
  } catch (e) {
    lastEvaluationMetrics = null;
    document.getElementById("metric-acc").textContent = "n/a";
    document.getElementById("metric-rejected").textContent = "n/a";
    document.getElementById("metric-quotes").textContent = "n/a";
    document.getElementById("metric-radar").textContent = "n/a";
    if (animate) showToast(`Benchmark unavailable: ${e.message}. No cached scores were shown.`, "warning");
  } finally {
    if (btnRun) {
      btnRun.disabled = false;
      btnRun.innerHTML = `<span class="btn-icon">▶</span> Run Benchmark Suite`;
    }
  }
}

// Helpers
function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function jsonBody(obj) {
  return JSON.stringify(obj);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
