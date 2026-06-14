/**
 * Video generation constants based on official Agnes AI documentation
 * https://agnes-ai.com/doc/agnes-video-v20
 */

// Video model name
export const VIDEO_MODEL = "agnes-video-v2.0";

// Valid frame counts (must be 8n+1 and <= 441)
export const VALID_FRAME_COUNTS = [81, 121, 161, 241, 441];

// Recommended frame rates
export const FRAME_RATES = [16, 24, 30, 60];

// Video resolution presets
export const VIDEO_RESOLUTIONS = [
  { id: "1152x768", label: "1152×768 (HD)", width: 1152, height: 768 },
  { id: "768x1152", label: "768×1152 (Portrait)", width: 768, height: 1152 },
] as const;

// Duration presets based on frame counts and frame rate (24fps)
export const VIDEO_DURATIONS = [
  { id: "81-24", label: "~3 seconds (81 frames @ 24fps)", frames: 81, fps: 24, duration: 3.375 },
  { id: "121-24", label: "~5 seconds (121 frames @ 24fps)", frames: 121, fps: 24, duration: 5.04 },
  { id: "161-24", label: "~6.7 seconds (161 frames @ 24fps)", frames: 161, fps: 24, duration: 6.71 },
  { id: "241-24", label: "~10 seconds (241 frames @ 24fps)", frames: 241, fps: 24, duration: 10.04 },
  { id: "441-24", label: "~18 seconds (441 frames @ 24fps)", frames: 441, fps: 24, duration: 18.375 },
] as const;

// Video prompt templates from official documentation
export const VIDEO_PROMPT_TEMPLATES = [
  {
    id: "cinematic",
    name: "Cinematic",
    template: "[Subject] + [Action/movement] + [Scene/environment] + [Camera movement] + [Cinematic lighting] + [Film style]",
    example: "A young astronaut walking across a red desert planet, dust blowing in the wind, slow cinematic tracking shot, dramatic lighting, realistic style",
  },
  {
    id: "product-showcase",
    name: "Product Showcase",
    template: "[Product] + [Slow rotation/display] + [Clean background] + [Studio lighting] + [Professional commercial video]",
    example: "A luxury watch rotating slowly on a marble platform, smooth 360-degree product showcase, soft studio lighting, clean and minimal, professional commercial video",
  },
  {
    id: "character-animation",
    name: "Character Animation",
    template: "[Character description] + [Subtle motion/breathing] + [Background] + [Natural movement] + [Realistic style]",
    example: "Animate the character with subtle breathing motion, hair moving gently in the wind, background city street, realistic style",
  },
  {
    id: "scene-transition",
    name: "Scene Transition",
    template: "[Scene A] + [Smooth transition] + [Scene B] + [Visual consistency] + [Dramatic lighting change] + [Wide angle]",
    example: "A smooth cinematic transition from a rainy city street to a sunny countryside road, maintaining visual consistency, dramatic lighting change, wide angle",
  },
] as const;
