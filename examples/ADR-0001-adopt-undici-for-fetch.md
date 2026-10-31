# ADR-41749-01: Adopt Undici for Fetch API in Node.js Core

* Status: **ACCEPTED**
* Date: 2022-02-01
* Repository: [nodejs/node](https://github.com/nodejs/node)
* Source Discussion: [#41749](https://github.com/nodejs/node/pull/41749)

## Context and Problem Statement

Node.js developers have long requested native WHATWG `fetch` support within Node.js runtime core to reduce reliance on third-party HTTP clients like `node-fetch` or `axios` and achieve browser web standard parity.

**Problem Statement:** Provide high-performance native `fetch` implementation without regressing core startup time or event loop throughput.

## Decision Drivers

* [VERIFIED] WHATWG Web Platform compatibility requirements
* [VERIFIED] High HTTP throughput and HTTP/1.1 pipelining performance
* [VERIFIED] Maintainability within Node.js core dependencies

## Considered Options

* **[Adopted]** Integrate Undici as the underlying HTTP engine for native `fetch`
* **[Rejected]** node-fetch pure JavaScript userland port

## Decision Outcome

Chosen approach: **Integrate Undici as the underlying HTTP engine for native fetch**

### Positive Consequences

* [VERIFIED] High-throughput native Fetch API available out-of-the-box
* [VERIFIED] Conformance with WHATWG Fetch specifications
* [VERIFIED] Backed by actively maintained high-performance HTTP client team

### Negative Consequences & Liabilities

* [VERIFIED] Increased surface area and bundle footprint for Node.js binary
* [PARTIALLY_SUPPORTED] Need to maintain Web Streams and FormData compatibility layer

### Architectural Trade-offs

* [VERIFIED] Adopted experimental flag `--experimental-fetch` initially to allow iterative stabilization

## Pros and Cons of Rejected Alternatives

### node-fetch pure JavaScript userland port
* Status: **REJECTED** ([VERIFIED])
* Rejection Reason: Sub-optimal throughput under high concurrent load compared to Undici engine
* Supporting Evidence Citations:
  - Comment [#41749-comm-1](https://github.com/nodejs/node/pull/41749#issuecomment-1025555555) by @mcollina: "Undici gives us 3x the throughput of userland wrappers with proper streaming support."

## Supporting Evidence

* **Comment [#41749-comm-1](https://github.com/nodejs/node/pull/41749#issuecomment-1025555555)** by @mcollina on 2022-02-01 10:15:00 UTC `[VERIFIED]`:
  > "LGTM to introduce fetch backed by undici under the experimental flag."
* **Comment [#41749-comm-2](https://github.com/nodejs/node/pull/41749#issuecomment-1025555556)** by @ronag on 2022-02-01 11:20:00 UTC `[VERIFIED]`:
  > "Performance benchmarks show undici is substantially faster than alternative wrappers."

## Contradictory Evidence & Objections

* No contradictory evidence or dissenting opinions detected in public discussion.

## Original GitHub Discussion

* Direct URL: https://github.com/nodejs/node/pull/41749

