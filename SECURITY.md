# Security

The current 1.0.x line is the initial maintained release line. There is no
response-time or long-term support guarantee.

For a suspected vulnerability, use the repository's GitHub private vulnerability
reporting feature. Avoid public exploit details, private models, or credentials.
Include the version, input type, reproduction steps, and expected impact.

Conversion workers provide crash isolation but are not a security sandbox.
Models are parsed by native libraries; use files from sources you trust. Input
and time limits are not a hard RAM or disk quota. The app does not request
elevation, intentionally download model dependencies, or automatically update.
Download releases from this repository and verify their checksums. Releases are
unsigned; a checksum establishes file consistency, not a code-signing identity.
