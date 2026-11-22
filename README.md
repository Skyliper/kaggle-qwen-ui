# Qwen web chat

GitHub Pages entry with PAT authentication against the private `Skyliper/kaggle-qwen` repository. The PAT goes only to GitHub; runtime API configuration is read from private `web-client.json`, never included in public builds. Credentials live in sessionStorage for the current tab. Chat history is stored by NextChat in the browser.

Ready client: [NextChat](https://github.com/ChatGPTNextWeb/NextChat), MIT, pinned source commit `1d3dc331512929a4b1d3e82354e72acce33b5c7a`. The workflow builds its static export under `/chat/`, disables server-only MCP, and configures the existing Qwen endpoint. It preserves the NextChat license in the published artifact. Model API keys are stripped from persistent access storage.

`server.html` preserves Kaggle controls including explicit account migration. The public repository contains no PAT or model API key. Anonymous visitors can download the frontend code but cannot access the model without its private API configuration.


## Search and page reader
The **Поиск + Tor** toggle supplies native model tools `web_search` and `read_web_page` through the authenticated gateway. Keyless DDGS metasearch handles normal search; Ahmia provides an incomplete onion index. Tor runs in the Kaggle session for v3 onion page reads, never on the user's PC. No paid search API or monthly quota is configured, but upstream rate limits and availability still apply. Pages are text-only, capped at 2 MiB downloads and 20,000 extracted characters per read; JavaScript and logins are not supported. External page content is untrusted. The updated Kaggle notebook must be started for these endpoints to work.
