import { Search, X } from "lucide-react";
import { useI18n } from "../i18n";
import type { Filters, Meta } from "../types";

interface Props {
  meta: Meta | null;
  filters: Filters;
  searchInput: string;
  onSearchInput: (v: string) => void;
  onChange: (patch: Partial<Filters>) => void;
}

export default function FilterBar({
  meta,
  filters,
  searchInput,
  onSearchInput,
  onChange,
}: Props) {
  const { t } = useI18n();

  const selectClass =
    "w-full appearance-none rounded-xl border-0 bg-white/90 px-4 py-2.5 text-sm text-slate-700 shadow-sm outline-none ring-1 ring-white/40 transition focus:ring-2 focus:ring-brand-500 cursor-pointer";

  return (
    <div className="flex flex-col gap-4">
      {/* Search */}
      <div className="glass-card flex items-center gap-3 rounded-2xl px-4 py-3 shadow-lg">
        <Search className="h-5 w-5 shrink-0 text-slate-400" />
        <input
          type="text"
          value={searchInput}
          onChange={(e) => onSearchInput(e.target.value)}
          placeholder={t("searchPlaceholder")}
          className="w-full border-0 bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
        />
        {searchInput && (
          <button
            onClick={() => onSearchInput("")}
            className="text-slate-400 transition hover:text-slate-600"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Dropdowns */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <select
          value={filters.conference}
          onChange={(e) => onChange({ conference: e.target.value })}
          className={selectClass}
        >
          <option value="">{t("allConferences")}</option>
          {meta?.conferences.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select
          value={filters.year}
          onChange={(e) => onChange({ year: e.target.value })}
          className={selectClass}
        >
          <option value="">{t("allYears")}</option>
          {meta?.years.map((y) => (
            <option key={y} value={String(y)}>
              {y}
            </option>
          ))}
        </select>

        <select
          value={filters.tag}
          onChange={(e) => onChange({ tag: e.target.value })}
          className={selectClass}
        >
          <option value="">{t("allTags")}</option>
          {meta?.tags.map((tag) => (
            <option key={tag} value={tag}>
              {t(`tag.${tag}`)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
