import Navbar from "@/components/navbar"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "登录 - Agnes Studio",
  description: "登录你的 Agnes Studio 账号，开始 AI 创作之旅",
  openGraph: {
    title: "登录 - Agnes Studio",
    description: "登录你的 Agnes Studio 账号，开始 AI 创作之旅",
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
