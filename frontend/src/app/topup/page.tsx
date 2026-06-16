"use client"

import { Coins, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useIsAuthenticated } from "@/stores/auth"
import Link from "next/link"

const PACKAGES = [
  { credits: 10, price: 0, featured: false, label: "免费体验" },
  { credits: 50, price: 9.9, featured: false, label: "入门套餐" },
  { credits: 200, price: 29.9, featured: true, label: "专业套餐" },
  { credits: 1000, price: 99.9, featured: false, label: "企业套餐" },
]

export default function TopUpPage() {
  const isAuthenticated = useIsAuthenticated()

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">充值积分</h1>
        <p className="text-muted-foreground mb-8">购买积分，畅享 AI 创作</p>

        <div className="grid sm:grid-cols-2 gap-4 mb-8">
          {PACKAGES.map((pkg, i) => (
            <Card key={i} className={`relative ${pkg.featured ? "border-primary shadow-lg" : ""}`}>
              {pkg.featured && (
                <div className="absolute -top-3 right-4 px-2 py-0.5 rounded-full bg-primary text-primary-foreground text-xs font-medium">
                  推荐
                </div>
              )}
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Coins className="w-5 h-5 text-primary" />
                  <CardTitle>{pkg.credits} 积分</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold mb-4">
                  {pkg.price === 0 ? "免费" : `¥${pkg.price}`}
                </p>
                <ul className="space-y-1 text-sm text-muted-foreground mb-4">
                  <li className="flex items-center gap-2">
                    <Check className="w-3.5 h-3.5 text-green-500" />
                    {pkg.credits} 积分有效期 1 年
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-3.5 h-3.5 text-green-500" />
                    支持生图和生视频
                  </li>
                </ul>
                {pkg.price === 0 ? (
                  <Link href={isAuthenticated ? "#" : "/login"} className="block">
                    <Button className="w-full" variant="default">
                      {isAuthenticated ? "已领取" : "注册领取"}
                    </Button>
                  </Link>
                ) : (
                  <Button className="w-full" variant={pkg.featured ? "glow" : "default"} disabled>
                    即将上线
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="p-4 rounded-lg bg-muted/50 text-sm text-muted-foreground">
          <p>💡 积分说明：</p>
          <ul className="list-disc list-inside mt-1 space-y-1">
            <li>生图消耗 1 积分/张</li>
            <li>生视频消耗 2 积分/秒</li>
            <li>注册即赠送 10 积分</li>
            <li>邀请好友各得 5 积分</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
