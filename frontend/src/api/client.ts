import type { Filters, Meta, Paper, PaperListResponse, PaperStatePatch } from "../types";

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
  if (filters.library === "read") params.set("is_read", "true");
  if (filters.library === "favorites") params.set("is_favorite", "true");
  if (filters.library === "notes") params.set("has_note", "true");
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const res = await fetch(`${API_BASE}/papers?${params.toString()}`);
  if (!res.ok) {
    console.error("fetchPapers failed", res.status);
    throw new Error("fetchPapers failed");
  }
  return res.json();
}

export async function translatePaperAbstract(paperId: number): Promise<Paper> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/translate_zh`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("translatePaperAbstract failed");
  return res.json();
}

export async function updatePaperState(
  paperId: number,
  patch: PaperStatePatch
): Promise<Paper> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/state`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error("updatePaperState failed");
  return res.json();
}

export async function updatePaperNote(paperId: number, note: string): Promise<Paper> {
  const res = await fetch(`${API_BASE}/papers/${paperId}/note`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  if (!res.ok) throw new Error("updatePaperNote failed");
  return res.json();
}
