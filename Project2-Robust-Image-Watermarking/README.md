def extract_watermark(original_image_path: str,  watermarked_image: np.ndarray, threshold: int = 10) -> np.ndarray:
    """
    从加水印的图像中提取水印 (基于差异)。

    Args:
        original_image_path: 原始图像路径。
        watermarked_image:  加水印后的图像 (NumPy 数组)。
        threshold:  阈值，用于二值化差异图像。

    Returns:
        提取的水印图像 (NumPy 数组,  灰度图像)，如果提取失败，返回 None。
    """
    try:
        original_image = cv2.imread(original_image_path)
        if original_image is None or watermarked_image is None:
            print("Error: Could not read images for extraction.")
            return None

        # 1. 将图像转换为灰度
        original_gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        watermarked_gray = cv2.cvtColor(watermarked_image, cv2.COLOR_BGR2GRAY)

        # 2. 计算差异图像
        diff = cv2.absdiff(watermarked_gray, original_gray)

        # 3.  threshold 二值化
        _, thresholded = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        # 4.  形态学操作 (可选,  用于降噪和平滑)  *非常重要！*
        kernel = np.ones((3, 3), np.uint8)
        closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel, iterations=2)
        opened  = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)


        return opened # 返回二值化后的图像

    except Exception as e:
        print(f"Error in extract_watermark: {e}")
        return None
