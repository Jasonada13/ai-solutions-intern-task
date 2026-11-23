import { createRepository } from "../src/repository.ts";

await createRepository().reset();
console.log("Reset all six requests to unreviewed. Reload the browser to see the changes.");
