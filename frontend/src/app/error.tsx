'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Application error:', error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold">出错了</h2>
        <p className="text-muted-foreground">
          页面加载时遇到了问题，请重试。
        </p>
        <Button onClick={reset}>重试</Button>
      </div>
    </div>
  )
}
