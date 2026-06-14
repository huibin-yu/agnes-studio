"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { ArrowLeft, Download, Heart, Image as ImageIcon, Loader2, Sparkles, Video } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { api } from "@/lib/api"

interface GalleryItem {
  id: number
  title: string
  description: string
  media_type: "image" | "video"
  media_url: string
  prompt: string
  style: string
  tags: string[]
  likes: number
  views: number
  user: {
    id: number
    username: string
    avatar_url?: string | null
  }
  created_at: string
}

export default function GalleryDetailPage() {
  const params = useParams<{ id: string }>()
  const [item, setItem] = useState<GalleryItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [liking, setLiking] = useState(false)

  useEffect(() => {
    const fetchItem = async () => {
      setLoading(true)
      setError("")
      try {
        const resp = await api.get(`/gallery/${params.id}`)
        setItem(resp.data)
      } catch {
        setError("作品不存在或已被移除")
      } finally {
        setLoading(false)
      }
    }
    fetchItem()
  }, [params.id])

  const likeItem = async () => {
    if (!item) return
    setLiking(true)
    try {
      const resp = await api.post(`/gallery/${item.id}/like`)
      setItem({ ...item, likes: resp.data.likes })
    } catch {
      setError("点赞失败，请登录后重试")
    } finally {
      setLiking(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 px-4">
        <div className="max-w-5xl mx-auto h-96 rounded-xl bg-muted animate-pulse" />
      </div>
    )
  }

  if (error && !item) {
    return (
      <div className="min-h-screen pt-24 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-destructive">{error}</p>
          <Link href="/gallery">
            <Button variant="outline" className="mt-4">返回画廊</Button>
          </Link>
        </div>
      </div>
    )
  }

  if (!item) return null

  const reuseHref = item.media_type === "video"
    ? `/generate/video?prompt=${encodeURIComponent(item.prompt)}`
    : `/generate/image?prompt=${encodeURIComponent(item.prompt)}&style=${encodeURIComponent(item.style || "none")}`

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-6xl mx-auto space-y-6">
        <Link href="/gallery" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回画廊
        </Link>

        {error && <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

        <div className="grid lg:grid-cols-[minmax(0,1fr)_360px] gap-6">
          <Card className="overflow-hidden">
            <CardContent className="p-0 bg-muted">
              {item.media_type === "video" ? (
                <video src={item.media_url} controls className="w-full max-h-[720px]" />
              ) : (
                <img src={item.media_url} alt={item.title} className="w-full max-h-[720px] object-contain" />
              )}
            </CardContent>
          </Card>

          <aside className="space-y-4">
            <div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                {item.media_type === "video" ? <Video className="w-4 h-4" /> : <ImageIcon className="w-4 h-4" />}
                {item.media_type === "video" ? "视频作品" : "图片作品"}
              </div>
              <h1 className="text-2xl font-bold">{item.title}</h1>
              <p className="text-sm text-muted-foreground mt-1">作者：{item.user?.username || "未知用户"}</p>
            </div>

            {item.description && <p className="text-sm text-muted-foreground">{item.description}</p>}

            <div className="rounded-lg border p-4">
              <div className="text-sm font-medium mb-2">完整提示词</div>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{item.prompt}</p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg border p-3">
                <div className="text-muted-foreground">风格</div>
                <div className="font-medium">{item.style || "none"}</div>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-muted-foreground">浏览</div>
                <div className="font-medium">{item.views}</div>
              </div>
            </div>

            {item.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {item.tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">{tag}</span>
                ))}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <Link href={reuseHref}>
                <Button>
                  <Sparkles className="w-4 h-4 mr-2" />
                  用同款生成
                </Button>
              </Link>
              <Button variant="outline" onClick={likeItem} disabled={liking}>
                {liking ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Heart className="w-4 h-4 mr-2" />}
                {item.likes}
              </Button>
              <Button variant="outline" onClick={() => window.open(item.media_url, "_blank", "noopener,noreferrer")}>
                <Download className="w-4 h-4 mr-2" />
                下载
              </Button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
