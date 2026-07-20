/**
 * Video Generation Page
 * Based on official Agnes AI documentation
 * https://agnes-ai.com/doc/agnes-video-v20
 */
'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Loader2, Video, Sparkles, Download, Share2, Wand2 } from 'lucide-react'
import { useGenerationStore } from '@/stores/generation'
import { api } from '@/lib/api'
import { VIDEO_MODEL, VALID_FRAME_COUNTS, VALID_FRAME_RATES, VIDEO_DURATIONS } from '@/lib/video-constants'
import { VIDEO_PROMPT_TEMPLATES, enhanceVideoPrompt } from '@/lib/prompt-tools'
import { showToast } from '@/components/ui/toast'

const MAX_POLL_ATTEMPTS = 120 // 10 minutes at 5s intervals

const VIDEO_USE_CASES = [
  {
    id: 'short-opening',
    name: '短视频开场',
    description: '5 秒以内，适合社媒开头和封面动态',
    frames: 81,
    fps: 24,
  },
  {
    id: 'product-loop',
    name: '产品展示',
    description: '5 秒商品转场和材质特写',
    frames: 121,
    fps: 24,
  },
  {
    id: 'story-shot',
    name: '剧情镜头',
    description: '10 秒叙事镜头，适合短片片段',
    frames: 241,
    fps: 24,
  },
]

function estimateVideoCredits(frames: number, fps: number) {
  const duration = frames / fps
  return Math.ceil(duration * 2)
}

