import { create } from 'zustand'

interface GenerationItem {
  id?: number
  type: 'image' | 'video'
  prompt: string
  imageUrl?: string
  videoUrl?: string
  size?: string
  style?: string
  createdAt: string
}

interface GenerationState {
  isGenerating: boolean
  progress: number
  error: string | null
  generations: GenerationItem[]
  setImageGenerating: (generating: boolean) => void
  setProgress: (progress: number) => void
  setError: (error: string | null) => void
  addGeneration: (generation: GenerationItem) => void
  reset: () => void
}

export const useGenerationStore = create<GenerationState>()((set) => ({
  isGenerating: false,
  progress: 0,
  error: null,
  generations: [],

  setImageGenerating: (generating) => set({ isGenerating: generating }),
  setProgress: (progress) => set({ progress }),
  setError: (error) => set({ error }),
  addGeneration: (generation) => set((state) => ({
    generations: [...state.generations, generation],
  })),
  reset: () => set({ isGenerating: false, progress: 0, error: null }),
}))
