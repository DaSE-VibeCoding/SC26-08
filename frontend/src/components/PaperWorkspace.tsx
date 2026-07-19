import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Bold, Calendar, CheckSquare, Download, ExternalLink, Eye, Heading2, List, Pencil, Quote, Save, Star } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { updatePaperNote } from "../api/client";
import { useI18n } from "../i18n";
import type { Paper } from "../types";

interface Props {
  paper: Paper;
  onClose: () => void;
  onPaperChange: (paper: Paper) => void;
}

export default function PaperWorkspace({ paper, onClose, onPaperChange }: Props) {
  const { t, lang } = useI18n();
  const [note, setNote] = useState(paper.note || "");
  const [saveState, setSaveState] = useState<"saved" | "saving" | "error">("saved");
  const [noteMode, setNoteMode] = useState<"edit" | "preview">("edit");
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const documentUrl = paper.pdf_url || paper.abs_url;

  const insertMarkdown = (before: string, after = "") => {
    const textarea = noteRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = note.slice(start, end);
    const next = `${note.slice(0, start)}${before}${selected}${after}${note.slice(end)}`;
    setNote(next);
    window.requestAnimationFrame(() => {
      textarea.focus();
      textarea.setSelectionRange(start + before.length, end + before.length);
    });
  };

  const insertTemplate = (kind: string) => {
    const templates: Record<string, Record<string, string>> = {
      quick: {
        zh: "## 核心问题\n\n## 核心方法\n\n## 主要结论\n\n## 我的评价\n\n## 后续事项\n- [ ] ",
        en: "## Research Question\n\n## Method\n\n## Findings\n\n## My Evaluation\n\n## Follow-ups\n- [ ] ",
      },
      deep: {
        zh: "## 研究背景与动机\n\n## 方法与创新点\n\n## 实验设计\n\n## 关键结果\n\n## 局限与疑问\n\n## 与已有工作的联系\n\n## 可借鉴的内容\n",
        en: "## Background & Motivation\n\n## Method & Novelty\n\n## Experiments\n\n## Key Results\n\n## Limitations & Questions\n\n## Related Work\n\n## Takeaways\n",
      },
      reproduce: {
        zh: "## 复现目标\n\n## 代码与数据\n\n## 环境配置\n\n## 关键超参数\n\n## 复现步骤\n- [ ] 获取代码和数据\n- [ ] 配置环境\n- [ ] 运行基线\n- [ ] 对比结果\n\n## 问题记录\n",
        en: "## Reproduction Goal\n\n## Code & Data\n\n## Environment\n\n## Hyperparameters\n\n## Steps\n- [ ] Get code and data\n- [ ] Configure environment\n- [ ] Run baseline\n- [ ] Compare results\n\n## Issues\n",
      },
    };
    const template = templates[kind]?.[lang];
    if (!template) return;
    setNote((current) => current.trim() ? `${current.trimEnd()}\n\n---\n\n${template}` : template);
    setNoteMode("edit");
  };

  const downloadNote = () => {
    const markdown = `# ${paper.title}\n\n${note}\n`;
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeTitle = paper.title.replace(/[\\/:*?"<>|]/g, "-").slice(0, 80);
    link.href = url;
    link.download = `${safeTitle || "paper-note"}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const noteTools: Array<{ Icon: LucideIcon; action: () => void; label: string }> = [
    { Icon: Heading2, action: () => insertMarkdown("## "), label: "heading" },
    { Icon: Bold, action: () => insertMarkdown("**", "**"), label: "bold" },
    { Icon: List, action: () => insertMarkdown("- "), label: "bulletList" },
    { Icon: CheckSquare, action: () => insertMarkdown("- [ ] "), label: "taskList" },
    { Icon: Quote, action: () => insertMarkdown("> "), label: "quote" },
  ];

  useEffect(() => {
    setNote(paper.note || "");
    setSaveState("saved");
  }, [paper.id]);

  useEffect(() => {
    if (note === (paper.note || "")) return;
    setSaveState("saving");
    const timer = window.setTimeout(async () => {
      try {
        const updated = await updatePaperNote(paper.id, note);
        onPaperChange(updated);
        setSaveState("saved");
      } catch {
        setSaveState("error");
      }
    }, 800);
    return () => window.clearTimeout(timer);
  }, [note, paper.id, paper.note, onPaperChange]);

  return (
    <div className="fixed inset-0 z-[60] flex flex-col bg-gradient-to-br from-[#667eea] to-[#764ba2]">
      <header className="glass flex items-center justify-between gap-4 border-b border-white/20 px-4 py-3 shadow-sm">
        <button
          type="button"
          onClick={onClose}
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-white transition hover:bg-white/20"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("backToLibrary")}
        </button>
        <p className="min-w-0 truncate text-lg font-bold text-white">{paper.title}</p>
        {paper.abs_url && (
          <a
            href={paper.abs_url}
            target="_blank"
            rel="noreferrer"
            className="flex shrink-0 items-center gap-1.5 rounded-lg bg-white/20 px-3 py-2 text-xs font-medium text-white hover:bg-white/30"
          >
            <ExternalLink className="h-4 w-4" />
            {t("viewAbs")}
          </a>
        )}
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <section className="min-h-[55vh] bg-transparent p-2 lg:min-h-0">
          {documentUrl ? (
            <iframe
              key={documentUrl}
              src={documentUrl}
              title={paper.title}
              className="h-full min-h-[55vh] w-full rounded-xl border-0 bg-white shadow-xl lg:min-h-0"
              referrerPolicy="no-referrer-when-downgrade"
            />
          ) : (
            <div className="glass flex h-full items-center justify-center rounded-xl text-sm text-white">
              {t("paperPageUnavailable")}
            </div>
          )}
        </section>

        <aside className="relative flex min-h-0 flex-col gap-4 overflow-y-auto border-l border-white/20 bg-white/10 p-4 backdrop-blur-sm lg:overflow-hidden">
          <section className="shrink-0 rounded-2xl bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-start justify-between gap-3">
              <h2 className="text-xl font-bold leading-snug text-slate-800">{paper.title}</h2>
              {paper.is_favorite && <Star className="h-5 w-5 shrink-0 fill-amber-400 text-amber-400" />}
            </div>
            <p className="mb-3 text-sm leading-relaxed text-slate-500">
              {paper.authors.length ? paper.authors.join(", ") : t("authorsNA")}
            </p>
            <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-full bg-brand-600 px-3 py-1 font-medium text-white">{paper.conference}</span>
              {paper.year && (
                <span className="flex items-center gap-1 text-slate-500">
                  <Calendar className="h-3.5 w-3.5" /> {paper.year}
                </span>
              )}
            </div>
          </section>

          <section className="flex min-h-[320px] flex-1 flex-col rounded-2xl bg-white p-5 shadow-sm">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-semibold text-slate-800">{t("myNotes")}</h3>
              <div className="flex items-center gap-2">
                <button type="button" onClick={() => setNoteMode("edit")} className={`rounded-lg p-1.5 ${noteMode === "edit" ? "bg-brand-100 text-brand-700" : "text-slate-400 hover:bg-slate-100"}`} title={t("editNote")}>
                  <Pencil className="h-3.5 w-3.5" />
                </button>
                <button type="button" onClick={() => setNoteMode("preview")} className={`rounded-lg p-1.5 ${noteMode === "preview" ? "bg-brand-100 text-brand-700" : "text-slate-400 hover:bg-slate-100"}`} title={t("previewNote")}>
                  <Eye className="h-3.5 w-3.5" />
                </button>
                <button type="button" onClick={downloadNote} className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-brand-700" title={t("downloadCurrentNote")}>
                  <Download className="h-3.5 w-3.5" />
                </button>
                <span className={`flex items-center gap-1 text-xs ${saveState === "error" ? "text-red-600" : "text-slate-400"}`}>
                  <Save className="h-3.5 w-3.5" />
                  {t(saveState === "saving" ? "savingNote" : saveState === "error" ? "noteSaveFailed" : "noteSaved")}
                </span>
              </div>
            </div>
            <div className="mb-3 flex flex-wrap items-center gap-1.5">
              <select defaultValue="" onChange={(event) => { insertTemplate(event.target.value); event.target.value = ""; }} className="mr-1 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-600 outline-none">
                <option value="" disabled>{t("noteTemplate")}</option>
                <option value="quick">{t("quickTemplate")}</option>
                <option value="deep">{t("deepTemplate")}</option>
                <option value="reproduce">{t("reproduceTemplate")}</option>
              </select>
              {noteTools.map(({ Icon, action, label }) => (
                <button key={label} type="button" onClick={action} className="rounded-lg border border-slate-200 p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-brand-700" title={t(label)}>
                  <Icon className="h-3.5 w-3.5" />
                </button>
              ))}
            </div>
            {noteMode === "edit" ? (
              <textarea
                ref={noteRef}
                value={note}
                maxLength={50000}
                onChange={(event) => setNote(event.target.value)}
                onBlur={async () => {
                  if (note === (paper.note || "")) return;
                  try {
                    const updated = await updatePaperNote(paper.id, note);
                    onPaperChange(updated);
                    setSaveState("saved");
                  } catch {
                    setSaveState("error");
                  }
                }}
                placeholder={t("notePlaceholder")}
                className="min-h-[260px] flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 p-4 font-mono text-sm leading-relaxed text-slate-700 outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
              />
            ) : (
              <div className="min-h-[260px] flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-relaxed text-slate-700">
                {note ? note.split("\n").map((line, index) => {
                  if (line.startsWith("## ")) return <h3 key={index} className="mb-2 mt-4 text-base font-bold text-slate-800 first:mt-0">{line.slice(3)}</h3>;
                  if (line.startsWith("# ")) return <h2 key={index} className="mb-2 mt-4 text-lg font-bold text-slate-900 first:mt-0">{line.slice(2)}</h2>;
                  if (line.startsWith("- [ ] ")) return <p key={index} className="my-1">☐ {line.slice(6)}</p>;
                  if (line.startsWith("- [x] ")) return <p key={index} className="my-1 text-slate-400 line-through">☑ {line.slice(6)}</p>;
                  if (line.startsWith("- ")) return <p key={index} className="my-1 pl-2">• {line.slice(2)}</p>;
                  if (line.startsWith("> ")) return <blockquote key={index} className="my-2 border-l-4 border-brand-300 pl-3 italic text-slate-500">{line.slice(2)}</blockquote>;
                  if (line === "---") return <hr key={index} className="my-4 border-slate-200" />;
                  return <p key={index} className={line ? "my-1" : "h-3"}>{line}</p>;
                }) : <p className="text-slate-400">{t("emptyNotePreview")}</p>}
              </div>
            )}
            <p className="mt-2 text-right text-xs text-slate-400">{note.length.toLocaleString()} / 50,000</p>
          </section>
        </aside>
      </div>
    </div>
  );
}
