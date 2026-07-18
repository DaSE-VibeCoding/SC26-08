import { useEffect, useMemo, useRef, useState } from "react";
import Header from "./components/Header";
import StatsBar from "./components/StatsBar";
import FilterBar from "./components/FilterBar";
import PaperCard from "./components/PaperCard";
import PaperDetail from "./components/PaperDetail";
import { I18nContext, translate } from "./i18n";
import { fetchMeta, fetchPapers } from "./api/client";
import type { Filters, Lang, Meta, Paper } from "./types";
import { Loader2, FileSearch, AlertTriangle } from "lucide-react";

const EMPTY_FILTERS: Filters = { conference: "", year: "", tag: "", q: "" };

export default function App() {
  const [lang, setLang] = useState<Lang>("zh");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selected, setSelected] = useState<Paper | null>(null);

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
            <div className="grid grid-cols-1 gap-5 animate-fade-in sm:grid-cols-2 lg:grid-cols-3">
              {papers.map((p) => (
                <PaperCard key={p.id} paper={p} onOpen={setSelected} />
              ))}
            </div>
          )}
        </main>

        {selected && (
          <PaperDetail paper={selected} onClose={() => setSelected(null)} />
        )}
      </div>
    </I18nContext.Provider>
  );
}
