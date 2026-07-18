import { createContext, useContext } from "react";
import type { Lang } from "../types";

type Dict = Record<string, string>;

export const translations: Record<Lang, Dict> = {
  zh: {
    appTitle: "扩散模型论文库",
    appSubtitle: "聚合顶会与 arXiv 的 Diffusion 方向论文",
    totalPapers: "论文总数",
    conferences: "会议数",
    years: "年份数",
    searchPlaceholder: "按标题、作者或关键词搜索…",
    allConferences: "全部会议",
    allYears: "全部年份",
    allTags: "全部标签",
    filterConference: "会议",
    filterYear: "年份",
    filterTag: "标签",
    authorsNA: "作者信息暂无",
    noResults: "未找到匹配的论文",
    noResultsHint: "试着调整搜索或筛选条件",
    loading: "正在加载论文…",
    loadFailed: "论文加载失败",
    loadFailedHint: "请确认后端服务已启动",
    viewPdf: "查看 PDF",
    viewAbs: "论文主页",
    close: "关闭",
    abstract: "摘要",
    abstractZhMissing: "（暂无中文摘要，以下为英文原文）",
    resultsCount: "共 {n} 篇",
    langSwitch: "EN",
    source: "来源",
  },
  en: {
    appTitle: "Diffusion Papers Hub",
    appSubtitle: "Diffusion research from top venues and arXiv",
    totalPapers: "Total Papers",
    conferences: "Conferences",
    years: "Years",
    searchPlaceholder: "Search by title, authors or keywords…",
    allConferences: "All Conferences",
    allYears: "All Years",
    allTags: "All Tags",
    filterConference: "Conference",
    filterYear: "Year",
    filterTag: "Tag",
    authorsNA: "Authors not available",
    noResults: "No papers found",
    noResultsHint: "Try adjusting your search or filters",
    loading: "Loading papers…",
    loadFailed: "Failed to load papers",
    loadFailedHint: "Please make sure the backend is running",
    viewPdf: "View PDF",
    viewAbs: "Paper Page",
    close: "Close",
    abstract: "Abstract",
    abstractZhMissing: "(No Chinese abstract yet, showing English original)",
    resultsCount: "{n} papers",
    langSwitch: "中",
    source: "Source",
  },
};

export interface I18nContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextValue>({
  lang: "zh",
  setLang: () => {},
  t: (key: string) => key,
});

export function useI18n() {
  return useContext(I18nContext);
}

export function translate(
  lang: Lang,
  key: string,
  vars?: Record<string, string | number>
): string {
  let str = translations[lang][key] ?? key;
  if (vars) {
    Object.entries(vars).forEach(([k, v]) => {
      str = str.replace(`{${k}}`, String(v));
    });
  }
  return str;
}
