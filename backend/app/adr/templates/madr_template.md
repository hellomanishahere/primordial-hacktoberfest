# {{ number }} - {{ title }}

* **Status:** {{ status }}
* **Date:** {{ date }}
* **Deciders:** {{ deciders }}
* **Source Discussion:** [{{ repository }}#{{ entity_number }}]({{ source_url }})

## Context and Problem Statement

{{ context_and_problem }}

## Decision Drivers

{% for driver in decision_drivers %}
* {{ driver }}
{% endfor %}

## Considered Options

{% for option in considered_options %}
* **{{ option.name }}{% if option.status == "chosen" %} (Chosen){% endif %}**
{% endfor %}

## Decision Outcome

Chosen option: **{{ chosen_option.name }}**, because {{ chosen_option.description }}

### Positive Consequences

{% for positive in consequences.positive %}
* {{ positive }}
{% endfor %}

### Negative Consequences

{% for negative in consequences.negative %}
* {{ negative }}
{% endfor %}

## Pros and Cons of the Options

{% for option in considered_options %}
### {{ option.name }}{% if option.status == "chosen" %} (Chosen){% endif %}

{% if option.rejection_reason %}
* Bad, because {{ option.rejection_reason }}
{% endif %}
{% for eid in option.evidence_ids %}
* *Evidence Citation:* Comment #{{ eid }}
{% endfor %}
{% endfor %}

## Evidence & Verification Log (Level 1 Technical Verification)

| Target Claim / Option | Author | Comment ID | GitHub Source Permalink | Technical Verification |
|---|---|---|---|---|
{% for evidence in evidence_catalog %}
| {{ evidence.claim_supported }} | @{{ evidence.author }} | `{{ evidence.comment_id }}` | [{{ evidence.comment_id }}]({{ evidence.html_url }}) | {% if evidence.is_technically_verified %}VERIFIED (Comment exists){% else %}UNVERIFIED{% endif %} |
{% endfor %}

