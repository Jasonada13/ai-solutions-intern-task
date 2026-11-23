import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import type { RequestRecord } from "./domain.ts";
import { initialRequests } from "./fixtures.ts";

export const defaultDataFile = fileURLToPath(new URL("../.data/requests.json", import.meta.url));

export function createRepository(filePath = defaultDataFile) {
  async function write(records: RequestRecord[]) {
    await mkdir(dirname(filePath), { recursive: true });
    await writeFile(`${filePath}.tmp`, `${JSON.stringify(records, null, 2)}\n`, "utf8");
    await rename(`${filePath}.tmp`, filePath);
  }

  async function read(): Promise<RequestRecord[]> {
    return JSON.parse(await readFile(filePath, "utf8"));
  }

  const ready = read().catch(async (error: NodeJS.ErrnoException) => {
    if (error.code !== "ENOENT") throw error;
    const records = initialRequests();
    await write(records);
    return records;
  });
  let pending: Promise<unknown> = ready;

  function enqueue<T>(operation: () => Promise<T>): Promise<T> {
    const result = pending.then(() => ready).then(operation);
    pending = result.catch(() => undefined);
    return result;
  }

  return {
    async list(): Promise<RequestRecord[]> {
      await pending;
      await ready;
      return read();
    },
    async get(id: string): Promise<RequestRecord | undefined> {
      return (await this.list()).find((request) => request.id === id);
    },
    save(request: RequestRecord): Promise<RequestRecord> {
      return enqueue(async () => {
        const records = await read();
        const index = records.findIndex((record) => record.id === request.id);
        if (index < 0) throw new Error("Cannot save an unknown request");
        records[index] = request;
        await write(records);
        return request;
      });
    },
    reset(): Promise<void> {
      return enqueue(() => write(initialRequests()));
    },
  };
}

export type RequestRepository = ReturnType<typeof createRepository>;
