# Qwen web chat

GitHub Pages entry with PAT authentication against the private `Skyliper/kaggle-qwen` repository. The PAT goes only to GitHub; runtime API configuration is read from private `web-client.json`, never included in public builds. Credentials live in sessionStorage for the current tab. Chat history is stored by NextChat in the browser.

Ready client: [NextChat](https://github.com/ChatGPTNextWeb/NextChat), MIT, pinned source commit `1d3dc331512929a4b1d3e82354e72acce33b5c7a`. The workflow builds its static export under `/chat/`, disables server-only MCP, and configures the existing Qwen endpoint. It preserves the NextChat license in the published artifact. Model API keys are stripped from persistent access storage.

`server.html` preserves Kaggle controls including explicit account migration. The public repository contains no PAT or model API key. Anonymous visitors can download the frontend code but cannot access the model without its private API configuration.
