# ADR-41749-01: Adopt Undici for Fetch API in Node.js Core

* Status: **ACCEPTED**
* Date: 2022-02-01
* Repository: [nodejs/node](https://github.com/nodejs/node)
* Source Discussion: [#41749](https://github.com/nodejs/node/pull/41749)

## Context and Problem Statement

Node.js developers have long requested native WHATWG `fetch` support within Node.js runtime core to reduce reliance on third-party HTTP clients like `node-fetch` or `axios` and achieve browser web standard parity.

**Problem Statement:** Provide high-performance native `fetch` implementation without regressing core startup time or event loop throughput, while balancing browser standard spec compliance with server-side reality.

## Decision Drivers

* [VERIFIED] Web Platform standard parity: native `fetch` is essential for Node.js relevance to developers (cited by @mcollina in [#1025771533](https://github.com/nodejs/node/pull/41749#issuecomment-1025771533)).
* [VERIFIED] Maintainability within Node.js core: Undici is developed directly by Node.js core maintainers (cited by @benjamingr in [#1025092422](https://github.com/nodejs/node/pull/41749#issuecomment-1025092422)).
* [VERIFIED] High HTTP throughput and HTTP/1.1 pipelining performance from the ground up.

## Considered Options

* **[Adopted]** Integrate Undici as the underlying HTTP engine for native `fetch`
* **[Rejected]** node-fetch pure JavaScript userland port (#27979)
* **[Rejected]** Reuse Chromium / Chrome fetch implementation from V8

## Decision Outcome

Chosen approach: **Integrate Undici as the underlying HTTP engine for native fetch**

### Positive Consequences

* [VERIFIED] High-throughput native Fetch API available out-of-the-box in Node.js core.
* [VERIFIED] Eliminates the mandatory installation of userland HTTP packages for basic HTTP fetching.
* [VERIFIED] Maintained directly by Node.js team contributors familiar with core runtime internals.

### Negative Consequences & Liabilities

* [VERIFIED] Increased surface area and bundle footprint for Node.js runtime (`deps/undici/undici.js`).
* [VERIFIED] Full browser WHATWG spec parity is not achievable server-side (CORS, caching, cookies, GC behavior differ, per @mcollina in [#1025181470](https://github.com/nodejs/node/pull/41749#issuecomment-1025181470)).
* [VERIFIED] Missing features initially such as `FormData` and `File` support (noted by @ronag in [#1025168564](https://github.com/nodejs/node/pull/41749#issuecomment-1025168564)).

### Architectural Trade-offs

* [VERIFIED] Adopted experimental flag `--experimental-fetch` initially to allow iterative stabilization before graduating to unflagged status.
* [VERIFIED] Bundle debugging vs size: Undici bundle left unminified in tree for debuggability (@targos in [#1025130980](https://github.com/nodejs/node/pull/41749#issuecomment-1025130980)).
* [VERIFIED] Lazy loading of Undici globals to prevent startup time regression (@mcollina in [#1025126819](https://github.com/nodejs/node/pull/41749#issuecomment-1025126819)).

## Pros and Cons of Rejected Alternatives

### node-fetch pure JavaScript userland port (#27979)
* Status: **REJECTED** ([VERIFIED])
* Rejection Reason: `node-fetch` is intentionally not spec-compliant on key aspects (e.g. `body` is a Node.js Readable stream rather than a WHATWG ReadableStream) and exposes Node-specific options like `agent` that do not align with web standards.
* Supporting Evidence Citations:
  - Comment [#1025096581](https://github.com/nodejs/node/pull/41749#issuecomment-1025096581) by @targos:
    > "`node-fetch` is also intentionally not spec-compliant on certain key aspects. For example, the `body` is a Node.js Readable stream. It also has node-specific options (like `agent`) that we may not want to expose in the same way."
  - Comment [#1025092422](https://github.com/nodejs/node/pull/41749#issuecomment-1025092422) by @benjamingr:
    > "Undici is a Node.js project written by Node.js core folks so I assume familiarity with the code is part of it - performance likely as well."

### Reuse Chrome / V8 internal fetch implementation
* Status: **REJECTED** ([VERIFIED])
* Rejection Reason: Chrome's fetch implementation is tightly coupled to Blink and Chromium browser networking infrastructure and is not exposed through V8 in a reusable way.
* Supporting Evidence Citations:
  - Comment [#1025092422](https://github.com/nodejs/node/pull/41749#issuecomment-1025092422) by @benjamingr:
    > "Not at all (I tried!) it's very tightly integrated into oh-so-many-things."

## Supporting Evidence

* **Comment [#1025096581](https://github.com/nodejs/node/pull/41749#issuecomment-1025096581)** by @targos on 2022-01-30 08:40:46 UTC `[VERIFIED]`:
  > "`node-fetch` is also intentionally not spec-compliant on certain key aspects. For example, the `body` is a Node.js Readable stream. It also has node-specific options (like `agent`) that we may not want to expose in the same way."
* **Comment [#1025181470](https://github.com/nodejs/node/pull/41749#issuecomment-1025181470)** by @mcollina on 2022-01-30 16:40:13 UTC `[VERIFIED]`:
  > "fetch cannot be implemented server-side by following the spec (CORS, caching, cookies, GC behavior and many other things). It's just not what our users would expect. Yet most of our users would greatly benefit from a 50-80% fetch. That's the goal."
* **Comment [#1025771533](https://github.com/nodejs/node/pull/41749#issuecomment-1025771533)** by @mcollina on 2022-01-31 14:04:47 UTC `[VERIFIED]`:
  > "@jimmywarting the fundamental reason we are doing this is because of the 300+ comments in https://github.com/nodejs/node/issues/19393, plus all the questions we get about this whenever we talk to JS developers. I think this is inevitable for Node.js to keep being relevant."

## Contradictory Evidence & Objections

* Multiple maintainers raised objections regarding spec compliance divergences:
  - @GeoffreyBooth argued that non-compliant fetch should be given a different name to avoid web interop issues.
  - @jasnell noted in [#1026110002](https://github.com/nodejs/node/pull/41749#issuecomment-1026110002) that renaming would kill the main developer adoption reason and recommended deferring full compliance until graduating from experimental.

## Original GitHub Discussion

* Direct URL: https://github.com/nodejs/node/pull/41749
