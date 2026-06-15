/**
 * Image Generation Page
 * Based on official Agnes AI documentation
 * https://agnes-ai.com/doc/overview
 */
'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Image as ImageIcon, Sparkles, Download, Share2, Wand2 } from 'lucide-react'
import { useGenerationStore } from '@/stores/generation'
import { api } from '@/lib/api'
import { IMAGE_MODELS, IMAGE_SIZES, IMAGE_STYLES } from '@/lib/image-constants'
import { IMAGE_PROMPT_TEMPLATES, enhanceImagePrompt } from '@/lib/prompt-tools'

interface ImageResult {
  id: number
  prompt: string
  image_url: string
  status: string
  seed: number | null
  size: string
  style: string
  created_at: string
}

const IMAGE_USE_CASES = [
  {
    id: 'social-cover',
    name: '社媒封面',
    description: '方图，主体清晰，适合小红书/公众号封面',
    model: 'agnes-image-2.1-flash',
    size: '1024x1024',
    style: 'realistic',
  },
  {
    id: 'product-main',
    name: '产品主图',
    description: '横版商品展示，适合电商与落地页',
    model: 'agnes-image-2.1-flash',
    size: '1024x768',
    style: 'photographic',
  },
  {
    id: 'poster',
    name: '竖版海报',
    description: '竖版构图，适合活动、课程、营销视觉',
    model: 'agnes-image-2.1-flash',
    size: '1024x1816',
    style: 'digital-art',
  },
]

function estimateImageCredits(size: string, model: string) {
  const sizeMultiplier = size.startsWith('4096') ? 8 : size.startsWith('2048') ? 3 : 1
  const modelMultiplier = model.includes('2.1') ? 1.2 : 1
  return Math.ceil(10 * sizeMultiplier * modelMultiplier)
}

