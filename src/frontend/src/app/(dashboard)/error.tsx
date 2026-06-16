"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/Button";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <p className="text-4xl font-bold text-gray-300">エラー</p>
      <p className="mt-4 text-lg font-medium text-gray-700">
        予期しないエラーが発生しました
      </p>
      <p className="mt-2 text-sm text-gray-500">{error.message}</p>
      <Button className="mt-8" onClick={reset}>
        再試行
      </Button>
    </div>
  );
}
