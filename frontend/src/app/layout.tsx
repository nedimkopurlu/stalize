import type { Metadata } from "next";
import { Inter, Fraunces } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Stalize — Borsa İstanbul Analiz Terminali",
  description: "BIST hisselerini teknik ve temel analiz ile değerlendirin — 400+ hisse, tarama motoru, portföy takibi",
  keywords: ["BIST100", "BIST30", "BIST250", "borsa", "hisse analiz", "teknik analiz", "temel analiz", "KAP", "screener"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      suppressHydrationWarning
      className={`${inter.variable} ${fraunces.variable}`}
      style={
        {
          '--font-display': '"Inter", "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif',
          '--font-mono': '"SFMono-Regular", "Menlo", "Monaco", "Consolas", monospace',
        } as React.CSSProperties
      }
    >
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
