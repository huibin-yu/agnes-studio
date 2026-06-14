import Navbar from "@/components/navbar"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "AI 视频生成 - Agnes Studio",
  description: "使用 AI 生成精美视频，支持文生视频、图生视频、多种参数调节",
  openGraph: {
    title: "AI 视频生成 - Agnes Studio",
    description: "使用 AI 生成精美视频，支持文生视频、图生视频、多种参数调节",
    type: "website",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main id="main-content" className="">{children}</main>
    </div>
  )
}
