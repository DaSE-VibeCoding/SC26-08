export interface Paper {
  id: number;
  title: string;
  authors: string[];
  conference: string;
  year: number | null;
  pdf_url: string | null;
  abs_url: string | null;
  abstract: string;
  abstract_zh: string | null;
  tags: string[];
  source: string;
}

export interface PaperListResponse {
  total: number;
  limit: number;
  offset: number;
  items: Paper[];
}

export interface Meta {
  total: number;
  conferences: string[];
  years: number[];
  tags: string[];
  sources: string[];
}

export interface Filters {
  conference: string;
  year: string;
  tag: string;
  q: string;
}

export type Lang = "zh" | "en";
