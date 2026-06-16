"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { FileText, ClipboardCheck, Send, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/auth";

const navItems = [
  { href: "/proposals", label: "施策提案", icon: FileText },
  { href: "/reviews", label: "承認フロー", icon: ClipboardCheck, roles: ["tl", "manager"] },
  { href: "/deliveries", label: "納品管理", icon: Send },
];

export function Sidebar() {
  const pathname = usePathname();
  const { role, email, signOut } = useAuthStore();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center border-b border-gray-200 px-6">
        <span className="text-lg font-bold text-primary-700">地方創生DX</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {navItems
            .filter((item) => !item.roles || (role && item.roles.includes(role)))
            .map(({ href, label, icon: Icon }) => (
              <li key={href}>
                <Link
                  href={href}
                  className={clsx(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    pathname.startsWith(href)
                      ? "bg-primary-50 text-primary-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              </li>
            ))}
        </ul>
      </nav>

      <div className="border-t border-gray-200 px-3 py-4">
        <p className="truncate px-3 text-xs text-gray-500">{email}</p>
        <button
          onClick={signOut}
          className="mt-1 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <LogOut className="h-4 w-4" />
          ログアウト
        </button>
      </div>
    </aside>
  );
}
