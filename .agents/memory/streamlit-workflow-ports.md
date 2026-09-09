---
name: Streamlit workflow ports
description: Replit workflow behavior for the root Streamlit application.
---

Use an explicit `0.0.0.0` bind and a `${PORT:-<waitForPort>}` fallback in the Streamlit workflow command. Non-artifact workflows may not inject `PORT`, even when `waitForPort` is configured.

**Why:** A bare `$PORT` expanded to an empty value in this environment, causing Streamlit to treat the next CLI flag as the port and fail before opening the preview port.

**How to apply:** Keep the workflow's `waitForPort` synchronized with the fallback port and verify both the listener address and HTTP response after restarting.