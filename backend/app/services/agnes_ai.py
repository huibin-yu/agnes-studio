"""Agnes AI Service - Handles all Agnes API interactions based on official documentation"""
import logging
import os
import httpx
from typing import Dict, Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Use centralized configuration from settings
AGNES_API_BASE = settings.AGNES_API_BASE
AGNES_API_KEY = settings.AGNES_API_KEY
IMAGE_MODELS = settings.IMAGE_MODELS
VIDEO_MODEL = settings.VIDEO_MODEL
VALID_IMAGE_SIZES = settings.VALID_IMAGE_SIZES
VALID_FRAME_COUNTS = settings.VALID_FRAME_COUNTS
DEFAULT_FRAME_RATE = settings.DEFAULT_FRAME_RATE

# Prompt templates from official documentation
IMAGE_PROMPT_TEMPLATES = {
    "cinematic": "[Main subject] + [Scene / background] + [Cinematic style] + [Dramatic lighting] + [Wide-angle composition] + [High detail]",
    "anime": "[Character description] + [Action/pose] + [Background/setting] + [Anime art style] + [Vibrant colors] + [Detailed]",
    "realistic": "[Subject] + [Environment] + [Photorealistic style] + [Natural lighting] + [Professional photography] + [8K quality]",
    "digital-art": "[Subject] + [Scene] + [Digital art style] + [Fantasy elements] + [Glowing effects] + [Detailed illustration]",
    "oil-painting": "[Subject] + [Scene] + [Oil painting style] + [Rich colors] + [Classic composition] + [Artistic brushstrokes]",
    "watercolor": "[Subject] + [Scene] + [Watercolor style] + [Soft colors] + [Transparent layers] + [Delicate details]",
    "pixel-art": "[Subject] + [Scene] + [Pixel art style] + [Retro gaming aesthetic] + [Limited color palette] + [8-bit/16-bit]",
    "3d-render": "[Subject] + [Scene] + [3D rendering style] + [Realistic materials] + [Studio lighting] + [High quality]",
    "fantasy": "[Subject] + [Magical scene] + [Fantasy art style] + [Enchanted atmosphere] + [Dramatic lighting] + [Detailed]",
    "scifi": "[Subject] + [Futuristic scene] + [Sci-fi style] + [Neon lights] + [High-tech elements] + [Cinematic]",
    "horror": "[Subject] + [Dark scene] + [Horror style] + [Eerie atmosphere] + [Dramatic shadows] + [Detailed]",
    "minimalist": "[Subject] + [Simple background] + [Minimalist style] + [Clean lines] + [Limited colors] + [Modern design]",
    "pop-art": "[Subject] + [Bold background] + [Pop art style] + [Vibrant colors] + [Graphic style] + [Eye-catching]",
    "comic": "[Subject] + [Action pose] + [Comic book style] + [Dynamic lines] + [Speech bubbles optional] + [Detailed]",
}

# Video prompt templates from official documentation
VIDEO_PROMPT_TEMPLATES = {
    "cinematic": "[Subject] + [Action/movement] + [Scene/environment] + [Camera movement] + [Cinematic lighting] + [Film style]",
    "product-showcase": "[Product] + [Slow rotation/display] + [Clean background] + [Studio lighting] + [Professional commercial video]",
    "character-animation": "[Character description] + [Subtle motion/breathing] + [Background] + [Natural movement] + [Realistic style]",
    "scene-transition": "[Scene A] + [Smooth transition] + [Scene B] + [Visual consistency] + [Dramatic lighting change] + [Wide angle]",
}


