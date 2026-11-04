// Respected Brain OpenCode plugin: v2 session hooks with a v1 factory fallback.
import { spawnSync } from "node:child_process";
import { appendFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const COMMAND = __COMMAND__;
const TRANSCRIPT_DIR = __TRANSCRIPT_DIRECTORY__;
const seen = new Set();
const started = new Set();
let v2 = false;

function remember(key) {
  if (seen.has(key)) return false;
  seen.add(key);
  if (seen.size > 512) seen.delete(seen.values().next().value);
  return true;
}

function sessionId(value) {
  const id = value && (value.sessionID || value.session_id || value.session?.id);
  return typeof id === "string" && id ? id : "";
}

function transcriptPath(id) {
  const name = (id || "opencode-unknown").replace(/[^A-Za-z0-9._-]/g, "_").slice(0, 120);
  return join(TRANSCRIPT_DIR, name + ".jsonl");
}

function append(id, role, text) {
  if (typeof text !== "string" || !text.trim()) return;
  const path = transcriptPath(id);
  const line = JSON.stringify({ message: { role, content: text } });
  if (!remember("line:" + path + ":" + line)) return;
  try {
    mkdirSync(TRANSCRIPT_DIR, { recursive: true });
    appendFileSync(path, line + "\n");
  } catch {}
}

function payload(id, extra) {
  const session = id || "opencode-unknown";
  return { session_id: session, cwd: process.cwd(), transcript_path: transcriptPath(session), ...extra };
}

function bridge(event, body) {
  const result = spawnSync(COMMAND[0], [...COMMAND.slice(1), "--event", event], {
    input: JSON.stringify(body || {}),
    encoding: "utf8",
    timeout: 60000,
    windowsHide: true,
  });
  try {
    return JSON.parse(result.stdout || "{}").additionalContext || "";
  } catch {
    return "";
  }
}

function start(id) {
  if (!id || started.has(id)) return "";
  started.add(id);
  return bridge("start", payload(id));
}

function prompt(id, text, messageID) {
  if (!id || !remember("prompt:" + id + ":" + (messageID || "") + ":" + (text || ""))) return;
  append(id, "user", text);
  bridge("prompt", payload(id, { prompt: text }));
}

function handle(type, data) {
  const id = sessionId(data);
  if (type === "session.next.prompt.admitted" || type === "chat.message") {
    const message = data.message || {};
    prompt(id || sessionId(message), data.prompt?.text ?? data.content ?? message.content, data.messageID || message.id);
    return;
  }
  if (type === "session.next.text.ended" || type === "session.text.ended") {
    append(id, "assistant", data.text);
    return;
  }
  if (type === "message.part.updated" && data.part?.type === "text") {
    append(id, "assistant", data.part.text);
    return;
  }
  if (/^session\.(next\.)?execution\.(succeeded|failed|interrupted)$/.test(type)) {
    bridge("turn", payload(id));
  }
}

async function server() {
  return {
    event: async ({ event }) => {
      if (!v2 && event?.type) handle(event.type, event.properties || {});
    },
    "chat.message": async (input) => {
      if (!v2) handle("chat.message", input || {});
    },
    "experimental.chat.system.transform": async (input) => {
      if (v2) return;
      const context = start(sessionId(input));
      if (context && Array.isArray(input?.system)) input.system.push(context);
    },
  };
}

async function setup(ctx) {
  if (!ctx || typeof ctx.session?.hook !== "function" || typeof ctx.event?.subscribe !== "function") {
    return async () => {};
  }
  v2 = true;
  const controller = new AbortController();
  const registrations = [];
  registrations.push(await ctx.session.hook("context", (input) => {
    const context = start(sessionId(input));
    if (context && Array.isArray(input?.system)) input.system.push(context);
  }));
  registrations.push(await ctx.session.hook("prompt", (properties) => {
    prompt(sessionId(properties), properties?.prompt?.text, properties?.messageID);
  }));
  const consuming = (async () => {
    for await (const input of ctx.event.subscribe({ signal: controller.signal })) {
      if (input?.type) handle(input.type, input.data || {});
    }
  })().catch(() => {});
  return async () => {
    controller.abort();
    for (const registration of registrations) {
      try { await registration?.dispose?.(); } catch {}
    }
    await consuming;
  };
}

export default { id: "respected-brain", server, setup };
