import type { Tool } from "@modelcontextprotocol/sdk/types.js";

/**
 * Cookie injection tool for headless VPS environments.
 *
 * When Google blocks headless auto-login with CAPTCHA, the user can:
 * 1. Log into Google via VNC Chrome
 * 2. Run the cookie extraction script (scripts/extract_chrome_cookies.py)
 * 3. Call this tool to inject the cookies into the MCP server's state.json
 *
 * This bypasses the need for interactive browser login.
 */
export const cookieInjectTool: Tool = {
  name: "inject_cookies",
  description:
    "Inject Google cookies from an external source (e.g., VNC Chrome) to bypass CAPTCHA-blocked auto-login.\n\n" +
    "Use this when:\n" +
    "  • Auto-login fails because Google shows CAPTCHA in headless mode\n" +
    "  • You logged into Google via VNC Chrome and extracted cookies\n" +
    "  • get_health reports authenticated=false and setup_auth is not practical\n\n" +
    "Workflow:\n" +
    "  1. Log into Google via VNC Chrome (http://YOUR_IP:6080/vnc.html)\n" +
    "  2. Run: python3 scripts/extract_chrome_cookies.py\n" +
    "  3. Call inject_cookies with the path to the extracted state.json\n" +
    "  4. Call get_health to verify authentication\n\n" +
    "The tool reads a Playwright-format state.json file and copies it to the\n" +
    "server's browser state directory, then validates the cookies.",
  inputSchema: {
    type: "object",
    properties: {
      state_path: {
        type: "string",
        description:
          "Path to a Playwright-format state.json file containing Google cookies.\n" +
          "Format: {\"cookies\": [{\"name\": \"SID\", \"value\": \"...\", \"domain\": \".google.com\", ...}]}\n" +
          "If not provided, attempts to auto-detect from common Chrome profile locations.",
      },
      force: {
        type: "boolean",
        description:
          "Overwrite existing state even if current cookies are valid. Default: false.",
        default: false,
      },
    },
  },
  annotations: {
    title: "Inject Google cookies",
    readOnlyHint: false,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
};
