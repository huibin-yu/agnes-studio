"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  Download,
  ExternalLink,
  Filter,
  Image as ImageIcon,
  Loader2,
  Play,
  Search,
  Send,
  Sparkles,
  Trash2,
  Video,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"

interface ImageWork {
  id: number
  prompt: string
  image_url: string | null
  status: string
  seed: number | null
  size: string
  style?: string | null
  created_at: string
}

interface VideoWork {
  id: number
  prompt: string
  status: string
  progress: number
  video_url?: string | null
  num_frames?: number | null
  frame_rate?: number | null
  created_at: string
}

interface PublishDraft {
  sourceType: "image" | "video"
  sourceId: number
  title: string
  description: string
  tags: string
  isPublic: boolean
  mediaType: "image" | "video"
  mediaUrl: string
  prompt: string
  style: string
}

type TypeFilter = "all" | "image" | "video"
type StatusFilter = "all" | "completed" | "running" | "failed"

export default function WorksPage() {
  const [images, setImages] = useState<ImageWork[]>([])
  const [videos, setVideos] = useState<VideoWork[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [query, setQuery] = useState("")
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [deletingKey, setDeletingKey] = useState<string | null>(null)
  const [publishing, setPublishing] = useState(false)
  const [publishedKeys, setPublishedKeys] = useState<string[]>([])
  const [draft, setDraft] = useState<PublishDraft | null>(null)

  const fetchWorks = async () => {
    setLoading(true)
    setError("")
    try {
      const [imageResp, videoResp] = await Promise.all([
        api.get("/images/my", { params: { per_page: 60 } }),
        api.get("/videos/my", { params: { per_page: 60 } }),
      ])
      setImages(imageResp.data.items || [])
      setVideos(Array.isArray(videoResp.data) ? videoResp.data : videoResp.data.items || [])
    } catch {
      setError("加载作品失败，请稍后重试")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorks()
  }, [])

  const normalizedQuery = query.trim().toLowerCase()

  const filteredImages = useMemo(() => {
    if (typeFilter === "video") return []
    return images.filter((image) => {
      const matchesQuery = !normalizedQuery || image.prompt.toLowerCase().includes(normalizedQuery)
      const matchesStatus = statusFilter === "all" || image.status === statusFilter
      return matchesQuery && matchesStatus
    })
  }, [images, normalizedQuery, statusFilter, typeFilter])

  const filteredVideos = useMemo(() => {
    if (typeFilter === "image") return []
    return videos.filter((video) => {
      const matchesQuery = !normalizedQuery || video.prompt.toLowerCase().includes(normalizedQuery)
      const statusGroup = video.status === "completed" ? "completed" : video.status === "failed" ? "failed" : "running"
      const matchesStatus = statusFilter === "all" || statusFilter === statusGroup
      return matchesQuery && matchesStatus
    })
  }, [normalizedQuery, statusFilter, typeFilter, videos])

  const completedCount = images.filter((item) => item.status === "completed").length +
    videos.filter((item) => item.status === "completed").length
  const runningCount = videos.filter((item) => item.status !== "completed" && item.status !== "failed").length

  const deleteWork = async (type: "image" | "video", id: number) => {
    const confirmed = window.confirm("确定删除这个作品吗？此操作无法撤销。")
    if (!confirmed) return

    const key = `${type}-${id}`
    setDeletingKey(key)
    setError("")
    try {
      await api.delete(type === "image" ? `/images/${id}` : `/videos/${id}`)
      if (type === "image") {
        setImages((items) => items.filter((item) => item.id !== id))
      } else {
        setVideos((items) => items.filter((item) => item.id !== id))
      }
    } catch {
      setError("删除失败，请稍后重试")
    } finally {
      setDeletingKey(null)
    }
  }

  const openPublishDialog = (work: ImageWork | VideoWork, type: "image" | "video") => {
    const mediaUrl = type === "image" ? (work as ImageWork).image_url : (work as VideoWork).video_url
    if (!mediaUrl) {
      setError(type === "image" ? "图片尚未生成完成，不能发布" : "视频尚未生成完成，不能发布")
      return
    }

    setDraft({
      sourceType: type,
      sourceId: work.id,
      title: work.prompt.slice(0, 48) || `${type === "image" ? "图片" : "视频"}作品 #${work.id}`,
      description: "由 Agnes Studio 生成",
      tags: type === "image" ? ((work as ImageWork).style || "") : "video",
      isPublic: true,
      mediaType: type,
      mediaUrl,
      prompt: work.prompt,
      style: type === "image" ? ((work as ImageWork).style || "none") : "video",
    })
  }

  const publishWork = async () => {
    if (!draft) return
    setPublishing(true)
    setError("")
    try {
      const tags = draft.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean)
        .slice(0, 20)

      await api.post("/gallery/", {
        title: draft.title.trim() || `${draft.mediaType === "image" ? "图片" : "视频"}作品 #${draft.sourceId}`,
        description: draft.description.trim(),
        media_type: draft.mediaType,
        media_url: draft.mediaUrl,
        prompt: draft.prompt,
        style: draft.style,
        tags,
        is_public: draft.isPublic,
      })

      setPublishedKeys((keys) => [...keys, `${draft.sourceType}-${draft.sourceId}`])
      setDraft(null)
    } catch {
      setError("发布到画廊失败，请稍后重试")
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold">我的作品</h1>
            <p className="text-muted-foreground mt-1">筛选、复用、下载、删除和发布历史生成结果</p>
          </div>
          <div className="flex flex-wrap gap-2">
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

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <MetricCard label="全部作品" value={images.length + videos.length} />
          <MetricCard label="已完成" value={completedCount} />
          <MetricCard label="生成中" value={runningCount} />
        </div>

        <div className="flex flex-col lg:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索提示词..."
              className="pl-10"
            />
          </div>
          <Select value={typeFilter} onValueChange={(value) => setTypeFilter(value as TypeFilter)}>
            <SelectTrigger className="lg:w-[160px]">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value="image">图片</SelectItem>
              <SelectItem value="video">视频</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as StatusFilter)}>
            <SelectTrigger className="lg:w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="completed">已完成</SelectItem>
              <SelectItem value="running">生成中</SelectItem>
              <SelectItem value="failed">失败</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {error && <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-80 rounded-xl bg-muted animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-8">
            {typeFilter !== "video" && (
              <section className="space-y-4">
                <SectionHeader title="图片作品" count={filteredImages.length} />
                {filteredImages.length === 0 ? (
                  <EmptyState href="/generate/image" label="开始生成图片" />
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredImages.map((image) => (
                      <Card key={image.id} className="overflow-hidden">
                        <div className="aspect-square bg-muted">
                          {image.image_url ? (
                            <img src={image.image_url} alt={image.prompt} className="w-full h-full object-cover" />
                          ) : (
                            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">{image.status}</div>
                          )}
                        </div>
                        <CardContent className="p-4 space-y-3">
                          <div>
                            <p className="text-sm line-clamp-2">{image.prompt}</p>
                            <p className="text-xs text-muted-foreground mt-1">{image.size} · {image.style || "none"} · {formatDate(image.created_at)}</p>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Link href={`/generate/image?prompt=${encodeURIComponent(image.prompt)}&size=${encodeURIComponent(image.size)}&style=${encodeURIComponent(image.style || "none")}`}>
                              <Button size="sm" variant="outline">
                                <Sparkles className="w-4 h-4 mr-1" />
                                复用
                              </Button>
                            </Link>
                            {image.image_url && (
                              <Button size="sm" variant="outline" onClick={() => window.open(image.image_url || "", "_blank", "noopener,noreferrer")}>
                                <Download className="w-4 h-4 mr-1" />
                                下载
                              </Button>
                            )}
                            {image.image_url && (
                              <Button
                                size="sm"
                                onClick={() => openPublishDialog(image, "image")}
                                disabled={publishedKeys.includes(`image-${image.id}`)}
                              >
                                <Send className="w-4 h-4 mr-1" />
                                {publishedKeys.includes(`image-${image.id}`) ? "已发布" : "发布"}
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => deleteWork("image", image.id)}
                              disabled={deletingKey === `image-${image.id}`}
                            >
                              {deletingKey === `image-${image.id}` ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Trash2 className="w-4 h-4 mr-1" />}
                              删除
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </section>
            )}

            {typeFilter !== "image" && (
              <section className="space-y-4">
                <SectionHeader title="视频作品" count={filteredVideos.length} />
                {filteredVideos.length === 0 ? (
                  <EmptyState href="/generate/video" label="开始生成视频" />
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredVideos.map((video) => (
                      <Card key={video.id} className="overflow-hidden">
                        {video.video_url ? (
                          <video src={video.video_url} controls className="w-full aspect-video bg-black object-contain" />
                        ) : (
                          <div className="aspect-video bg-muted flex flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
                            <Play className="w-6 h-6" />
                            {video.status} · {video.progress || 0}%
                          </div>
                        )}
                        <CardContent className="p-4 space-y-3">
                          <div>
                            <p className="text-sm line-clamp-3">{video.prompt}</p>
                            <p className="text-xs text-muted-foreground mt-1">{formatVideoMeta(video)} · {formatDate(video.created_at)}</p>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Link href={`/generate/video?prompt=${encodeURIComponent(video.prompt)}`}>
                              <Button size="sm" variant="outline">
                                <Sparkles className="w-4 h-4 mr-1" />
                                复用
                              </Button>
                            </Link>
                            {video.video_url && (
                              <Button size="sm" variant="outline" onClick={() => window.open(video.video_url || "", "_blank", "noopener,noreferrer")}>
                                <Download className="w-4 h-4 mr-1" />
                                下载
                              </Button>
                            )}
                            {video.video_url && (
                              <Button
                                size="sm"
                                onClick={() => openPublishDialog(video, "video")}
                                disabled={publishedKeys.includes(`video-${video.id}`)}
                              >
                                <Send className="w-4 h-4 mr-1" />
                                {publishedKeys.includes(`video-${video.id}`) ? "已发布" : "发布"}
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => deleteWork("video", video.id)}
                              disabled={deletingKey === `video-${video.id}`}
                            >
                              {deletingKey === `video-${video.id}` ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Trash2 className="w-4 h-4 mr-1" />}
                              删除
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </section>
            )}
          </div>
        )}
      </div>

      <Dialog open={Boolean(draft)} onOpenChange={(open) => !open && setDraft(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>发布到画廊</DialogTitle>
            <DialogDescription>发布前可以编辑标题、说明、标签和公开状态。</DialogDescription>
          </DialogHeader>
          {draft && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">标题</label>
                <Input value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} className="mt-1" />
              </div>
              <div>
                <label className="text-sm font-medium">说明</label>
                <Textarea
                  value={draft.description}
                  onChange={(event) => setDraft({ ...draft, description: event.target.value })}
                  rows={3}
                  className="mt-1 min-h-[90px]"
                />
              </div>
              <div>
                <label className="text-sm font-medium">标签</label>
                <Input
                  value={draft.tags}
                  onChange={(event) => setDraft({ ...draft, tags: event.target.value })}
                  placeholder="用英文逗号分隔，例如 poster, product"
                  className="mt-1"
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={draft.isPublic}
                  onChange={(event) => setDraft({ ...draft, isPublic: event.target.checked })}
                  className="h-4 w-4 rounded border"
                />
                公开展示在社区画廊
              </label>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDraft(null)} disabled={publishing}>取消</Button>
            <Button onClick={publishWork} disabled={publishing || !draft?.title.trim()}>
              {publishing && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              发布
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className="text-2xl font-semibold mt-1">{value}</div>
      </CardContent>
    </Card>
  )
}

function SectionHeader({ title, count }: { title: string; count: number }) {
  return (
    <div className="flex items-center justify-between">
      <h2 className="text-xl font-semibold">{title}</h2>
      <span className="text-sm text-muted-foreground">{count} 个</span>
    </div>
  )
}

function EmptyState({ href, label }: { href: string; label: string }) {
  return (
    <div className="rounded-xl border border-dashed p-10 text-center">
      <p className="text-muted-foreground mb-4">暂无匹配作品</p>
      <Link href={href}>
        <Button>
          <ExternalLink className="w-4 h-4 mr-2" />
          {label}
        </Button>
      </Link>
    </div>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value))
}

function formatVideoMeta(video: VideoWork) {
  const seconds = video.num_frames && video.frame_rate ? `${(video.num_frames / video.frame_rate).toFixed(1)} 秒` : "视频"
  return `${video.status} · ${video.progress || 0}% · ${seconds}`
}
