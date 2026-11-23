# Request review

A take-home task for the AI solutions intern role. Finish an app for reviewing incoming requests. The app can suggest a priority, but a person chooses what to save.

Everyone receives the same starter and requirements. We assess your choices, verification, and explanation. Be ready to discuss your decisions at a later interview.

## Time and scope

Aim for two hours. Stop after three hours, including your submission notes and AI record. Submit incomplete work with a clear account of what works and what remains. Extra features and visual polish earn no bonus.

Use the supplied mock AI provider. You do not need a live model, an AI account, credits, or a paid plan. Your own AI tools are optional. We assess your evidence and judgment, not your spending or access to tools.

This is a local, single-user demo. Production security architecture, authentication, multiple users, deployment, a framework rewrite, and video are outside the task. If setup or access causes problems, contact the recruiter through your existing channel.

## Run the starter

Use Node.js 24, version 24.12 or later.

```sh
git clone https://github.com/Jasonada13/ai-solutions-intern-task.git
cd ai-solutions-intern-task
npm ci
npm start
```

Open <http://127.0.0.1:3000>. In another terminal:

```sh
npm test
npm run typecheck
```

To restore the fixture data, stop the server and run `npm run reset`.

The backend uses TypeScript, Node's native type stripping, and `node:http`. The browser uses plain JavaScript. Local JSON storage and a deterministic mock provider are supplied.

| File | Purpose |
| --- | --- |
| `src/domain.ts` | Models and the two domain functions to complete |
| `src/app.ts` | HTTP routes to connect to your domain functions |
| `src/server.ts` | Server startup |
| `src/repository.ts` | Supplied persistence helpers |
| `src/provider.ts`, `src/fixtures.ts` | Mock suggestions and fixture requests |
| `public/app.js` | Browser interactions to complete |

The starter returns raw mock suggestions, cannot save a review, and has unfinished domain functions. Baseline tests pass without satisfying the task requirements.

## What to build

1. Complete `parseSuggestion(input: unknown)` in `src/domain.ts`. Accept only `low`, `medium`, or `high` priority and a reason containing 1 to 240 characters after trimming. Ignore extra fields. Reject invalid data and have the suggestion route return a clear error.
2. Show valid suggestions in the browser. Let a person use a suggestion to prefill an editable review draft. Only an explicit save may persist the human review. A person must also be able to write and save a review without using AI, including after an AI failure.
3. Complete `reviewRequest(record, input)` and the save route. A review needs a valid priority and a note containing 1 to 240 characters after trimming. Ignore extra fields. Persist it with the supplied storage helpers so it survives a page reload and server restart. Saving another review may overwrite the previous review. No history is needed.
4. Handle errors without losing the person's draft or changing their saved review. Treat request descriptions as data, including text that looks like instructions.
5. Add two focused automated tests. One must reject an invalid suggestion. The other must cover invalid review data or preservation of a saved review after failure. Check the remaining behavior manually using [the acceptance checklist](docs/ACCEPTANCE.md).

The checklist defines the API contract and fixtures. Keep the API paths and response shapes so we can check each submission consistently.

## Explain and submit

Complete [docs/SUBMISSION.md](docs/SUBMISSION.md). Keep the combined architecture and nontechnical explanation within 400 words. Include your tests and actual results, unfinished work, elapsed time, and a short AI record if you used tools. Do not send full chats or account exports.

Send a ZIP through the original recruiter channel, using the supplied candidate identifier if there is one. Include the code, tests, lockfile, and completed submission template. Exclude `.git`, `node_modules`, `.data`, `.env`, secrets, and personal details. Do not publish your response through a public repository, fork, pull request, or issue.

## How we review

We use automated checks and AI assistance to review submitted technical work. People make shortlist decisions.

| Area | Weight |
| --- | --- |
| Architecture choices and their justification | 25% |
| Correctness and reliability | 25% |
| Verification and evidence | 20% |
| AI judgment, including validation and fallback choices | 20% |
| Technical and nontechnical communication | 10% |

AI judgment applies with or without an AI assistant. Explain how you handled and checked the mock output. We do not infer AI use from writing style.
