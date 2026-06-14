export const IMAGE_MODEL = 'agnes-image-2.1-flash'
export const IMAGE_MODELS = [
  { id: 'agnes-image-2.1-flash', name: 'Agnes Image 2.1 Flash', recommended: true, description: 'Enhanced image generation with better high-density details' },
  { id: 'agnes-image-2.0-flash', name: 'Agnes Image 2.0 Flash', description: 'Fast image generation (text-to-image, image-to-image)' },
]
export const IMAGE_SIZES = [
  { id: '1024x768', width: 1024, height: 768, label: '1024×768 (Standard)', ratio: '4:3' },
  { id: '1024x1024', width: 1024, height: 1024, label: '1024×1024 (Square)', ratio: '1:1' },
  { id: '768x1024', width: 768, height: 1024, label: '768×1024 (Portrait)', ratio: '3:4' },
  { id: '2048x2048', width: 2048, height: 2048, label: '2048×2048 (2K)', ratio: '1:1' },
  { id: '4096x4096', width: 4096, height: 4096, label: '4096×4096 (4K)', ratio: '1:1' },
  { id: '1816x1024', width: 1816, height: 1024, label: '1816×1024 (Wide)', ratio: '16:9' },
  { id: '1024x1816', width: 1024, height: 1816, label: '1024×1816 (Tall)', ratio: '9:16' },
]

export const IMAGE_STYLES = [
  { id: 'none', label: 'No Style' },
  { id: 'cinematic', label: 'Cinematic' },
  { id: 'anime', label: 'Anime' },
  { id: 'photographic', label: 'Photographic' },
  { id: 'digital-art', label: 'Digital Art' },
  { id: 'pixel-art', label: 'Pixel Art' },
  { id: 'fantasy-art', label: 'Fantasy Art' },
]

export const IMAGE_PROMPT_TEMPLATES = [
  {
    id: 1,
    name: 'Landscape',
    template: 'A majestic mountain range at sunset, golden light, dramatic clouds, 8k ultra detailed',
  },
  {
    id: 2,
    name: 'Portrait',
    template: 'Elegant woman with flowing hair, soft lighting, bokeh background, cinematic portrait',
  },
  {
    id: 3,
    name: 'Sci-Fi',
    template: 'Futuristic space station orbiting a gas giant, stars in background, detailed sci-fi concept art',
  },
  {
    id: 4,
    name: 'Anime',
    template: 'Chibi character, pastel colors, sparkles, cute anime style, kawaii',
  },
]
