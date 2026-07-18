import { useEffect } from "react";
import { X, FileText, ExternalLink, Calendar, Users } from "lucide-react";
import { useI18n } from "../i18n";
import type { Paper } from "../types";

interface Props {
  paper: Paper;
  onClose: () => void;
}

export default function PaperDetail({ paper, onClose }: Props) {
  const { t, lang } = useI18n();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const showZh = lang === "zh" && !!paper.abstract_zh;
  const abstractText = showZh ? paper.abstract_zh! : paper.abstract;
  const zhMissing = lang === "zh" && !paper.abstract_zh && !!paper.abstract;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 p-4 backdrop-blur-sm sm:p-8"
      onClick={onClose}
    >
      <div
        className="glass-card my-auto w-full max-w-3xl animate-scale-in rounded-2xl p-6 shadow-2xl sm:p-8"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-xl font-bold leading-snug text-slate-800 sm:text-2xl">
            {paper.title}
          </h2>
          <button
            onClick={onClose}
            className="shrink-0 rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            aria-label={t("close")}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Meta badges */}
        <div className="mb-5 flex flex-wrap items-center gap-3 text-sm">
          <span className="rounded-full bg-gradient-to-r from-brand-500 to-brand-700 px-3 py-1 font-medium text-white">
            {paper.conference}
          </span>
          {paper.year && (
            <span className="flex items-center gap-1 text-slate-500">
              <Calendar className="h-4 w-4" />
              {paper.year}
            </span>
          )}
          <span className="text-slate-400">
            {t("source")}: {paper.source}
          </span>
        </div>

        {/* Authors */}
        {paper.authors.length > 0 && (
          <div className="mb-5 flex items-start gap-2 text-sm text-slate-600">
            <Users className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            <span>{paper.authors.join(", ")}</span>
          </div>
        )}

        {/* Abstract */}
        {abstractText && (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
              {t("abstract")}
            </h3>
            {zhMissing && (
              <p className="mb-2 text-xs italic text-amber-600">
                {t("abstractZhMissing")}
              </p>
            )}
            <p className="text-sm leading-relaxed text-slate-700">
              {abstractText}
            </p>
          </div>
        )}

        {/* Tags */}
        {paper.tags.length > 0 && (
          <div className="mb-6 flex flex-wrap gap-2">
            {paper.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-brand-50 px-3 py-1 text-xs text-brand-700"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Links */}
        <div className="flex flex-wrap gap-3">
          {paper.pdf_url && (
            <a
              href={paper.pdf_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700 active:scale-95"
            >
              <FileText className="h-4 w-4" />
              {t("viewPdf")}
            </a>
          )}
          {paper.abs_url && (
            <a
              href={paper.abs_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 rounded-xl bg-slate-100 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-200 active:scale-95"
            >
              <ExternalLink className="h-4 w-4" />
              {t("viewAbs")}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
