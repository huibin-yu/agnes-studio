import Navbar from "@/components/navbar"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "社区画廊 - Agnes Studio",
  description: "浏览 AI 生成的精美图片和视频，发现创意灵感",
  openGraph: {
    title: "社区画廊 - Agnes Studio",
    description: "浏览 AI 生成的精美图片和视频，发现创意灵感",
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
      <main id="main-content">{children}</main>
    </div>
  )
}
