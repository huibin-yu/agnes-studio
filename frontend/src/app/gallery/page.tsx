"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Search, Heart, Eye, Filter } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { api } from "@/lib/api"

interface GalleryUser {
  id: number
  username: string
}

interface GalleryItem {
  id: number
  title: string
  prompt: string
  media_url: string
  media_type: string
  style: string
  likes: number
  views: number
  user: GalleryUser
}

const STYLES = [
  { value: "all", label: "全部风格" },
  { value: "cinematic", label: "电影质感" },
  { value: "anime", label: "动漫" },
  { value: "realistic", label: "写实" },
  { value: "digital-art", label: "数字艺术" },
  { value: "fantasy", label: "奇幻" },
  { value: "scifi", label: "科幻" },
  { value: "watercolor", label: "水彩" },
]

export default function GalleryPage() {
  const router = useRouter()
  const [items, setItems] = useState<GalleryItem[]>([])
  const [query, setQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")
  const [style, setStyle] = useState("all")
  const [tag, setTag] = useState("")
  const [sort, setSort] = useState("newest")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  const fetchGallery = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const params: Record<string, string | number> = { sort, per_page: 20 }
      if (debouncedQuery) params.query = debouncedQuery
      if (style !== "all") params.style = style
      if (tag) params.tags = tag

      const response = await api.get("/gallery/public", { params })
      setItems(response.data.items || [])
    } catch {
      setError("加载画廊失败，请稍后重试")
      setItems([])
    }
    setLoading(false)
  }, [debouncedQuery, style, tag, sort])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const nextStyle = params.get("style")
    const nextTag = params.get("tag")
    if (nextStyle) setStyle(nextStyle)
    if (nextTag) setTag(nextTag)
  }, [])

  useEffect(() => {
    fetchGallery()
  }, [fetchGallery])

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold">社区画廊</h1>
            <p className="text-muted-foreground mt-1">浏览和发现创作者们的精彩作品</p>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索作品或提示词..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={style} onValueChange={setStyle}>
            <SelectTrigger className="w-[160px]">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="风格" />
            </SelectTrigger>
            <SelectContent>
              {STYLES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            value={tag}
            onChange={(event) => setTag(event.target.value)}
            placeholder="标签筛选"
            className="sm:w-[160px]"
          />
          <Select value={sort} onValueChange={setSort}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">最新发布</SelectItem>
              <SelectItem value="popular">最多点赞</SelectItem>
              <SelectItem value="trending">最多浏览</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Error */}
        {error && (
          <div className="text-center py-8">
            <p className="text-red-500">{error}</p>
            <Button variant="outline" className="mt-2" onClick={fetchGallery}>
              重试
            </Button>
          </div>
        )}

        {/* Gallery Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-64 rounded-xl bg-muted animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {items.map((item) => (
              <Link key={item.id} href={`/gallery/${item.id}`}>
                <Card className="overflow-hidden group hover:shadow-md transition-all h-full">
                  <div className="aspect-square relative overflow-hidden bg-muted">
                    <img
                      src={item.media_url}
                      alt={item.title || "Gallery item"}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                      <p className="text-white text-xs line-clamp-2">{item.prompt}</p>
                    </div>
                  </div>
                  <CardContent className="p-3">
                    <h3 className="text-sm font-medium truncate">{item.title}</h3>
                    <p className="text-xs text-muted-foreground truncate">{item.user?.username}</p>
                    {item.style && (
                      <button
                        type="button"
                        onClick={(event) => {
                          event.preventDefault()
                          setStyle(item.style)
                        }}
                        className="mt-2 rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
                      >
                        {item.style}
                      </button>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3" />
                        {item.likes}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {item.views}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="text-center py-20">
            <p className="text-muted-foreground">
              {debouncedQuery ? `没有找到 "${debouncedQuery}" 相关的作品` : "暂无作品，成为第一个创作者吧！"}
            </p>
            {(style !== "all" || tag) && (
              <Button
                variant="outline"
                className="mt-4 mr-2"
                onClick={() => {
                  setStyle("all")
                  setTag("")
                }}
              >
                清除筛选
              </Button>
            )}
            <Button className="mt-4" onClick={() => router.push("/generate/image")}>
              开始创作
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
