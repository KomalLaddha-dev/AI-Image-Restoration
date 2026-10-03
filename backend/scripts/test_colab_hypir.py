import os
import sys
from pathlib import Path
import time
import requests
import base64
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))
load_dotenv(backend_dir / ".env")

url = os.getenv("COLAB_HYPIR_URL", "").rstrip("/")
api_key = os.getenv("COLAB_HYPIR_API_KEY", "")

if not url:
    print("COLAB_HYPIR_URL is not set in .env.")
    sys.exit(1)

print(f"Checking health at {url}/health ...")
try:
    resp = requests.get(f"{url}/health", timeout=5.0)
    resp.raise_for_status()
    print("Health check response:", resp.json())
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)

test_img_path = backend_dir / "test_input.jpg"
if not test_img_path.exists():
    print(f"Test image not found at {test_img_path}")
    sys.exit(1)

print("Sending image for enhancement...")
start_time = time.time()
try:
    with open(test_img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        payload = {'image_base64': img_b64, 'patch_size': 512, 'stride': 256}
        headers = {'x-api-key': api_key}
        resp = requests.post(f"{url}/enhance", json=payload, headers=headers, timeout=90.0)
        
    if resp.status_code == 200:
        duration = time.time() - start_time
        data = resp.json()
        print(f"Enhancement succeeded in {duration:.2f}s")
        print(f"Peak VRAM used: {data.get('peak_vram_mb', 'N/A')} MB")
            
        result_path = backend_dir / "test_outputs" / "colab_hypir_result.jpg"
        result_path.parent.mkdir(exist_ok=True)
        with open(result_path, "wb") as out_f:
            out_f.write(base64.b64decode(data['image_base64']))
        print(f"Result saved to {result_path}")
    else:
        print(f"Enhancement failed with status {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"Enhancement request failed: {e}")
