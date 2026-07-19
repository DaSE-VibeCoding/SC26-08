import { Calendar, Eye, EyeOff, Star } from "lucide-react";
import { useI18n } from "../i18n";
import type { Paper } from "../types";

interface Props {
  paper: Paper;
  onOpen: (p: Paper) => void;
  onStateChange: (paper: Paper, patch: { is_read?: boolean; is_favorite?: boolean }) => void;
  showNote?: boolean;
}

export default function PaperCard({ paper, onOpen, onStateChange, showNote = false }: Props) {
  const { t } = useI18n();

  const preview = showNote ? paper.note : paper.abstract;

  return (
    <article
      onClick={() => onOpen(paper)}
      onKeyDown={(event) => {
        if (event.target !== event.currentTarget) return;
        if (event.key === "Enter" || event.key === " ") onOpen(paper);
      }}
      role="button"
      tabIndex={0}
      className={`glass-card group relative flex flex-col rounded-2xl p-5 text-left shadow-md transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl cursor-pointer ${paper.is_read ? "opacity-80" : ""}`}
    >
      <div className="absolute right-3 top-3 flex gap-1">
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onStateChange(paper, { is_read: !paper.is_read });
          }}
          className={`rounded-full p-2 transition ${paper.is_read ? "bg-emerald-100 text-emerald-700" : "bg-white/80 text-slate-400 hover:text-slate-700"}`}
          title={t(paper.is_read ? "markUnread" : "markRead")}
          aria-label={t(paper.is_read ? "markUnread" : "markRead")}
        >
          {paper.is_read ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
        </button>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onStateChange(paper, { is_favorite: !paper.is_favorite });
          }}
          className={`rounded-full p-2 transition ${paper.is_favorite ? "bg-amber-100 text-amber-500" : "bg-white/80 text-slate-400 hover:text-amber-500"}`}
          title={t(paper.is_favorite ? "removeFavorite" : "addFavorite")}
          aria-label={t(paper.is_favorite ? "removeFavorite" : "addFavorite")}
        >
          <Star className={`h-4 w-4 ${paper.is_favorite ? "fill-current" : ""}`} />
        </button>
      </div>
      <h3 className="mb-2 line-clamp-2 pr-20 text-base font-semibold leading-snug text-slate-800 transition group-hover:text-brand-600">
        {paper.title}
      </h3>

      <p className="mb-3 line-clamp-1 text-xs text-slate-500">
        {paper.authors.length > 0
          ? paper.authors.join(", ")
          : t("authorsNA")}
      </p>

      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full bg-gradient-to-r from-brand-500 to-brand-700 px-3 py-1 font-medium text-white">
          {paper.conference}
        </span>
        {paper.year && (
          <span className="flex items-center gap-1 text-slate-500">
            <Calendar className="h-3.5 w-3.5" />
            {paper.year}
          </span>
        )}
      </div>

      {preview && (
        <div className={`mb-3 flex-1 ${showNote ? "rounded-xl bg-amber-50 p-3" : ""}`}>
          {showNote && <p className="mb-1 text-[11px] font-semibold text-amber-700">{t("notePreview")}</p>}
          <p className="line-clamp-5 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">{preview}</p>
        </div>
      )}

      <div className="mt-auto flex flex-wrap gap-1.5">
        {paper.tags.slice(0, 4).map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-brand-50 px-2.5 py-0.5 text-[11px] text-brand-700"
          >
            {t(`tag.${tag}`)}
          </span>
        ))}
      </div>
    </article>
  );
}
