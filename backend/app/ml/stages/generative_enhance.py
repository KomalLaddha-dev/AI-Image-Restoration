import os
import cv2
import time
import requests
import base64
import numpy as np
from loguru import logger
from skimage.metrics import structural_similarity as ssim

class RemoteColabHYPIR:
    def __init__(self):
        from app.config import get_settings
        settings = get_settings()
        self.url = settings.colab_hypir_url.rstrip("/")
        self.api_key = settings.colab_hypir_api_key

    def check_health(self) -> bool:
        if not self.url:
            return False
        try:
            resp = requests.get(f"{self.url}/health", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("model_loaded") is True:
                    return True
            return False
        except requests.exceptions.RequestException:
            return False

    def enhance(self, image: np.ndarray) -> np.ndarray | None:
        try:
            _, encoded = cv2.imencode('.jpg', image)
            img_b64 = base64.b64encode(encoded.tobytes()).decode("utf-8")
            payload = {'image_base64': img_b64, 'patch_size': 512, 'stride': 256}
            headers = {'x-api-key': self.api_key}

            resp = requests.post(f"{self.url}/enhance", json=payload, headers=headers, timeout=90.0)
            if resp.status_code == 200:
                data = resp.json()
                img_arr = np.frombuffer(base64.b64decode(data['image_base64']), np.uint8)
                result = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                return result
            else:
                logger.error(f"Colab HYPIR /enhance failed with status {resp.status_code}: {resp.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Colab HYPIR request failed: {e}")
            return None


class GenerativeEnhancer:
    def __init__(self):
        self.provider = None

    def load(self, provider_type: str = "off"):
        if provider_type == "colab":
            self.provider = RemoteColabHYPIR()
        elif provider_type == "local":
            self.provider = None # Not implemented
        elif provider_type == "hosted":
            self.provider = None # Not implemented
        else:
            self.provider = None

    def unload(self):
        self.provider = None

    def process(self, image: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Returns a tuple: (enhanced_image, success)
        """
        if self.provider is None:
            return image, False

        start_time = time.time()
        
        # 1. Check Health
        if hasattr(self.provider, "check_health"):
            if not self.provider.check_health():
                logger.warning("Colab HYPIR unavailable, falling back to Real-ESRGAN")
                return image, False

        # 2. Enhance
        enhanced = self.provider.enhance(image)
        if enhanced is None:
            logger.warning("Colab HYPIR enhancement failed, falling back to Real-ESRGAN")
            return image, False

        duration = time.time() - start_time

        # 3. Fidelity Guard
        h, w = image.shape[:2]
        
        # 1/8-downsampled luminance comparison
        gray_in = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_out = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        
        target_h, target_w = max(1, h // 8), max(1, w // 8)
        gray_in_down = cv2.resize(gray_in, (target_w, target_h), interpolation=cv2.INTER_AREA)
        gray_out_down = cv2.resize(gray_out, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
        s, _ = ssim(gray_in_down, gray_out_down, data_range=255, full=True)
        
        if s < 0.80:
            logger.warning(f"Generative fidelity guard failed! SSIM={s:.3f}. Falling back to Real-ESRGAN.")
            return image, False

        logger.info(f"Generative enhancement succeeded. SSIM: {s:.3f}, Time: {duration:.2f}s")
        return enhanced, True
