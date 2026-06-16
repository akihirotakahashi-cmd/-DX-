import { clsx } from "clsx";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  reviewing_tl: "bg-yellow-100 text-yellow-800",
  reviewing_mgr: "bg-orange-100 text-orange-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-500",
  superseded: "bg-gray-100 text-gray-400",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "下書き",
  reviewing_tl: "TLレビュー中",
  reviewing_mgr: "マネージャーレビュー中",
  approved: "承認済",
  rejected: "却下",
  cancelled: "キャンセル",
  superseded: "差し替え済",
};

interface BadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STATUS_COLORS[status] ?? "bg-gray-100 text-gray-700",
        className
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}
