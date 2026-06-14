/**
 * Image generation constants based on official Agnes AI documentation
 * https://agnes-ai.com/doc/overview
 */

// Available image generation models
export const IMAGE_MODELS = [
  {
    id: "agnes-image-2.1-flash",
    name: "Image 2.1 Flash",
    description: "Enhanced model with better high-density details (Recommended)",
    recommended: true,
  },
  {
    id: "agnes-image-2.0-flash",
    name: "Image 2.0 Flash",
    description: "Fast image generation",
    recommended: false,
  },
] as const;

// Valid image sizes from official documentation
export const IMAGE_SIZES = [
  { id: "1024x768", label: "1024×768 (Standard)", ratio: "4:3" },
  { id: "1024x1024", label: "1024×1024 (Square)", ratio: "1:1" },
  { id: "768x1024", label: "768×1024 (Portrait)", ratio: "3:4" },
  { id: "2048x2048", label: "2048×2048 (2K)", ratio: "1:1" },
  { id: "4096x4096", label: "4096×4096 (4K)", ratio: "1:1" },
  { id: "1816x1024", label: "1816×1024 (Wide)", ratio: "16:9" },
  { id: "1024x1816", label: "1024×1816 (Tall)", ratio: "9:16" },
] as const;

// Image styles based on official prompt templates
export const IMAGE_STYLES = [
  { id: "none", label: "No Style", prompt_suffix: "" },
  { id: "cinematic", label: "Cinematic", prompt_suffix: ", cinematic realism, dramatic lighting, wide-angle composition, film grain, professional cinematography" },
  { id: "anime", label: "Anime", prompt_suffix: ", anime style, vibrant colors, detailed character design, manga aesthetic" },
  { id: "realistic", label: "Photorealistic", prompt_suffix: ", photorealistic, professional photography, 8K resolution, natural lighting" },
  { id: "digital-art", label: "Digital Art", prompt_suffix: ", digital art, fantasy illustration, glowing effects, detailed composition" },
  { id: "oil-painting", label: "Oil Painting", prompt_suffix: ", oil painting style, rich colors, classic composition, artistic brushstrokes" },
  { id: "watercolor", label: "Watercolor", prompt_suffix: ", watercolor painting, soft colors, transparent layers, delicate details" },
  { id: "pixel-art", label: "Pixel Art", prompt_suffix: ", pixel art style, retro gaming aesthetic, limited color palette, 16-bit" },
  { id: "3d-render", label: "3D Render", prompt_suffix: ", 3D rendering, realistic materials, studio lighting, high quality render" },
  { id: "fantasy", label: "Fantasy", prompt_suffix: ", fantasy art style, enchanted atmosphere, magical elements, dramatic lighting" },
  { id: "scifi", label: "Sci-Fi", prompt_suffix: ", sci-fi style, futuristic elements, neon lights, high-tech, cinematic" },
  { id: "horror", label: "Horror", prompt_suffix: ", horror style, dark atmosphere, eerie lighting, dramatic shadows" },
  { id: "minimalist", label: "Minimalist", prompt_suffix: ", minimalist design, clean lines, simple composition, modern aesthetic" },
  { id: "pop-art", label: "Pop Art", prompt_suffix: ", pop art style, bold colors, graphic design, eye-catching composition" },
  { id: "comic", label: "Comic", prompt_suffix: ", comic book style, dynamic lines, action pose, detailed illustration" },
] as const;
