import { createServer } from "node:http";
import type { IncomingMessage, ServerResponse } from "node:http";
import { readFile } from "node:fs/promises";
import type { RequestRepository } from "./repository.ts";
import { suggestRequest } from "./provider.ts";
import type { SuggestionProvider } from "./provider.ts";

function json(response: ServerResponse, status: number, body: unknown) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(body));
}

async function readJson(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > 16_384) throw new Error("Request body is too large.");
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

const assets: Record<string, [string, string]> = {
  "/": ["index.html", "text/html"],
  "/app.js": ["app.js", "text/javascript"],
  "/styles.css": ["styles.css", "text/css"],
};

export function createApp(repository: RequestRepository, provider: SuggestionProvider = suggestRequest) {
  async function handle(request: IncomingMessage, response: ServerResponse) {
    const path = new URL(request.url ?? "/", "http://localhost").pathname;
    if (request.method === "GET" && assets[path]) {
      const [file, contentType] = assets[path];
      const content = await readFile(new URL(`../public/${file}`, import.meta.url));
      response.writeHead(200, { "Content-Type": `${contentType}; charset=utf-8` });
      response.end(content);
      return;
    }
    if (request.method === "GET" && path === "/api/requests") {
      json(response, 200, { requests: await repository.list() });
      return;
    }
    const route = /^\/api\/requests\/([^/]+)(?:\/(suggestion|review))?$/.exec(path);
    if (!route) return json(response, 404, { error: "Not found." });
    const record = await repository.get(route[1]);
    if (!record) return json(response, 404, { error: "Request not found." });
    if (request.method === "GET" && !route[2]) {
      return json(response, 200, { request: record });
    }
    if (request.method === "POST" && route[2] === "suggestion") {
      try {
        const suggestion = await provider(record);
        // TODO: Validate provider output with parseSuggestion before returning it.
        json(response, 200, { suggestion });
      } catch {
        json(response, 502, { error: "Could not get a valid suggestion. You can review manually." });
      }
      return;
    }
    if (request.method === "PUT" && route[2] === "review") {
      let input: unknown;
      try {
        input = await readJson(request);
      } catch {
        return json(response, 400, { error: "The body must be valid JSON, at most 16 KB." });
      }
      // TODO: Validate input with reviewRequest (400 on invalid input), save the result,
      // and return 200 with { request: savedRequest }. Keep storage failures as 500.
      void input;
      json(response, 501, { error: "Saving reviews is not implemented yet. Complete the review route." });
      return;
    }
    json(response, 405, { error: "Method not allowed." });
  }

  return createServer((request, response) => {
    handle(request, response).catch((error: unknown) => {
      console.error(error);
      json(response, 500, { error: "Something went wrong on the server." });
    });
  });
}