export default function ImageGenerationPage() {
  const [prompt, setPrompt] = useState('')
  const [selectedModel, setSelectedModel] = useState('agnes-image-2.1-flash')
  const [selectedSize, setSelectedSize] = useState('1024x768')
  const [selectedStyle, setSelectedStyle] = useState('none')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<ImageResult | null>(null)
  const [error, setError] = useState('')
  
  const { addGeneration } = useGenerationStore()
  const estimatedCredits = estimateImageCredits(selectedSize, selectedModel)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const nextPrompt = params.get('prompt')
    const nextStyle = params.get('style')
    const nextSize = params.get('size')
    if (nextPrompt) setPrompt(nextPrompt)
    if (nextStyle) setSelectedStyle(nextStyle)
    if (nextSize) setSelectedSize(nextSize)
  }, [])

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('请输入提示词')
      return
    }

    setIsGenerating(true)
    setError('')
    setResult(null)

    try {
      const response = await api.post('/images/generate', {
        prompt: prompt.trim(),
        model: selectedModel,
        size: selectedSize,
        style: selectedStyle,
        negative_prompt: negativePrompt || undefined,
      })

      setResult(response.data)
      addGeneration({
        type: 'image',
        prompt: prompt.trim(),
        imageUrl: response.data.image_url,
        size: selectedSize,
        style: selectedStyle,
        createdAt: new Date().toISOString(),
      })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || '图片生成失败，请重试')
    } finally {
      setIsGenerating(false)
    }
  }

  const applyUseCase = (useCaseId: string) => {
    const useCase = IMAGE_USE_CASES.find((item) => item.id === useCaseId)
    if (!useCase) return
    setSelectedModel(useCase.model)
    setSelectedSize(useCase.size)
    setSelectedStyle(useCase.style)
  }

  const applyTemplate = (templateId: string) => {
    const template = IMAGE_PROMPT_TEMPLATES.find((item) => item.id === templateId)
    if (!template) return
    setPrompt(template.prompt)
    if (template.style) setSelectedStyle(template.style)
    if (template.size) setSelectedSize(template.size)
  }

  const handleEnhancePrompt = () => {
    if (!prompt.trim()) {
      setError('请先输入提示词')
      return
    }
    setPrompt(enhanceImagePrompt(prompt, selectedStyle))
    setError('')
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ImageIcon className="h-6 w-6" />
            AI Image Generation
          </CardTitle>
          <CardDescription>
            Powered by Agnes AI • {selectedModel}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">参数预设</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
              {IMAGE_USE_CASES.map((useCase) => (
                <button
                  key={useCase.id}
                  type="button"
                  onClick={() => applyUseCase(useCase.id)}
                  className="text-left rounded-lg border p-3 hover:border-primary hover:bg-muted/50 transition-colors"
                >
                  <div className="text-sm font-medium">{useCase.name}</div>
                  <div className="text-xs text-muted-foreground mt-1">{useCase.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Prompt Templates */}
          <div>
            <label className="text-sm font-medium">创作模板</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
              {IMAGE_PROMPT_TEMPLATES.map((template) => (
                <button
                  key={template.id}
                  type="button"
                  onClick={() => applyTemplate(template.id)}
                  className="text-left rounded-lg border p-3 hover:border-primary hover:bg-muted/50 transition-colors"
                >
                  <div className="text-sm font-medium">{template.name}</div>
                  <div className="text-xs text-muted-foreground mt-1">{template.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Prompt Input */}
          <div>
            <label className="text-sm font-medium">Prompt</label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A majestic dragon flying over a medieval castle at sunset"
              rows={4}
              className="mt-1"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleEnhancePrompt}
              className="mt-2"
            >
              <Wand2 className="h-4 w-4 mr-2" />
              增强提示词
            </Button>
          </div>

          {/* Negative Prompt */}
          <div>
            <label className="text-sm font-medium">Negative Prompt (optional)</label>
            <Textarea
              value={negativePrompt}
              onChange={(e) => setNegativePrompt(e.target.value)}
              placeholder="blurry, low quality, distorted"
              rows={2}
              className="mt-1"
            />
          </div>

          {/* Model Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Model</label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {IMAGE_MODELS.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      {model.name} {model.recommended && '(Recommended)'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Size Selection */}
            <div>
              <label className="text-sm font-medium">Size</label>
              <Select value={selectedSize} onValueChange={setSelectedSize}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {IMAGE_SIZES.map((size) => (
                    <SelectItem key={size.id} value={size.id}>
                      {size.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Style Selection */}
          <div>
            <label className="text-sm font-medium">Style (optional)</label>
            <Select value={selectedStyle} onValueChange={setSelectedStyle}>
              <SelectTrigger className="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {IMAGE_STYLES.map((style) => (
                  <SelectItem key={style.id} value={style.id}>
                    {style.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Generate Button */}
          <div className="rounded-lg border bg-muted/30 p-3 text-sm text-muted-foreground">
            预计消耗：<span className="font-medium text-foreground">{estimatedCredits}</span> 积分 · {selectedSize} · {selectedModel}
          </div>

          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
            className="w-full"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                生成图片
              </>
            )}
          </Button>

          {/* Error Message */}
          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <div>{error}</div>
              {prompt.trim() && (
                <Button type="button" size="sm" variant="outline" className="mt-2" onClick={handleGenerate} disabled={isGenerating}>
                  一键重试
                </Button>
              )}
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="mt-4">
              <img
                src={result.image_url}
                alt={prompt}
                className="w-full rounded-lg"
              />
              <div className="flex gap-2 mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const a = document.createElement('a')
                    a.href = result.image_url
                    a.download = `agnes-${result.id}.png`
                    a.target = '_blank'
                    a.rel = 'noopener noreferrer'
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                  }}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (navigator.share) {
                      navigator.share({
                        title: 'AI Generated Image',
                        text: prompt,
                        url: result.image_url,
                      })
                    } else {
                      navigator.clipboard.writeText(result.image_url)
                    }
                  }}
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Share
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
