export const VIDEO_MODEL = 'agnes-video-v2.0'

export const VALID_FRAME_COUNTS = [81, 121, 161, 241, 441]

export const VALID_FRAME_RATES = [16, 24, 30, 60]

export const VIDEO_DURATIONS = [
  { id: 1, label: '3s (81 frames @ 24fps)', frames: 81, fps: 24 },
  { id: 2, label: '5s (121 frames @ 24fps)', frames: 121, fps: 24 },
  { id: 3, label: '7s (161 frames @ 24fps)', frames: 161, fps: 24 },
  { id: 4, label: '10s (241 frames @ 24fps)', frames: 241, fps: 24 },
  { id: 5, label: '18s (441 frames @ 24fps)', frames: 441, fps: 24 },
]

export const VIDEO_PROMPT_TEMPLATES = [
  {
    id: 1,
    name: 'Cinematic Portrait',
    example: 'A young astronaut walking across a red desert planet, dust blowing in the wind, slow cinematic tracking shot',
    template: 'Cinematic portrait of an astronaut in a red desert',
  },
  {
    id: 2,
    name: 'Nature Documentary',
    example: 'Time-lapse of a flower blooming in a forest, sunlight filtering through leaves, peaceful atmosphere',
    template: 'Nature time-lapse of flower blooming',
  },
  {
    id: 3,
    name: 'City Aerial',
    example: 'Drone shot flying over a futuristic cityscape at sunset, neon lights beginning to glow, smooth movement',
    template: 'Aerial cityscape at sunset',
  },
  {
    id: 4,
    name: 'Abstract Motion',
    example: 'Colorful liquid morphing and flowing, macro shot, slow motion, vibrant colors blending together',
    template: 'Abstract colorful liquid flow',
  },
]
