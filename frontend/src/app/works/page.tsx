"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Download, ExternalLink, Image as ImageIcon, Loader2, Send, Sparkles, Video } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"

interface ImageWork {
  id: number
  prompt: string
  image_url: string | null
  status: string
  seed: number | null
  size: string
  created_at: string
}

interface VideoWork {
  id: number
  prompt: string
  status: string
  progress: number
  created_at: string
}

export default function WorksPage() {
  const [images, setImages] = useState<ImageWork[]>([])
  const [videos, setVideos] = useState<VideoWork[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [publishingId, setPublishingId] = useState<number | null>(null)
  const [publishedIds, setPublishedIds] = useState<number[]>([])

  useEffect(() => {
    const fetchWorks = async () => {
      setLoading(true)
      setError("")
      try {
        const [imageResp, videoResp] = await Promise.all([
          api.get("/images/my", { params: { per_page: 30 } }),
          api.get("/videos/my", { params: { per_page: 30 } }),
        ])
        setImages(imageResp.data.items || [])
        setVideos(Array.isArray(videoResp.data) ? videoResp.data : videoResp.data.items || [])
      } catch {
        setError("加载作品失败，请稍后重试")
      } finally {
        setLoading(false)
      }
    }
    fetchWorks()
  }, [])

  const publishImage = async (image: ImageWork) => {
    if (!image.image_url) return
    setPublishingId(image.id)
    try {
      await api.post("/gallery/", {
        title: image.prompt.slice(0, 48) || `图片作品 #${image.id}`,
        description: "由 Agnes Studio 生成",
        media_type: "image",
        media_url: image.image_url,
        prompt: image.prompt,
        style: "none",
        tags: [],
        is_public: true,
      })
      setPublishedIds((ids) => [...ids, image.id])
    } catch {
      setError("发布到画廊失败，请稍后重试")
    } finally {
      setPublishingId(null)
    }
  }

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">我的作品</h1>
            <p className="text-muted-foreground mt-1">管理历史生成结果，复用提示词，发布优秀作品</p>
          </div>
          <div className="flex gap-2">
            <Link href="/generate/image">
              <Button>
                <ImageIcon className="w-4 h-4 mr-2" />
                生图
              </Button>
            </Link>
            <Link href="/generate/video">
              <Button variant="outline">
                <Video className="w-4 h-4 mr-2" />
                生视频
              </Button>
            </Link>
          </div>
        </div>

        {error && <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-72 rounded-xl bg-muted animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <section className="space-y-4">
              <h2 className="text-xl font-semibold">图片作品</h2>
              {images.length === 0 ? (
                <EmptyState href="/generate/image" label="开始生成图片" />
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {images.map((image) => (
                    <Card key={image.id} className="overflow-hidden">
                      <div className="aspect-square bg-muted">
                        {image.image_url ? (
                          <img src={image.image_url} alt={image.prompt} className="w-full h-full object-cover" />
                        ) : (
                          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">{image.status}</div>
                        )}
                      </div>
                      <CardContent className="p-4 space-y-3">
                        <p className="text-sm line-clamp-2">{image.prompt}</p>
                        <div className="flex flex-wrap gap-2">
                          <Link href={`/generate/image?prompt=${encodeURIComponent(image.prompt)}&size=${encodeURIComponent(image.size)}`}>
                            <Button size="sm" variant="outline">
                              <Sparkles className="w-4 h-4 mr-1" />
                              复用
                            </Button>
                          </Link>
                          {image.image_url && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => window.open(image.image_url || "", "_blank", "noopener,noreferrer")}
                            >
                              <Download className="w-4 h-4 mr-1" />
                              下载
                            </Button>
                          )}
                          {image.image_url && (
                            <Button
                              size="sm"
                              onClick={() => publishImage(image)}
                              disabled={publishingId === image.id || publishedIds.includes(image.id)}
                            >
                              {publishingId === image.id ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Send className="w-4 h-4 mr-1" />}
                              {publishedIds.includes(image.id) ? "已发布" : "发布"}
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </section>

            <section className="space-y-4">
              <h2 className="text-xl font-semibold">视频作品</h2>
              {videos.length === 0 ? (
                <EmptyState href="/generate/video" label="开始生成视频" />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {videos.map((video) => (
                    <Card key={video.id}>
                      <CardHeader>
                        <CardTitle className="text-base flex items-center gap-2">
                          <Video className="w-4 h-4" />
                          视频 #{video.id}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <p className="text-sm line-clamp-3">{video.prompt}</p>
                        <div className="text-xs text-muted-foreground">状态：{video.status} · 进度：{video.progress || 0}%</div>
                        <Link href={`/generate/video?prompt=${encodeURIComponent(video.prompt)}`}>
                          <Button size="sm" variant="outline">
                            <Sparkles className="w-4 h-4 mr-1" />
                            复用提示词
                          </Button>
                        </Link>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  )
}

function EmptyState({ href, label }: { href: string; label: string }) {
  return (
    <div className="rounded-xl border border-dashed p-10 text-center">
      <p className="text-muted-foreground mb-4">暂无作品</p>
      <Link href={href}>
        <Button>
          <ExternalLink className="w-4 h-4 mr-2" />
          {label}
        </Button>
      </Link>
    </div>
  )
}
