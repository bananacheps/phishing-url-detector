---
name: Streamlit workflow ports
description: Replit workflow behavior for the root Streamlit application.
---

Use an explicit `0.0.0.0` bind and a `${PORT:-<waitForPort>}` fallback in the Streamlit workflow command. For the Preview router, map `internalPort` to external port `80`; changing the mapping can refresh routing without restarting the process.

**Why:** A bare `$PORT` expanded to an empty value in this environment, causing Streamlit to treat the next CLI flag as the port and fail before opening the preview port.

**How to apply:** Keep the workflow's `waitForPort` synchronized with the fallback port. After a workflow restart, verify the mapping remains present and check both the internal listener and the Replit domain; if the router is stale, toggle the external mapping and restore it.

An active non-artifact Streamlit workflow can still return `404 — This deployment has no previewable artifacts` from `REPLIT_DEV_DOMAIN`; that response is a Preview/artifact-registration issue, not evidence that the local listener or app code failed.

**Why:** The process can be healthy on `0.0.0.0:5000` while the artifact router has no registered root preview target.

**How to apply:** Check the local listener and workflow logs separately from the public Preview domain. Do not change model or application code to fix this platform-level 404; confirm whether the project has a registered previewable root artifact or use the workflow's own preview surface. When the router is stale, applying `5000 → 5000` and then `5000 → 80` while the process stays running refreshes the standard Preview route; restarting afterward can normalize away the manual mapping.