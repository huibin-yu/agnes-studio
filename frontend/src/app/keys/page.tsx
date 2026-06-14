"use client"

import { useState } from "react"
import { Key, Copy, Trash2, Plus, Eye, EyeOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const MOCK_KEYS = [
  { id: 1, name: "默认 Key", key: "agsk_1234567890abcdef", active: true, created: "2026-01-01" },
]

export default function ApiKeysPage() {
  const [keys, setKeys] = useState(MOCK_KEYS)
  const [showNewKey, setShowNewKey] = useState(false)
  const [newKey, setNewKey] = useState("")
  const [keyName, setKeyName] = useState("")

  const handleCreate = () => {
    const randomKey = "agsk_" + Math.random().toString(36).substring(2, 34)
    const newKeyItem = {
      id: Date.now(),
      name: keyName || "未命名 Key",
      key: randomKey,
      active: true,
      created: new Date().toISOString().split("T")[0],
    }
    setKeys([newKeyItem, ...keys])
    setNewKey(randomKey)
    setShowNewKey(true)
    setKeyName("")
  }

  const handleDelete = (id: number) => {
    setKeys(keys.filter((k) => k.id !== id))
  }

  const copyKey = (key: string) => {
    navigator.clipboard.writeText(key)
  }

  return (
    <div className="min-h-screen pt-20 pb-10 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">API Key 管理</h1>
        <p className="text-muted-foreground mb-8">管理你的 API 访问密钥</p>

        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Key className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1">
                <p className="font-medium">API 使用说明</p>
                <p className="text-sm text-muted-foreground">
                  使用你的 Key 调用 Agnes Studio API，每个请求需要在 Header 中携带 Authorization: Bearer YOUR_KEY
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Create Key */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              创建新 Key
              <Button onClick={() => setShowNewKey(!showNewKey)} size="sm">
                <Plus className="w-4 h-4 mr-1" />
                {showNewKey ? "取消" : "创建"}
              </Button>
            </CardTitle>
          </CardHeader>
          {showNewKey && (
            <CardContent>
              <div className="space-y-3">
                <Input
                  placeholder="Key 名称"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                />
                <Button onClick={handleCreate} className="w-full">
                  创建 Key
                </Button>
                {newKey && (
                  <div className="p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                    <p className="text-sm text-yellow-800 mb-1">⚠️ 请妥善保存这个 Key，以后无法查看</p>
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-black/5 px-2 py-1 rounded flex-1 overflow-hidden text-ellipsis whitespace-nowrap">
                        {newKey}
                      </code>
                      <Button size="sm" variant="outline" onClick={() => copyKey(newKey)}>
                        <Copy className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Keys List */}
        <div className="space-y-3">
          {keys.map((key) => (
            <Card key={key.id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${key.active ? "bg-green-500" : "bg-red-500"}`} />
                    <div>
                      <p className="font-medium">{key.name}</p>
                      <div className="flex items-center gap-2">
                        <code className="text-xs bg-muted px-2 py-0.5 rounded">
                          {key.key.slice(0, 10)}...
                        </code>
                        <span className="text-xs text-muted-foreground">{key.created}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="ghost" onClick={() => copyKey(key.key)}>
                      <Copy className="w-3.5 h-3.5" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => handleDelete(key.id)}>
                      <Trash2 className="w-3.5 h-3.5 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
