import { createApp } from "./app.ts";
import { createRepository } from "./repository.ts";

const repository = createRepository();
await repository.list();
createApp(repository).listen(3000, "127.0.0.1", () => {
  console.log("Request review starter: http://127.0.0.1:3000");
});
