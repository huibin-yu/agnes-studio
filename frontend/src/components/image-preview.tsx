"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Download, ExternalLink } from "lucide-react"

interface ImagePreviewProps {
  imageUrl: string
  prompt: string
  isOpen: boolean
  onClose: () => void
}

export function ImagePreview({ imageUrl, prompt, isOpen, onClose }: ImagePreviewProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle>图片预览</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <img
            src={imageUrl}
            alt={prompt}
            className="w-full h-auto rounded-lg"
          />
          {prompt && (
            <div className="p-3 rounded-lg bg-muted">
              <p className="text-sm text-muted-foreground">提示词：</p>
              <p className="text-sm mt-1">{prompt}</p>
            </div>
          )}
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => window.open(imageUrl, "_blank")}>
              <ExternalLink className="w-4 h-4 mr-2" />
              新窗口打开
            </Button>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              下载
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
