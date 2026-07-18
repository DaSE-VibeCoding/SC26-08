import { Sparkles, Languages } from "lucide-react";
import { useI18n } from "../i18n";

export default function Header() {
  const { t, lang, setLang } = useI18n();

  return (
    <header className="glass sticky top-0 z-30 w-full rounded-b-2xl px-4 py-3 sm:px-8 sm:py-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/25">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white sm:text-2xl">
              {t("appTitle")}
            </h1>
            <p className="hidden text-xs text-white/80 sm:block">
              {t("appSubtitle")}
            </p>
          </div>
        </div>

        <button
          onClick={() => setLang(lang === "zh" ? "en" : "zh")}
          className="flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm font-medium text-white transition-all hover:bg-white/35 hover:shadow-lg active:scale-95"
        >
          <Languages className="h-4 w-4" />
          {t("langSwitch")}
        </button>
      </div>
    </header>
  );
}
