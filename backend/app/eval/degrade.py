import cv2
import numpy as np
import random
import os

def apply_sepia(image):
    """Applies a sepia tone to the image."""
    image = np.array(image, dtype=np.float64)
    sepia_filter = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]
    ])
    sepia_image = cv2.transform(image, sepia_filter)
    sepia_image = np.clip(sepia_image, 0, 255)
    return sepia_image.astype(np.uint8)

def add_noise(image, severity=0.05):
    """Adds salt and pepper noise to the image."""
    row, col, ch = image.shape
    s_vs_p = 0.5
    amount = severity
    out = np.copy(image)
    
    # Salt mode
    num_salt = np.ceil(amount * image.size * s_vs_p)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in image.shape]
    out[tuple(coords)] = 255

    # Pepper mode
    num_pepper = np.ceil(amount * image.size * (1. - s_vs_p))
    coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in image.shape]
    out[tuple(coords)] = 0
    return out

def add_blur(image, ksize=5):
    """Applies Gaussian blur to the image."""
    return cv2.GaussianBlur(image, (ksize, ksize), 0)

def add_scratches(image, num_scratches=10, max_length=100, max_thickness=3):
    """Adds random white/light gray scratches."""
    out = np.copy(image)
    h, w = image.shape[:2]
    
    for _ in range(num_scratches):
        x1, y1 = random.randint(0, w), random.randint(0, h)
        
        # Random angle and length
        angle = random.uniform(0, 2 * np.pi)
        length = random.randint(10, max_length)
        
        x2 = int(x1 + length * np.cos(angle))
        y2 = int(y1 + length * np.sin(angle))
        
        thickness = random.randint(1, max_thickness)
        color = random.randint(200, 255) # Light scratch
        
        cv2.line(out, (x1, y1), (x2, y2), (color, color, color), thickness)
        
    return out

def synthesize_degradation(image_path, output_path):
    """Applies a full degradation pipeline to an image."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
        
    # 1. Sepia/Desaturation
    img = apply_sepia(img)
    
    # 2. Add Blur
    img = add_blur(img, ksize=random.choice([3, 5, 7]))
    
    # 3. Add Noise
    img = add_noise(img, severity=random.uniform(0.01, 0.03))
    
    # 4. Add Scratches
    img = add_scratches(img, num_scratches=random.randint(5, 20))
    
    cv2.imwrite(output_path, img)
    return img

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Synthetically degrade an image.")
    parser.add_argument("input", help="Path to input image")
    parser.add_argument("output", help="Path to output degraded image")
    args = parser.parse_args()
    
    synthesize_degradation(args.input, args.output)
    print(f"Degraded image saved to {args.output}")
