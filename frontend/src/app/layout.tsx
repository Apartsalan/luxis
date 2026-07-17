import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Luxis — Praktijkmanagement",
  description: "Praktijkmanagementsysteem voor de Nederlandse Advocatuur",
  manifest: "/manifest.webmanifest",
  // iOS negeert manifest-iconen en -naam volledig; deze twee zijn verplicht,
  // anders toont "Zet op beginscherm" een schermafdruk + de domeinnaam.
  appleWebApp: {
    capable: true,
    title: "Luxis",
    statusBarStyle: "default",
  },
  icons: {
    icon: "/icon-192.png",
    apple: "/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // cover = de app mag onder de notch/home-indicator tekenen; onze safe-area
  // helpers (globals.css) houden knoppen en balken vrij van de systeem-UI.
  viewportFit: "cover",
  themeColor: "#1d4fd7",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="nl" className={inter.variable}>
      <body className="min-h-screen font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
