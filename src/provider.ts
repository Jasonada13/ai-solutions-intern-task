import type { RequestRecord } from "./domain.ts";

export type SuggestionProvider = (request: RequestRecord) => Promise<unknown>;

// Deterministic local fixtures; request text is data, never an instruction to execute.
export const suggestRequest: SuggestionProvider = async (request) => {
  switch (request.id) {
    case "REQ-001":
      return { priority: "high", reason: "The unavailable portal blocks customers from getting support." };
    case "REQ-002":
      return { priority: "low", reason: "This is a cosmetic change with a flexible deadline." };
    case "REQ-003":
      return { priority: "urgent", reason: "The report is delayed, but a workaround is available." };
    case "REQ-004":
      throw new Error("Simulated provider outage");
    case "REQ-005":
      return { priority: "medium", reason: "The filter would improve the team's daily dashboard workflow." };
    case "REQ-006":
      return { priority: "low", reason: "   " };
    default:
      throw new Error("No provider fixture for this request");
  }
};
