"use client"

import { useEffect, useState, useCallback } from "react"
import { Key, Copy, Trash2, Plus, AlertCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"

interface ApiKeyItem {
  id: number
  name: string
  key_prefix: string
  is_active: boolean
  rate_limit: number
  daily_limit: number
  expires_at: string | null
  created_at: string
}

interface CreatedKey extends ApiKeyItem {
  key: string
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [showCreate, setShowCreate] = useState(false)
  const [keyName, setKeyName] = useState("")
  const [creating, setCreating] = useState(false)
  const [createdKey, setCreatedKey] = useState<CreatedKey | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [copied, setCopied] = useState(false)

  const fetchKeys = useCallback(async () => {
    try {
      setLoading(true)
      setError("")
      const resp = await api.get("/keys")
      setKeys(resp.data.items || [])
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || "加载 API Key 列表失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchKeys()
  }, [fetchKeys])

  const handleCreate = async () => {
    if (!keyName.trim()) return
    try {
      setCreating(true)
      setError("")
      const resp = await api.post("/keys", { name: keyName.trim() })
      setCreatedKey(resp.data)
      setKeyName("")
      setShowCreate(false)
      fetchKeys()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || "创建 API Key 失败")
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm("确定要删除这个 API Key 吗？删除后不可恢复。")) return
    try {
      setDeletingId(id)
      await api.delete(`/keys/${id}`)
      setKeys(keys.filter((k) => k.id !== id))
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || "删除 API Key 失败")
    } finally {
      setDeletingId(null)
    }
  }

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    })
  }

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">API Key 管理</h1>
        <p className="text-muted-foreground mb-8">管理你的 API 访问密钥</p>

        {/* Usage Guide */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Key className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1">
                <p className="font-medium">API 使用说明</p>
                <p className="text-sm text-muted-foreground">
                  使用你的 Key 调用 Agnes Studio API，每个请求需要在 Header 中携带
                  <code className="mx-1 px-1.5 py-0.5 rounded bg-muted text-xs">Authorization: Bearer YOUR_KEY</code>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
            <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setError("")}>
              关闭
            </Button>
          </div>
        )}

        {/* Created Key Banner (shown only once after creation) */}
        {createdKey && (
          <div className="mb-6 rounded-lg border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-700 dark:bg-yellow-950">
            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
              ⚠️ 请妥善保存这个 Key，以后无法再次查看
            </p>
            <div className="flex items-center gap-2">
              <code className="text-xs bg-black/5 dark:bg-white/10 px-3 py-1.5 rounded flex-1 overflow-hidden text-ellipsis whitespace-nowrap font-mono">
                {createdKey.key}
              </code>
              <Button size="sm" variant="outline" onClick={() => copyKey(createdKey.key)}>
                {copied ? "已复制" : <Copy className="w-3.5 h-3.5" />}
              </Button>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 text-xs"
              onClick={() => setCreatedKey(null)}
            >
              我已保存，关闭提示
            </Button>
          </div>
        )}

        {/* Create Key */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-base">
              创建新 Key
              <Button onClick={() => { setShowCreate(!showCreate); setCreatedKey(null) }} size="sm" variant={showCreate ? "outline" : "default"}>
                <Plus className="w-4 h-4 mr-1" />
                {showCreate ? "取消" : "创建"}
              </Button>
            </CardTitle>
          </CardHeader>
          {showCreate && (
            <CardContent>
              <div className="flex gap-3">
                <Input
                  placeholder="Key 名称（如：我的项目）"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  disabled={creating}
                />
                <Button onClick={handleCreate} disabled={creating || !keyName.trim()}>
                  {creating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    "确认创建"
                  )}
                </Button>
              </div>
            </CardContent>
          )}
        </Card>

        {/* Keys List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : keys.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              <Key className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>还没有 API Key</p>
              <p className="text-sm mt-1">点击上方「创建」按钮生成你的第一个 Key</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {keys.map((apiKey) => (
              <Card key={apiKey.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${apiKey.is_active ? "bg-green-500" : "bg-red-500"}`} />
                      <div>
                        <p className="font-medium">{apiKey.name}</p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                          <code className="bg-muted px-2 py-0.5 rounded font-mono">
                            {apiKey.key_prefix}...
                          </code>
                          <span>创建于 {formatDate(apiKey.created_at)}</span>
                          <span>限速 {apiKey.rate_limit}/分钟</span>
                          {apiKey.expires_at && (
                            <span>过期于 {formatDate(apiKey.expires_at)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDelete(apiKey.id)}
                      disabled={deletingId === apiKey.id}
                    >
                      {deletingId === apiKey.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5 text-destructive" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
