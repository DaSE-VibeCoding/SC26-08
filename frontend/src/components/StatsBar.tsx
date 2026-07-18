import { FileText, Building2, CalendarDays } from "lucide-react";
import { useI18n } from "../i18n";
import type { Meta } from "../types";

interface Props {
  meta: Meta | null;
}

export default function StatsBar({ meta }: Props) {
  const { t } = useI18n();

  const cards = [
    {
      icon: FileText,
      label: t("totalPapers"),
      value: meta?.total ?? 0,
    },
    {
      icon: Building2,
      label: t("conferences"),
      value: meta?.conferences.length ?? 0,
    },
    {
      icon: CalendarDays,
      label: t("years"),
      value: meta?.years.length ?? 0,
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3 sm:gap-5">
      {cards.map((c) => (
        <div
          key={c.label}
          className="glass flex flex-col items-center rounded-2xl px-3 py-4 text-white sm:px-6 sm:py-5"
        >
          <c.icon className="mb-2 h-5 w-5 text-white/80 sm:h-6 sm:w-6" />
          <div className="text-2xl font-bold sm:text-3xl">{c.value}</div>
          <div className="text-center text-xs text-white/75 sm:text-sm">
            {c.label}
          </div>
        </div>
      ))}
    </div>
  );
}
