"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell } from "lucide-react";
import { clsx } from "clsx";
import api, { Notification } from "@/lib/api";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  const loadCount = async () => {
    try {
      const res = await api.get<{ count: number }>("/notifications/unread-count");
      setUnreadCount(res.data.count);
    } catch {}
  };

  const loadNotifications = async () => {
    try {
      const res = await api.get<Notification[]>("/notifications");
      setNotifications(res.data);
    } catch {}
  };

  useEffect(() => {
    loadCount();
    const interval = setInterval(loadCount, 30_000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (open) loadNotifications();
  }, [open]);

  // ドロップダウン外クリックで閉じる
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const markAllRead = async () => {
    await api.patch("/notifications/read-all");
    setUnreadCount(0);
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const markRead = async (id: string) => {
    await api.patch(`/notifications/${id}/read`);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    setUnreadCount((c) => Math.max(0, c - 1));
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
        aria-label="通知"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute right-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-50 w-80 rounded-lg border border-gray-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
            <span className="text-sm font-semibold">通知</span>
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-primary-600 hover:underline"
              >
                すべて既読
              </button>
            )}
          </div>

          <ul className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <li className="px-4 py-6 text-center text-sm text-gray-400">通知はありません</li>
            ) : (
              notifications.map((n) => (
                <li
                  key={n.id}
                  className={clsx(
                    "border-b border-gray-50 last:border-0",
                    !n.read && "bg-blue-50"
                  )}
                >
                  {n.link_url ? (
                    <Link
                      href={n.link_url}
                      onClick={() => { markRead(n.id); setOpen(false); }}
                      className="block px-4 py-3 hover:bg-gray-50"
                    >
                      <NotificationItem notification={n} />
                    </Link>
                  ) : (
                    <button
                      onClick={() => markRead(n.id)}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50"
                    >
                      <NotificationItem notification={n} />
                    </button>
                  )}
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

function NotificationItem({ notification: n }: { notification: Notification }) {
  return (
    <>
      <p className={clsx("text-sm", !n.read && "font-medium text-gray-900", n.read && "text-gray-600")}>
        {n.message}
      </p>
      <p className="mt-0.5 text-xs text-gray-400">
        {new Date(n.created_at).toLocaleString("ja-JP", {
          month: "numeric",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
      </p>
    </>
  );
}
