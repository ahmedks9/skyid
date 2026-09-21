import cv2
import numpy as np


def load_grayscale_normalized(image_path):
    """
    Load an image and convert to a normalized grayscale float array.
    Returns a 2D numpy array with values in [0, 1].
    """
    img_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_float = img_gray.astype(np.float32) / 255.0

    return img_float

def subtract_background(img, blur_fraction=0.05):
    """
    Estimate and remove a smooth background gradient via large-kernel Gaussian blur.
    blur_fraction controls kernel size relative to image size (larger = smoother background estimate).
    """
    h, w = img.shape
    kernel_size = int(min(h, w) * blur_fraction)
    if kernel_size % 2 == 0:
        kernel_size += 1  # Gaussian blur kernel size must be odd
    kernel_size = max(kernel_size, 3)

    background = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
    subtracted = img - background
    subtracted = np.clip(subtracted, 0, 1)

    return subtracted, background

def denoise_light(img, kernel_size=3):
    """
    Apply a light median filter to reduce speckle noise while preserving small star blobs.
    """
    img_uint8 = (img * 255).astype(np.uint8)
    denoised_uint8 = cv2.medianBlur(img_uint8, kernel_size)
    denoised = denoised_uint8.astype(np.float32) / 255.0
    return denoised

if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    img = load_grayscale_normalized(path)
    print(f"Loaded image: shape={img.shape}, dtype={img.dtype}, "
          f"min={img.min():.3f}, max={img.max():.3f}, mean={img.mean():.3f}")

    subtracted, background = subtract_background(img)
    print(f"After background subtraction: min={subtracted.min():.3f}, "
          f"max={subtracted.max():.3f}, mean={subtracted.mean():.3f}")

    cv2.imwrite("debug_original.png", (img * 255).astype(np.uint8))
    cv2.imwrite("debug_background.png", (background * 255).astype(np.uint8))
    cv2.imwrite("debug_subtracted.png", (subtracted * 255).astype(np.uint8))
    print("Wrote debug_original.png, debug_background.png, debug_subtracted.png")