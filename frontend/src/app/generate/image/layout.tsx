import Navbar from "@/components/navbar"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "AI 图片生成 - Agnes Studio",
  description: "使用 AI 生成精美图片，支持 14+ 种艺术风格、多种尺寸、参数调节",
  openGraph: {
    title: "AI 图片生成 - Agnes Studio",
    description: "使用 AI 生成精美图片，支持 14+ 种艺术风格、多种尺寸、参数调节",
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
