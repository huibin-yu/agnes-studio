"use client"

import { useState, useEffect } from "react"
import { Camera, LogOut, Coins, Image as ImageIcon, Video, Shield, Key, FolderOpen, Gift, Copy, Check } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import { useAuthStore } from "@/stores/auth"

interface UserStats {
  total_images: number
  total_videos: number
}

export default function ProfilePage() {
  const { user, logout } = useAuthStore()
  const [stats, setStats] = useState<UserStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const resp = await api.get("/users/stats")
        setStats(resp.data)
      } catch {
        // ignore
      }
      setLoading(false)
    }
    fetchStats()
  }, [])

  const referralCode = user?.referral_code
  const referralLink = referralCode
    ? `${typeof window !== "undefined" ? window.location.origin : ""}/login?ref=${referralCode}`
    : ""

  const copyReferral = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // ignore
    }
  }

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Profile Header */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-white text-2xl font-bold">
                {user?.username?.[0]?.toUpperCase() ?? "U"}
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold">{user?.username}</h1>
                <p className="text-muted-foreground">{user?.email}</p>
              </div>
              <Button variant="outline" onClick={() => logout()}>
                <LogOut className="w-4 h-4 mr-2" />
                退出登录
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <Coins className="w-6 h-6 mx-auto text-primary mb-2" />
              <p className="text-2xl font-bold">{loading ? "-" : user?.credits ?? 0}</p>
              <p className="text-xs text-muted-foreground">积分余额</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <ImageIcon className="w-6 h-6 mx-auto text-violet-500 mb-2" />
              <p className="text-2xl font-bold">{loading ? "-" : stats?.total_images ?? 0}</p>
              <p className="text-xs text-muted-foreground">图片生成</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Video className="w-6 h-6 mx-auto text-pink-500 mb-2" />
              <p className="text-2xl font-bold">{loading ? "-" : stats?.total_videos ?? 0}</p>
              <p className="text-xs text-muted-foreground">视频生成</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Camera className="w-6 h-6 mx-auto text-emerald-500 mb-2" />
              <p className="text-2xl font-bold">{loading ? "-" : (stats?.total_images ?? 0) + (stats?.total_videos ?? 0)}</p>
              <p className="text-xs text-muted-foreground">总创作</p>
            </CardContent>
          </Card>
        </div>

        {/* Referral System */}
        {referralCode && (
          <Card className="border-primary/30 bg-gradient-to-br from-violet-500/5 to-pink-500/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gift className="w-5 h-5 text-primary" />
                邀请好友，各得 5 积分
              </CardTitle>
              <CardDescription>
                分享你的专属推荐码或链接，朋友注册成功后双方各获得 5 积分奖励
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground mb-1">推荐码</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 px-3 py-2 rounded-lg bg-muted font-mono text-sm">
                    {referralCode}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyReferral(referralCode)}
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    {copied ? "已复制" : "复制"}
                  </Button>
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">推荐链接</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 px-3 py-2 rounded-lg bg-muted text-sm truncate">
                    {referralLink}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyReferral(referralLink)}
                  >
                    <Copy className="w-4 h-4" />
                    复制链接
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-4">
          <Link href="/generate/image">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="w-5 h-5 text-violet-500" />
                  生成图片
                </CardTitle>
                <CardDescription>使用 AI 生成精美图片</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/generate/video">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Video className="w-5 h-5 text-pink-500" />
                  生成视频
                </CardTitle>
                <CardDescription>输入描述生成短视频</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/keys">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="w-5 h-5 text-emerald-500" />
                  API Key
                </CardTitle>
                <CardDescription>管理你的 API 访问密钥</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/works">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-sky-500" />
                  我的作品
                </CardTitle>
                <CardDescription>查看历史作品并发布到画廊</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          <Link href="/topup">
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-amber-500" />
                  充值积分
                </CardTitle>
                <CardDescription>购买更多积分继续使用</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>
      </div>
    </div>
  )
}
