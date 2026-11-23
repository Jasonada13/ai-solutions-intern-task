# Acceptance checklist

Use this to check your work and report what you observed. Leave unfinished items unchecked and describe them in `SUBMISSION.md`. Stay within the three-hour limit.

## Request and review data

Each request has `id`, `title`, `description`, and `review`.

```ts
type Priority = 'low' | 'medium' | 'high';

type Review =
  | { status: 'unreviewed' }
  | { status: 'reviewed'; priority: Priority; note: string };

type RequestRecord = {
  id: string;
  title: string;
  description: string;
  review: Review;
};

type Suggestion = { priority: Priority; reason: string };
```

- [ ] `parseSuggestion` validates unknown data at runtime. It accepts the three priority values and a string reason with 1 to 240 characters after trimming.
- [ ] `reviewRequest` validates the incoming review. It accepts the same priority values and a string note with 1 to 240 characters after trimming.
- [ ] `parseSuggestion` ignores extra fields and returns only `priority` and `reason`.
- [ ] `reviewRequest` preserves the request's `id`, `title`, and `description`, and returns a new record with its validated review without mutating the original record. It ignores extra fields in the submitted review input.
- [ ] Missing fields, wrong types, blank strings, overlong text, and invalid priorities fail validation. Values are not silently coerced.

## API contract

| Method and path | Successful response |
| --- | --- |
| `GET /api/requests` | `200`, `{ "requests": [...] }` |
| `GET /api/requests/:id` | `200`, `{ "request": ... }` |
| `POST /api/requests/:id/suggestion` | `200`, `{ "suggestion": { "priority": ..., "reason": ... } }` |
| `PUT /api/requests/:id/review` | `200`, `{ "request": ... }` |

The review request body is `{ "priority": ..., "note": ... }`.

- [ ] Malformed review JSON and invalid review fields return `400`.
- [ ] An unknown request ID returns `404` on the request, suggestion, and review routes.
- [ ] An invalid mock result or provider failure returns `502` with a useful error.
- [ ] A successful save returns the request with its validated, trimmed review.
- [ ] Suggestion responses contain validated suggestions. They never save a review.

## Browser behavior and fixtures

The supplied fixtures have these cases. Use them without calling a live model.

| ID | Mock outcome | What to check |
| --- | --- | --- |
| `REQ-001` | Valid high priority | Suggestion displays and can prefill an editable draft |
| `REQ-002` | Valid low priority | Low priority works as well as high |
| `REQ-003` | Invalid priority, `urgent` | Error displays, invalid suggestion cannot be used |
| `REQ-004` | Provider unavailable | Error displays, manual review still works |
| `REQ-005` | Valid medium priority, description contains synthetic prompt injection | Description stays data, no automatic review or special action |
| `REQ-006` | Invalid blank reason | Error displays, invalid suggestion cannot be used |

- [ ] Requests and their saved review status are visible.
- [ ] A person can request a suggestion, edit its priority and note, then choose to save.
- [ ] Requesting or accepting a suggestion only affects the draft until the person saves.
- [ ] A person can write and save a manual review without requesting a suggestion.
- [ ] A failed suggestion or failed save leaves the person's existing draft and saved review unchanged.
- [ ] A person can edit and overwrite a saved review.
- [ ] A saved review remains after reloading the page.
- [ ] A saved review remains after stopping and restarting the server. Do not run reset during this check.

## Verification and handoff

- [ ] Add one automated test that rejects an invalid suggestion.
- [ ] Add a second focused test for invalid review data or preservation of a saved review after failure.
- [ ] Run `npm test` and `npm run typecheck` and report their actual results.
- [ ] Record manual checks you performed, including persistence after restart. Separate observed results from checks you would do later.
- [ ] Complete `SUBMISSION.md`, including elapsed time and AI use or no AI use.
- [ ] Exclude `.git`, `node_modules`, `.data`, `.env`, secrets, and personal details from the ZIP.
