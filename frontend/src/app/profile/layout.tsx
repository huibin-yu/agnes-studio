import Navbar from "@/components/navbar"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "个人中心 - Agnes Studio",
  description: "管理你的账号、查看创作历史、积分余额",
  openGraph: {
    title: "个人中心 - Agnes Studio",
    description: "管理你的账号、查看创作历史、积分余额",
    type: "profile",
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
