import type { Metadata } from "next";
import { Inter, Manrope, JetBrains_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const themeBootstrap = `try{const t=localStorage.getItem('kazilayer-theme');document.documentElement.classList.toggle('dark',t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches))}catch{}`;

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const mono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "KaziLayer | Operations control centre",
  description: "One versioned operational contract for requests, dispatch, field work, and audit.",
  icons: { icon: "/icons/favicon.svg", apple: "/icons/apple-touch-icon-180.png" },
  manifest: "/web/site.webmanifest",
  openGraph: { title: "KaziLayer", description: "Work in one flow", images: ["/social/social-card-1200x630.png"] },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${manrope.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="min-h-full" suppressHydrationWarning>
        <Script id="theme-bootstrap" strategy="beforeInteractive">
          {themeBootstrap}
        </Script>
        {children}
      </body>
    </html>
  );
}