class AgnesAIService:
    """Service for interacting with Agnes AI API"""

    def __init__(self):
        self.api_key = AGNES_API_KEY
        self.api_base = AGNES_API_BASE
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=360.0  # 6 minutes for image/video generation
        )

    async def generate_image(self, prompt: str, size: str = "1024x768", 
                           style: str = None, negative_prompt: str = None,
                           model: str = "agnes-image-2.1-flash",
                           return_base64: bool = False) -> Dict:
        """
        Generate image using Agnes AI API
        
        Args:
            prompt: Text description of the image
            size: Image size (e.g., "1024x768")
            style: Style preset (will enhance prompt)
            negative_prompt: What to avoid in the image
            model: Model to use
            return_base64: Whether to return base64 instead of URL
            
        Returns:
            Dict with image_url and other metadata
        """
        # Enhance prompt with style if provided
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        # Add negative prompt if provided
        if negative_prompt:
            enhanced_prompt = f"{enhanced_prompt}\nAvoid: {negative_prompt}"
        
        # Prepare request body
        request_body = {
            "model": model,
            "prompt": enhanced_prompt,
            "size": size
        }
        
        # Add output format
        if return_base64:
            request_body["return_base64"] = True
        else:
            request_body["extra_body"] = {
                "response_format": "url"
            }
        
        try:
            response = await self.client.post("/images/generations", json=request_body)
            response.raise_for_status()
            data = response.json()
            
            # Extract image URL or base64
            if "data" in data and len(data["data"]) > 0:
                image_data = data["data"][0]
                if return_base64:
                    return {
                        "image_url": None,
                        "image_b64": image_data.get("b64_json"),
                        "prompt": enhanced_prompt,
                        "revised_prompt": image_data.get("revised_prompt")
                    }
                else:
                    return {
                        "image_url": image_data.get("url"),
                        "image_b64": None,
                        "prompt": enhanced_prompt,
                        "revised_prompt": image_data.get("revised_prompt")
                    }
            else:
                raise Exception("No image data in response")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Agnes API error: {e.response.status_code} - {e.response.text}")
            raise Exception("Image generation service error. Please try again later.")
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise Exception("Image generation failed. Please try again later.")

    async def generate_image_to_image(self, prompt: str, image_url: str, 
                                     size: str = "1024x768",
                                     model: str = "agnes-image-2.1-flash",
                                     return_base64: bool = False) -> Dict:
        """
        Edit/transform image using Agnes AI API (image-to-image)
        
        Args:
            prompt: Editing instruction
            image_url: URL of input image
            size: Output size
            model: Model to use
            return_base64: Whether to return base64
            
        Returns:
            Dict with generated image data
        """
        request_body = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "extra_body": {
                "image": [image_url],  # IMPORTANT: image must be in extra_body!
            }
        }
        
        if return_base64:
            request_body["extra_body"]["response_format"] = "b64_json"
        else:
            request_body["extra_body"]["response_format"] = "url"
        
        try:
            response = await self.client.post("/images/generations", json=request_body)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                image_data = data["data"][0]
                if return_base64:
                    return {
                        "image_url": None,
                        "image_b64": image_data.get("b64_json"),
                        "prompt": prompt,
                        "revised_prompt": image_data.get("revised_prompt")
                    }
                else:
                    return {
                        "image_url": image_data.get("url"),
                        "image_b64": None,
                        "prompt": prompt,
                        "revised_prompt": image_data.get("revised_prompt")
                    }
            else:
                raise Exception("No image data in response")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Agnes image-to-image API error: {e.response.status_code} - {e.response.text}")
            raise Exception("Image-to-image service error. Please try again later.")
        except Exception as e:
            logger.error(f"Image-to-image generation failed: {e}")
            raise Exception("Image-to-image generation failed. Please try again later.")

    async def create_video_task(self, prompt: str, mode: str = "ti2vid",
                               image: str = None, extra_body: Dict = None,
                               num_frames: int = 121, frame_rate: int = 24,
                               height: int = 768, width: int = 1152,
                               negative_prompt: str = None) -> Dict:
        """
        Create video generation task
        
        Args:
            prompt: Video description
            mode: Generation mode ("ti2vid" for text-to-video, "i2v" for image-to-video)
            image: URL for image-to-video mode
            extra_body: Additional parameters for multi-image/keyframe mode
            num_frames: Must be 8n+1 and <= 441
            frame_rate: FPS (1-60)
            height: Video height
            width: Video width
            negative_prompt: What to avoid
            
        Returns:
            Dict with task_id, video_id, and other metadata
        """
        request_body = {
            "model": VIDEO_MODEL,
            "prompt": prompt,
            "mode": mode,
            "num_frames": num_frames,
            "frame_rate": frame_rate,
            "height": height,
            "width": width
        }
        
        # Add image for image-to-video
        if image:
            request_body["image"] = image
            
        # Add extra_body for multi-image/keyframes
        if extra_body:
            request_body["extra_body"] = extra_body
            
        # Add negative prompt if provided
        if negative_prompt:
            request_body["negative_prompt"] = negative_prompt
            
        try:
            response = await self.client.post("/videos", json=request_body)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"Agnes video API error: {e.response.status_code} - {e.response.text}")
            raise Exception("Video creation service error. Please try again later.")
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            raise Exception("Video creation failed. Please try again later.")

    async def poll_video_status(self, video_id: str) -> Dict:
        """
        Poll video generation status using video_id (RECOMMENDED method)
        
        Args:
            video_id: The video ID from task creation
            
        Returns:
            Dict with video status and result
        """
        try:
            response = await self.client.get(
                "/agnesapi",
                params={"video_id": video_id}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Agnes video poll API error: {e.response.status_code} - {e.response.text}")
            raise Exception("Video status check failed. Please try again later.")
        except Exception as e:
            logger.error(f"Video polling failed: {e}")
            raise Exception("Video polling failed. Please try again later.")

    def _enhance_prompt(self, prompt: str, style: str = None) -> str:
        """
        Enhance prompt with style-specific keywords based on official documentation
        
        Args:
            prompt: Original prompt
            style: Style preset
            
        Returns:
            Enhanced prompt
        """
        if not style or style == "none":
            return prompt
            
        style_keywords = {
            "cinematic": ", cinematic realism, dramatic lighting, wide-angle composition, film grain, professional cinematography",
            "anime": ", anime style, vibrant colors, detailed character design, manga aesthetic",
            "realistic": ", photorealistic, professional photography, 8K resolution, natural lighting",
            "digital-art": ", digital art, fantasy illustration, glowing effects, detailed composition",
            "oil-painting": ", oil painting style, rich colors, classic composition, artistic brushstrokes",
            "watercolor": ", watercolor painting, soft colors, transparent layers, delicate details",
            "pixel-art": ", pixel art style, retro gaming aesthetic, limited color palette, 16-bit",
            "3d-render": ", 3D rendering, realistic materials, studio lighting, high quality render",
            "fantasy": ", fantasy art style, enchanted atmosphere, magical elements, dramatic lighting",
            "scifi": ", sci-fi style, futuristic elements, neon lights, high-tech, cinematic",
            "horror": ", horror style, dark atmosphere, eerie lighting, dramatic shadows",
            "minimalist": ", minimalist design, clean lines, simple composition, modern aesthetic",
            "pop-art": ", pop art style, bold colors, graphic design, eye-catching composition",
            "comic": ", comic book style, dynamic lines, action pose, detailed illustration"
        }
        
        if style in style_keywords:
            return f"{prompt}{style_keywords[style]}"
        return prompt


# Global instance
agnes_service = AgnesAIService()
