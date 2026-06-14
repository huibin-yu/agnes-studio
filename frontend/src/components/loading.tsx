"use client"

interface LoadingDotsProps {
  message?: string
}

export function LoadingDots({ message = "Loading" }: LoadingDotsProps) {
  return (
    <div className="flex items-center gap-2">
      <span>{message}</span>
      <span className="inline-flex gap-0.5">
        <span className="animate-pulse [animation-delay:0s]">.</span>
        <span className="animate-pulse [animation-delay:0.2s]">.</span>
        <span className="animate-pulse [animation-delay:0.4s]">.</span>
      </span>
    </div>
  )
}
