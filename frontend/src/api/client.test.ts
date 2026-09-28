import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("ApiClient ChartSpec", () => {
  it("loads immutable chart specs from their additive API route", async () => {
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "csp_0123456789ab", title: "Trend", chart_spec: { mark: "line" }, version: 1, status: "ready", dataset_hash: "sha256:x", content_hash: "sha256:y", created_at: "2026-01-01T00:00:00Z" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetch);

    const chart = await new ApiClient("u_0123456789ab").getChartSpec("csp_0123456789ab");

    expect(fetch).toHaveBeenCalledWith(
      "/api/chart-specs/csp_0123456789ab",
      expect.objectContaining({ headers: expect.objectContaining({ "X-User-Id": "u_0123456789ab" }) }),
    );
    expect(chart.chart_spec).toEqual({ mark: "line" });
  });
});
