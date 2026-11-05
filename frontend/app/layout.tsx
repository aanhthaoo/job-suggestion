import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "JobPortal AI - Hệ thống tìm kiếm việc làm thông minh & BI Analytics",
  description: "Tìm việc làm phù hợp với AI Matching 5 thành phần và phân tích thị trường lao động",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className="antialiased flex flex-col min-h-screen bg-slate-50/50 text-slate-900">
        <Providers>
          <div className="flex-1">
            {children}
          </div>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
