import { Calendar } from "lucide-react";
import { useI18n } from "../i18n";
import type { Paper } from "../types";

interface Props {
  paper: Paper;
  onOpen: (p: Paper) => void;
}

export default function PaperCard({ paper, onOpen }: Props) {
  const { t, lang } = useI18n();

  const preview =
    lang === "zh" && paper.abstract_zh ? paper.abstract_zh : paper.abstract;

  return (
    <button
      onClick={() => onOpen(paper)}
      className="glass-card group flex flex-col rounded-2xl p-5 text-left shadow-md transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl cursor-pointer"
    >
      <h3 className="mb-2 line-clamp-2 text-base font-semibold leading-snug text-slate-800 transition group-hover:text-brand-600">
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
        <p className="mb-3 line-clamp-3 flex-1 text-sm leading-relaxed text-slate-600">
          {preview}
        </p>
      )}

      <div className="mt-auto flex flex-wrap gap-1.5">
        {paper.tags.slice(0, 4).map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-brand-50 px-2.5 py-0.5 text-[11px] text-brand-700"
          >
            {tag}
          </span>
        ))}
      </div>
    </button>
  );
}
