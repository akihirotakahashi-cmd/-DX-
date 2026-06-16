"use client";

import { useToastStore } from "@/store/toast";
import { clsx } from "clsx";
import { CheckCircle, XCircle, Info, X } from "lucide-react";

const ICONS = {
  success: <CheckCircle className="h-5 w-5 text-green-500" />,
  error: <XCircle className="h-5 w-5 text-red-500" />,
  info: <Info className="h-5 w-5 text-blue-500" />,
};

const BG = {
  success: "border-green-200 bg-green-50",
  error: "border-red-200 bg-red-50",
  info: "border-blue-200 bg-blue-50",
};

export function ToastContainer() {
  const { toasts, dismiss } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={clsx(
            "flex items-start gap-3 rounded-lg border px-4 py-3 shadow-md",
            BG[t.type]
          )}
          style={{ minWidth: 280, maxWidth: 400 }}
        >
          {ICONS[t.type]}
          <p className="flex-1 text-sm font-medium text-gray-800">{t.message}</p>
          <button onClick={() => dismiss(t.id)} className="text-gray-400 hover:text-gray-600">
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
