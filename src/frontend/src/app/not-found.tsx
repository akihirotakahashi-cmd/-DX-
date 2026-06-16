import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gray-50 text-center">
      <p className="text-6xl font-bold text-gray-200">404</p>
      <p className="text-xl font-medium text-gray-700">ページが見つかりません</p>
      <p className="text-sm text-gray-500">URLが正しいかご確認ください</p>
      <Link href="/proposals" className="mt-4 text-sm text-primary-600 hover:underline">
        トップへ戻る
      </Link>
    </div>
  );
}
