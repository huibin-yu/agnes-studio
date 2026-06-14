"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Check, AlertCircle, Info } from "lucide-react"
import { cn } from "@/lib/utils"

type ToastType = "success" | "error" | "info" | "warning"

interface Toast {
  id: number
  message: string
  type: ToastType
}

let toastId = 0

interface ToastProviderProps {
  children: React.ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    const interval = setInterval(() => {
      setToasts((prev) => prev.slice(1))
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const addToast = (message: string, type: ToastType = "info") => {
    const newToast: Toast = { id: toastId++, message, type }
    setToasts((prev) => [...prev, newToast])
  }

  if (typeof window !== "undefined") {
    window.showToast = addToast
  }

  return (
    <>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.9 }}
              className={cn(
                "flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg border max-w-sm",
                toast.type === "success" && "bg-green-50 border-green-200 text-green-800",
                toast.type === "error" && "bg-red-50 border-red-200 text-red-800",
                toast.type === "info" && "bg-blue-50 border-blue-200 text-blue-800",
                toast.type === "warning" && "bg-yellow-50 border-yellow-200 text-yellow-800"
              )}
            >
              {toast.type === "success" && <Check className="w-4 h-4" />}
              {toast.type === "error" && <AlertCircle className="w-4 h-4" />}
              {toast.type === "info" && <Info className="w-4 h-4" />}
              {toast.type === "warning" && <AlertCircle className="w-4 h-4" />}
              <span className="text-sm">{toast.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </>
  )
}

export function showToast(message: string, type: ToastType = "info") {
  if (typeof window.showToast === "function") {
    window.showToast(message, type)
  }
}

declare global {
  interface Window {
    showToast: (message: string, type?: ToastType) => void
  }
}