export default function VideoGenerationPage() {
  const [prompt, setPrompt] = useState('')
  const [numFrames, setNumFrames] = useState(121)
  const [frameRate, setFrameRate] = useState(24)
  const [isGenerating, setIsGenerating] = useState(false)
  const [videoId, setVideoId] = useState<number | null>(null)
  const [videoStatus, setVideoStatus] = useState<string>('')
  const [progress, setProgress] = useState(0)
  const [videoUrl, setVideoUrl] = useState<string>('')
  const [error, setError] = useState('')
  const pollCountRef = useRef(0)
  const lastPollTimeRef = useRef(0)

  const { addGeneration } = useGenerationStore()
  const estimatedCredits = estimateVideoCredits(numFrames, frameRate)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const nextPrompt = params.get('prompt')
    if (nextPrompt) setPrompt(nextPrompt)
  }, [])

  // Poll video status with minimum interval protection
  const pollVideoStatus = useCallback(async () => {
    if (!videoId) return

    // Ensure minimum 3 seconds between polls
    const now = Date.now()
    const timeSinceLastPoll = now - lastPollTimeRef.current
    if (timeSinceLastPoll < 3000) {
      return
    }
    lastPollTimeRef.current = now

    pollCountRef.current += 1
    if (pollCountRef.current > MAX_POLL_ATTEMPTS) {
      setError('视频生成超时，请稍后在个人中心查看结果')
      setVideoStatus('timeout')
      return
    }

    try {
      const response = await api.get(`/videos/${videoId}/poll`)
      const { status, progress: prog, video_url, error_message } = response.data

      setVideoStatus(status)
      setProgress(prog || 0)

      if (status === 'completed' && video_url) {
        setVideoUrl(video_url)
        addGeneration({
          type: 'video',
          prompt: prompt,
          videoUrl: video_url,
          createdAt: new Date().toISOString(),
        })
      } else if (status === 'failed') {
        setError(error_message || '视频生成失败，请重试')
      }
    } catch {
      // Don't set error on transient poll failures
    }
  }, [videoId, prompt, addGeneration])

  // Auto-poll when video is generating
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (videoId && videoStatus !== 'completed' && videoStatus !== 'failed' && videoStatus !== 'timeout') {
      interval = setInterval(pollVideoStatus, 5000)
      return () => clearInterval(interval)
    }
  }, [videoId, videoStatus, pollVideoStatus])

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('请输入视频描述')
      return
    }

    setIsGenerating(true)
    setError('')
    setVideoStatus('')
    setProgress(0)
    setVideoUrl('')
    pollCountRef.current = 0

    try {
      const response = await api.post('/videos/generate', {
        prompt: prompt.trim(),
        model: VIDEO_MODEL,
        num_frames: numFrames,
        frame_rate: frameRate,
      })

      setVideoId(response.data.id)
      setVideoStatus(response.data.status)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
      const message = axiosErr.response?.status === 402
        ? `积分余额不足，本次预计消耗 ${estimatedCredits} 积分，请充值或选择更短时长后重试`
        : axiosErr.response?.data?.detail || '视频生成请求失败'
      setError(message)
      showToast(message, axiosErr.response?.status === 402 ? 'warning' : 'error')
    } finally {
      setIsGenerating(false)
    }
  }

  const applyUseCase = (useCaseId: string) => {
    const useCase = VIDEO_USE_CASES.find((item) => item.id === useCaseId)
    if (!useCase) return
    setNumFrames(useCase.frames)
    setFrameRate(useCase.fps)
  }

  const applyTemplate = (templateId: string) => {
    const template = VIDEO_PROMPT_TEMPLATES.find((item) => item.id === templateId)
    if (!template) return
    setPrompt(template.prompt)
  }

  const handleEnhancePrompt = () => {
    if (!prompt.trim()) {
      setError('请输入视频描述')
      return
    }
    setPrompt(enhanceVideoPrompt(prompt))
    setError('')
  }

  const durationSeconds = (numFrames / frameRate).toFixed(2)

  return (
    <div className="container mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Video className="h-6 w-6" />
            AI 视频生成
          </CardTitle>
          <CardDescription>
            Powered by Agnes AI • {VIDEO_MODEL}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">参数预设</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
              {VIDEO_USE_CASES.map((useCase) => (
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
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-2">
              {VIDEO_PROMPT_TEMPLATES.map((template) => (
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
            <label htmlFor="video-prompt" className="text-sm font-medium">视频描述</label>
            <Textarea
              id="video-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A young astronaut walking across a red desert planet, dust blowing in the wind, slow cinematic tracking shot"
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

          {/* Video Settings */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="video-duration" className="text-sm font-medium">时长</label>
              <Select value={`${numFrames}-${frameRate}`} onValueChange={(val) => {
                const [frames, fps] = val.split('-').map(Number)
                setNumFrames(frames)
                setFrameRate(fps)
              }}>
                <SelectTrigger id="video-duration" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VIDEO_DURATIONS.map((dur) => (
                    <SelectItem key={dur.id} value={`${dur.frames}-${dur.fps}`}>
                      {dur.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label htmlFor="video-frames" className="text-sm font-medium">帧数</label>
              <Select value={numFrames.toString()} onValueChange={(val) => setNumFrames(Number(val))}>
                <SelectTrigger id="video-frames" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VALID_FRAME_COUNTS.map((frames) => (
                    <SelectItem key={frames} value={frames.toString()}>
                      {frames} 帧
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label htmlFor="video-fps" className="text-sm font-medium">帧率</label>
              <Select value={frameRate.toString()} onValueChange={(val) => setFrameRate(Number(val))}>
                <SelectTrigger id="video-fps" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VALID_FRAME_RATES.map((fps) => (
                    <SelectItem key={fps} value={fps.toString()}>
                      {fps} FPS
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Duration Info */}
          <div className="text-sm text-muted-foreground">
            预计时长: {durationSeconds} 秒 · 预计消耗: <span className="font-medium text-foreground">{estimatedCredits}</span> 积分
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
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                生成视频
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

          {/* Progress */}
          {(videoStatus && videoStatus !== 'timeout') && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>状态: {videoStatus === 'completed' ? '已完成' : videoStatus === 'failed' ? '失败' : '生成中...'}</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="w-full" />
            </div>
          )}

          {/* Result */}
          {videoUrl && (
            <div className="mt-4">
              <video
                src={videoUrl}
                controls
                className="w-full rounded-lg"
              />
              <div className="flex gap-2 mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const a = document.createElement('a')
                    a.href = videoUrl
                    a.download = `agnes-video-${videoId}.mp4`
                    a.target = '_blank'
                    a.rel = 'noopener noreferrer'
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                  }}
                >
                  <Download className="h-4 w-4 mr-2" />
                  下载
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (navigator.share) {
                      navigator.share({
                        title: 'AI Generated Video',
                        text: prompt,
                        url: videoUrl,
                      })
                    } else {
                      navigator.clipboard.writeText(videoUrl)
                    }
                  }}
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  分享
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

    </div>
  )
}
