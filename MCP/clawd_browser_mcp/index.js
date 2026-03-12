import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { chromium } from "playwright-core";
import fs from "fs/promises";
import path from "path";

// 模拟 Clawdbot 的角色快照逻辑
const INTERACTIVE_ROLES = new Set([
  "button", "link", "textbox", "checkbox", "radio", "combobox", "listbox",
  "menuitem", "menuitemcheckbox", "menuitemradio", "option", "searchbox",
  "slider", "spinbutton", "switch", "tab", "treeitem",
]);

class ClawdBrowserServer {
  constructor() {
    this.server = new Server(
      {
        name: "clawd-browser-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.browser = null;
    this.context = null;
    this.page = null;
    this.refs = new Map(); // 存储 ref -> selector/locator 映射

    this.setupTools();
  }

  async ensureBrowser() {
    if (!this.browser) {
      this.browser = await chromium.launch({ 
        headless: false,
        executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" 
      });
      this.context = await this.browser.newContext();
      this.page = await this.context.newPage();
    }
    return this.page;
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "browser_navigate",
          description: "导航到指定 URL",
          inputSchema: {
            type: "object",
            properties: {
              url: { type: "string" },
            },
            required: ["url"],
          },
        },
        {
          name: "browser_snapshot",
          description: "获取当前页面的视觉角色快照 (Clawdbot 风格)",
          inputSchema: {
            type: "object",
            properties: {
              format: { type: "string", enum: ["aria", "ai"], default: "aria" },
            },
          },
        },
        {
          name: "browser_click",
          description: "点击快照中的元素",
          inputSchema: {
            type: "object",
            properties: {
              ref: { type: "string", description: "快照中的 ref 标识，如 e1, ax1" },
            },
            required: ["ref"],
          },
        },
        {
          name: "browser_type",
          description: "在元素中输入文本",
          inputSchema: {
            type: "object",
            properties: {
              ref: { type: "string" },
              text: { type: "string" },
            },
            required: ["ref", "text"],
          },
        },
        {
          name: "browser_screenshot",
          description: "截取当前页面屏幕",
          inputSchema: {
            type: "object",
            properties: {
              name: { type: "string", default: "screenshot" },
            },
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      const page = await this.ensureBrowser();

      try {
        switch (name) {
          case "browser_navigate": {
            await page.goto(args.url, { waitUntil: "networkidle" });
            return { content: [{ type: "text", text: `已导航至 ${args.url}` }] };
          }

          case "browser_snapshot": {
            // 简化版的 Clawdbot 快照逻辑
            const ariaSnapshot = await page.locator("body").ariaSnapshot();
            const lines = ariaSnapshot.split("\n");
            let result = "";
            this.refs.clear();
            let counter = 0;

            for (const line of lines) {
              const match = line.match(/^(\s*-\s*)(\w+)(?:\s+"([^"]*)")?(.*)$/);
              if (match) {
                const [, prefix, role, name, suffix] = match;
                const isInteractive = INTERACTIVE_ROLES.has(role.toLowerCase());
                if (isInteractive) {
                  counter++;
                  const ref = `e${counter}`;
                  const enhanced = `${prefix}${role}${name ? ` "${name}"` : ""} [ref=${ref}]${suffix}`;
                  result += enhanced + "\n";
                  // 存储定位信息，这里简化为使用 role 和 name
                  this.refs.set(ref, { role: role.toLowerCase(), name });
                } else {
                  result += line + "\n";
                }
              } else {
                result += line + "\n";
              }
            }

            return { content: [{ type: "text", text: result || "(空快照)" }] };
          }

          case "browser_click": {
            const refData = this.refs.get(args.ref);
            if (!refData) throw new Error(`未找到 ref: ${args.ref}`);
            
            const locator = page.getByRole(refData.role, { name: refData.name }).first();
            await locator.click();
            return { content: [{ type: "text", text: `已点击 ${args.ref}` }] };
          }

          case "browser_type": {
            const refData = this.refs.get(args.ref);
            if (!refData) throw new Error(`未找到 ref: ${args.ref}`);
            
            const locator = page.getByRole(refData.role, { name: refData.name }).first();
            await locator.fill(args.text);
            return { content: [{ type: "text", text: `已在 ${args.ref} 输入文本` }] };
          }

          case "browser_screenshot": {
            const buffer = await page.screenshot();
            const base64 = buffer.toString("base64");
            return {
              content: [
                { type: "image", data: base64, mimeType: "image/png" },
                { type: "text", text: "截图已完成" }
              ],
            };
          }

          default:
            throw new Error(`未知工具: ${name}`);
        }
      } catch (error) {
        return {
          content: [{ type: "text", text: `错误: ${error.message}` }],
          isError: true,
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Clawd Browser MCP server running on stdio");
  }
}

const server = new ClawdBrowserServer();
server.run().catch(console.error);