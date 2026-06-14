export interface PromptTemplate {
  id: string
  name: string
  description: string
  prompt: string
  style?: string
  size?: string
}

export const IMAGE_PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    id: 'xhs-cover',
    name: '小红书封面',
    description: '适合生活方式、好物分享、教程封面',
    style: 'realistic',
    size: '1024x1024',
    prompt: '明亮干净的小红书风格封面，主体清晰，浅色背景，柔和自然光，画面留有标题空间，高级感构图',
  },
  {
    id: 'product',
    name: '产品主图',
    description: '电商、品牌展示、详情页首图',
    style: 'photographic',
    size: '1024x768',
    prompt: '高端产品摄影，一件精致产品置于简洁棚拍背景中，柔和布光，真实材质细节，商业广告质感',
  },
  {
    id: 'avatar',
    name: '头像形象',
    description: '社交头像、品牌 IP、账号人设',
    style: 'cinematic',
    size: '1024x1024',
    prompt: '半身肖像，主体面向镜头，自信自然的表情，电影级布光，背景虚化，细节丰富，专业头像摄影',
  },
  {
    id: 'poster',
    name: '活动海报',
    description: '适合活动、课程、营销视觉',
    style: 'digital-art',
    size: '1024x1816',
    prompt: '现代活动海报视觉，强烈视觉中心，层次清晰，动感构图，高级配色，适合加入标题和行动按钮',
  },
]

export const VIDEO_PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    id: 'opening',
    name: '短视频开场',
    description: '3-5 秒吸引注意力的开场镜头',
    prompt: '电影感短视频开场镜头，主体从画面中心进入，镜头缓慢推进，光线自然，节奏清晰，适合社交媒体',
  },
  {
    id: 'product-video',
    name: '产品展示',
    description: '产品旋转、特写、广告片段',
    prompt: '产品商业展示视频，产品缓慢旋转，镜头从全景切到材质特写，干净背景，专业棚拍灯光，高级广告质感',
  },
  {
    id: 'scene-motion',
    name: '场景氛围',
    description: '环境、旅行、自然风景动态镜头',
    prompt: '沉浸式场景氛围视频，镜头平滑移动，环境细节丰富，光影自然变化，电影纪录片质感',
  },
]

export function enhanceImagePrompt(prompt: string, style?: string) {
  const parts = [
    prompt.trim(),
    '主体清晰',
    '构图稳定',
    '高质量细节',
    '自然光影',
    '专业视觉呈现',
  ]
  if (style && style !== 'none') {
    parts.push(`${style} style`)
  }
  return Array.from(new Set(parts.filter(Boolean))).join(', ')
}

export function enhanceVideoPrompt(prompt: string) {
  const parts = [
    prompt.trim(),
    'smooth camera movement',
    'cinematic lighting',
    'clear subject motion',
    'stable composition',
    'high quality video',
  ]
  return Array.from(new Set(parts.filter(Boolean))).join(', ')
}
