import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, test } from "node:test";
import { createApp } from "../src/app.ts";
import { createRepository } from "../src/repository.ts";
import { initialRequests } from "../src/fixtures.ts";
import { suggestRequest } from "../src/provider.ts";

let directory: string;
let baseUrl: string;
let server: ReturnType<typeof createApp>;

before(async () => {
  directory = await mkdtemp(join(tmpdir(), "request-review-test-"));
  server = createApp(createRepository(join(directory, "api.json")));
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  baseUrl = `http://127.0.0.1:${address.port}`;
});

after(async () => {
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  await rm(directory, { recursive: true, force: true });
});

test("the supplied API lists all six initially unreviewed requests", async () => {
  const response = await fetch(`${baseUrl}/api/requests`);
  assert.equal(response.status, 200);
  const { requests } = await response.json();
  assert.deepEqual(requests, initialRequests());
});

test("unknown request IDs return 404", async () => {
  for (const [method, suffix] of [["GET", ""], ["POST", "/suggestion"], ["PUT", "/review"]]) {
    const response = await fetch(`${baseUrl}/api/requests/REQ-999${suffix}`, { method });
    assert.equal(response.status, 404);
    assert.equal((await response.json()).error, "Request not found.");
  }
});

test("the supplied route reports provider failure as 502", async () => {
  const response = await fetch(`${baseUrl}/api/requests/REQ-004/suggestion`, { method: "POST" });
  assert.equal(response.status, 502);
  assert.equal(typeof (await response.json()).error, "string");
});

test("the supplied JSON parser rejects malformed request bodies", async () => {
  const response = await fetch(`${baseUrl}/api/requests/REQ-001/review`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: "{broken",
  });
  assert.equal(response.status, 400);
});

test("repository saves survive a new repository instance and reset restores fixtures", async () => {
  const file = join(directory, "persistence.json");
  const repository = createRepository(file);
  const [record, second] = await repository.list();
  const reviewed = { ...record, review: { status: "reviewed" as const, priority: "low" as const, note: "A manual test review." } };
  const another = { ...second, review: { ...reviewed.review, note: "Another manual test review." } };
  await Promise.all([repository.save(reviewed), repository.save(another)]);
  const reopened = createRepository(file);
  assert.deepEqual(await reopened.get(record.id), reviewed);
  assert.deepEqual(await reopened.get(second.id), another);
  await reopened.reset();
  assert.deepEqual(await reopened.list(), initialRequests());
});

test("the fake provider exposes the documented deterministic edge cases", async () => {
  const fixtures = initialRequests();
  assert.equal((await suggestRequest(fixtures[0]) as { priority: string }).priority, "high");
  assert.equal((await suggestRequest(fixtures[1]) as { priority: string }).priority, "low");
  assert.equal((await suggestRequest(fixtures[2]) as { priority: string }).priority, "urgent");
  await assert.rejects(() => suggestRequest(fixtures[3]), /Simulated provider outage/);
  assert.equal((await suggestRequest(fixtures[4]) as { priority: string }).priority, "medium");
  assert.equal((await suggestRequest(fixtures[5]) as { reason: string }).reason.trim(), "");
});
