# Web to MCP (Cursor setup)

[Web to MCP](https://web-to-mcp.com) bridges live website UI into Cursor (or Claude Code) via [Model Context Protocol](https://modelcontextprotocol.io/). A Chrome extension captures a selected DOM component; the MCP server exposes tools so the AI can fetch that capture’s HTML and screenshot and recreate it accurately.

This is separate from MeloTunez / Base44 work.

## What you get

After signing in (Google) and installing the extension:

1. Browse any site → select a component with the extension.
2. You get a capture reference (slug / id).
3. In Cursor chat, the MCP tools pull HTML + screenshot for that reference.

Typical tools (names may evolve):

- `get_html_for_reference` — HTML for a capture slug (prefer styles → new classes; avoid relying on original class names / data attrs).
- `get_screenshot_for_reference` — PNG screenshot (base64) for the same slug.

## Enable in Cursor (local / IDE)

Your **personal MCP URL** looks like:

`https://web-to-mcp.com/mcp/<YOUR_UNIQUE_ID>/`

Treat that UUID path like a credential: do not commit it to a public repo. Keep it in local Cursor MCP settings (or a private env / secrets store).

### Via Cursor UI

1. **Settings → Cursor Settings → Tools & MCP** (or Features → Model Context Protocol).
2. Add a server named `web-to-mcp` with your URL from the Web to MCP dashboard.
3. Connect / restart if prompted so tools appear in chat.

### Via config file (pattern only)

Project (`.cursor/mcp.json`) or global Cursor MCP config:

```json
{
  "mcpServers": {
    "web-to-mcp": {
      "url": "https://web-to-mcp.com/mcp/<YOUR_UNIQUE_ID>/"
    }
  }
}
```

Replace `<YOUR_UNIQUE_ID>` with the URL from your Web to MCP dashboard (already issued for your account). Prefer UI / local config over committing the real URL.

## Cloud agent note

This Cloud Agent environment does **not** currently expose a `web-to-mcp` / `webtomcp` dynamic tool namespace. Use the integration in the Cursor desktop IDE where MCP settings are configured. Follow-up prompts that rely on capture slugs should be run in a session that has the server connected.

## Dashboard / product (high level)

- Google sign-in → unique MCP URL
- Chrome extension for component selection
- Captures sent over a secure MCP channel to Cursor / Claude Code
- Free tier + paid plans for higher capture limits (see site pricing)
