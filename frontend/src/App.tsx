import { useEffect, useMemo, useRef, useState } from "react";
import Header from "./components/Header";
import StatsBar from "./components/StatsBar";
import FilterBar from "./components/FilterBar";
import PaperCard from "./components/PaperCard";
import PaperDetail from "./components/PaperDetail";
import PaperWorkspace from "./components/PaperWorkspace";
import { I18nContext, translate } from "./i18n";
import { fetchMeta, fetchPapers, updatePaperState } from "./api/client";
import type { Filters, Lang, Meta, Paper } from "./types";
import { Loader2, FileSearch, AlertTriangle, BookOpenCheck, BookOpenText, Download, Library, Star } from "lucide-react";

const EMPTY_FILTERS: Filters = { conference: "", year: "", tag: "", q: "", library: "all" };

export default function App() {
  const [lang, setLang] = useState<Lang>("zh");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [downloadingNotes, setDownloadingNotes] = useState(false);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<Paper | null>(null);
  const [workspacePaper, setWorkspacePaper] = useState<Paper | null>(null);

  const debounceRef = useRef<number | null>(null);

  const i18nValue = useMemo(
    () => ({
      lang,
      setLang,
      t: (key: string, vars?: Record<string, string | number>) =>
        translate(lang, key, vars),
    }),
    [lang]
  );

  // Load meta once
  useEffect(() => {
    fetchMeta()
      .then(setMeta)
      .catch(() => setError(true));
  }, []);

  // Debounce search input into filters.q
  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      setFilters((f) => ({ ...f, q: searchInput.trim() }));
    }, 300);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [searchInput]);

  // Fetch papers on filter change
  useEffect(() => {
    setLoading(true);
    setError(false);
    fetchPapers(filters, 60, 0)
      .then((res) => {
        setPapers(res.items);
        setTotal(res.total);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [filters]);

  const handleFilterChange = (patch: Partial<Filters>) =>
    setFilters((f) => ({ ...f, ...patch }));

  const handleStateChange = async (
    paper: Paper,
    patch: { is_read?: boolean; is_favorite?: boolean }
  ) => {
    try {
      const updated = await updatePaperState(paper.id, patch);
      const leavesCurrentView =
        (filters.library === "read" && !updated.is_read) ||
        (filters.library === "favorites" && !updated.is_favorite);
      setPapers((items) => leavesCurrentView
        ? items.filter((item) => item.id !== updated.id)
        : items.map((item) => item.id === updated.id ? updated : item));
      if (leavesCurrentView) setTotal((value) => Math.max(0, value - 1));
      setSelected((current) => current?.id === updated.id ? updated : current);
    } catch {
      window.alert(i18nValue.t("stateUpdateFailed"));
    }
  };

  const handleLoadMore = async () => {
    setLoadingMore(true);
    try {
      const res = await fetchPapers(filters, 60, papers.length);
      setPapers((items) => {
        const existingIds = new Set(items.map((item) => item.id));
        return [...items, ...res.items.filter((item) => !existingIds.has(item.id))];
      });
      setTotal(res.total);
    } catch {
      window.alert(i18nValue.t("loadMoreFailed"));
    } finally {
      setLoadingMore(false);
    }
  };

  const handlePaperChange = (updated: Paper) => {
    const leavesNotesView = filters.library === "notes" && !updated.note.trim();
    setPapers((items) => leavesNotesView
      ? items.filter((item) => item.id !== updated.id)
      : items.map((item) => item.id === updated.id ? updated : item));
    if (leavesNotesView) setTotal((value) => Math.max(0, value - 1));
    setSelected((current) => current?.id === updated.id ? updated : current);
    setWorkspacePaper((current) => current?.id === updated.id ? updated : current);
  };

  const handleDownloadAllNotes = async () => {
    setDownloadingNotes(true);
    try {
      const allNotes: Paper[] = [];
      let offset = 0;
      let expected = 1;
      while (offset < expected) {
        const res = await fetchPapers(filters, 200, offset);
        allNotes.push(...res.items);
        expected = res.total;
        offset += res.items.length;
        if (res.items.length === 0) break;
      }
      const markdown = allNotes.map((paper) => [
        `# ${paper.title}`,
        "",
        `- ${i18nValue.t("authorsLabel")}: ${paper.authors.join(", ") || i18nValue.t("authorsNA")}`,
        `- ${i18nValue.t("venueLabel")}: ${paper.conference}${paper.year ? ` (${paper.year})` : ""}`,
        paper.abs_url ? `- ${i18nValue.t("paperLinkLabel")}: ${paper.abs_url}` : "",
        "",
        paper.note,
        "",
        "---",
        "",
      ].filter(Boolean).join("\n")).join("\n");
      const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `paper-notes-${new Date().toISOString().slice(0, 10)}.md`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      window.alert(i18nValue.t("downloadNotesFailed"));
    } finally {
      setDownloadingNotes(false);
    }
  };

  return (
    <I18nContext.Provider value={i18nValue}>
      <div className="min-h-screen font-sans">
        <Header />

        <main className="mx-auto max-w-6xl px-4 pb-16 pt-6 sm:px-8">
          <div className="mb-6">
            <StatsBar meta={meta} />
          </div>

          <div className="mb-6">
            <FilterBar
              meta={meta}
              filters={filters}
              searchInput={searchInput}
              onSearchInput={setSearchInput}
              onChange={handleFilterChange}
            />
          </div>

          <nav className="mb-5 flex flex-wrap gap-2" aria-label={i18nValue.t("paperLibrary") }>
            {([
              ["all", Library, "allPapers"],
              ["read", BookOpenCheck, "readPapers"],
              ["favorites", Star, "myFavorites"],
              ["notes", BookOpenText, "paperNotes"],
            ] as const).map(([value, Icon, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => handleFilterChange({ library: value })}
                className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium shadow-sm transition ${filters.library === value ? "bg-white text-brand-700 ring-2 ring-brand-300" : "bg-white/20 text-white hover:bg-white/30"}`}
              >
                <Icon className={`h-4 w-4 ${value === "favorites" && filters.library === value ? "fill-amber-400 text-amber-400" : ""}`} />
                {i18nValue.t(label)}
              </button>
            ))}
          </nav>

          {filters.library === "notes" && total > 0 && (
            <div className="mb-5 flex justify-end">
              <button
                type="button"
                onClick={handleDownloadAllNotes}
                disabled={downloadingNotes}
                className="flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-brand-700 shadow-sm transition hover:shadow-md disabled:cursor-wait disabled:opacity-70"
              >
                {downloadingNotes ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                {i18nValue.t(downloadingNotes ? "preparingDownload" : "downloadAllNotes")}
              </button>
            </div>
          )}

          {!loading && !error && (
            <p className="mb-4 text-sm text-white/85">
              {i18nValue.t("resultsCount", { n: total })}
            </p>
          )}

          {loading ? (
            <div className="flex flex-col items-center gap-3 py-20 text-white">
              <Loader2 className="h-8 w-8 animate-spin" />
              <p>{i18nValue.t("loading")}</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center gap-3 py-20 text-white">
              <AlertTriangle className="h-10 w-10" />
              <h2 className="text-lg font-semibold">
                {i18nValue.t("loadFailed")}
              </h2>
              <p className="text-white/80">{i18nValue.t("loadFailedHint")}</p>
            </div>
          ) : papers.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-20 text-white">
              <FileSearch className="h-10 w-10" />
              <h2 className="text-lg font-semibold">
                {i18nValue.t("noResults")}
              </h2>
              <p className="text-white/80">{i18nValue.t("noResultsHint")}</p>
            </div>
          ) : (
            <div>
              <div className="grid grid-cols-1 gap-5 animate-fade-in sm:grid-cols-2 lg:grid-cols-3">
                {papers.map((p) => (
                  <PaperCard
                    key={p.id}
                    paper={p}
                    onOpen={filters.library === "notes" ? setWorkspacePaper : setSelected}
                    onStateChange={handleStateChange}
                    showNote={filters.library === "notes"}
                  />
                ))}
              </div>
              {papers.length < total && (
                <div className="mt-8 flex flex-col items-center gap-2">
                  <button
                    type="button"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-brand-700 shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-wait disabled:opacity-70"
                  >
                    {loadingMore && <Loader2 className="h-4 w-4 animate-spin" />}
                    {i18nValue.t(loadingMore ? "loadingMore" : "loadMore")}
                  </button>
                  <p className="text-xs text-white/75">
                    {i18nValue.t("loadedProgress", { loaded: papers.length, total })}
                  </p>
                </div>
              )}
            </div>
          )}
        </main>

        {selected && (
          <PaperDetail
            paper={selected}
            onClose={() => setSelected(null)}
            onStateChange={handleStateChange}
            onOpenWorkspace={(paper) => {
              setWorkspacePaper(paper);
              setSelected(null);
            }}
          />
        )}
        {workspacePaper && (
          <PaperWorkspace
            paper={workspacePaper}
            onClose={() => setWorkspacePaper(null)}
            onPaperChange={handlePaperChange}
          />
        )}
      </div>
    </I18nContext.Provider>
  );
}
