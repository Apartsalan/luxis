import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Luxis — Praktijkmanagement",
  description: "Praktijkmanagementsysteem voor de Nederlandse Advocatuur",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="nl">
      <body className="min-h-screen bg-cream-50 text-navy-800">
        {children}
      </body>
    </html>
  );
}
