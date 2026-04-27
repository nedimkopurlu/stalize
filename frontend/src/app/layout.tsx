import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Stalize — BIST100 Analiz Terminali",
  description: "BIST100 hisselerini teknik ve temel analiz ile değerlendirin",
  keywords: ["BIST100", "BIST30", "borsa", "hisse analiz", "teknik analiz", "temel analiz", "KAP"],
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
      className={inter.variable}
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
