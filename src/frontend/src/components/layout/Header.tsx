"use client";

import { useAuthStore } from "@/store/auth";
import { NotificationBell } from "@/components/notifications/NotificationBell";

export function Header() {
  const { role } = useAuthStore();

  const roleLabel: Record<string, string> = {
    consultant: "コンサルタント",
    tl: "チームリーダー",
    manager: "マネージャー",
    system_admin: "システム管理者",
  };

  return (
    <header className="flex h-14 items-center justify-end gap-4 border-b border-gray-200 bg-white px-6">
      {role && (
        <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
          {roleLabel[role] ?? role}
        </span>
      )}
      <NotificationBell />
    </header>
  );
}
