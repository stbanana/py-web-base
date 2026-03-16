import type { Metadata } from "next";
import { I18nProvider } from "@/components/i18n-provider";
import { AppThemeProvider } from "@/components/theme-provider";
import "@carbon/styles/css/styles.css";
import "./globals.scss";

export const metadata: Metadata = {
  title: "yoroATS",
  description: "yoroATS frontend",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>
          <AppThemeProvider>{children}</AppThemeProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
