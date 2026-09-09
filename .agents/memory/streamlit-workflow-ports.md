---
name: Streamlit workflow ports
description: Replit workflow behavior for the root Streamlit application.
---

Use an explicit `0.0.0.0` bind and a `${PORT:-<waitForPort>}` fallback in the Streamlit workflow command. For the Preview router, map `internalPort` to external port `80`; changing the mapping can refresh routing without restarting the process.

**Why:** A bare `$PORT` expanded to an empty value in this environment, causing Streamlit to treat the next CLI flag as the port and fail before opening the preview port.

**How to apply:** Keep the workflow's `waitForPort` synchronized with the fallback port. After a workflow restart, verify the mapping remains present and check both the internal listener and the Replit domain; if the router is stale, toggle the external mapping and restore it.