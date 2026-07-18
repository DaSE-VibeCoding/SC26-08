import type { Filters, Meta, PaperListResponse } from "../types";

const API_BASE = "/api";

export async function fetchMeta(): Promise<Meta> {
  const res = await fetch(`${API_BASE}/meta`);
  if (!res.ok) {
    console.error("fetchMeta failed", res.status);
    throw new Error("fetchMeta failed");
  }
  return res.json();
}

export async function fetchPapers(
  filters: Filters,
  limit = 60,
  offset = 0
): Promise<PaperListResponse> {
  const params = new URLSearchParams();
  if (filters.conference) params.set("conference", filters.conference);
  if (filters.year) params.set("year", filters.year);
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.q) params.set("q", filters.q);
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const res = await fetch(`${API_BASE}/papers?${params.toString()}`);
  if (!res.ok) {
    console.error("fetchPapers failed", res.status);
    throw new Error("fetchPapers failed");
  }
  return res.json();
}
