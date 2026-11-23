export const PRIORITIES = ["low", "medium", "high"] as const;
export const MAX_REVIEW_TEXT_LENGTH = 240;
export type Priority = (typeof PRIORITIES)[number];

export type Review =
  | { status: "unreviewed" }
  | { status: "reviewed"; priority: Priority; note: string };

export type RequestRecord = {
  id: string;
  title: string;
  description: string;
  review: Review;
};

export type Suggestion = { priority: Priority; reason: string };

// TODO: Validate unknown provider output. Trim reason (1 to 240 characters), ignore extra fields.
export function parseSuggestion(_input: unknown): Suggestion {
  throw new Error("Not implemented: parseSuggestion");
}

// TODO: Validate { priority, note } and return a reviewed copy without mutating record.
// Trim note (1 to 240 characters) and ignore extra fields.
export function reviewRequest(_record: RequestRecord, _input: unknown): RequestRecord {
  throw new Error("Not implemented: reviewRequest");
}
