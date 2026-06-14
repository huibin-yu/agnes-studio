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
      setError('Please enter a prompt')
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
      setError(axiosErr.response?.data?.detail || 'Failed to generate image')
    } finally {
      setIsGenerating(false)
    }
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
      setError('Please enter a prompt first')
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
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
            className="w-full"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Image
              </>
            )}
          </Button>

          {/* Error Message */}
          {error && (
            <div className="text-red-500 text-sm">{error}</div>
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
