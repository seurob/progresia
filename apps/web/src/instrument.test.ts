import { describe, expect, it } from "vitest";
import { sanitizeSentryEvent } from "./instrument";

describe("sanitizeSentryEvent", () => {
  it("removes credentials, request data and user identity", () => {
    const event = sanitizeSentryEvent({
      type: undefined,
      user: { id: "user-1", email: "private@example.com" },
      request: {
        data: { password: "secret" },
        cookies: { session: "secret" },
        headers: {
          Authorization: "Bearer secret",
          Cookie: "session=secret",
          "Content-Type": "application/json"
        }
      }
    });

    expect(event.user).toBeUndefined();
    expect(event.request?.data).toBeUndefined();
    expect(event.request?.cookies).toBeUndefined();
    expect(event.request?.headers).toEqual({ "Content-Type": "application/json" });
  });
});
