# watermark_algorithms.py
import numpy as np
import cv2
from typing import Tuple

class WatermarkAlgorithm:
    """
    基类水印算法
    """
    def embed_watermark(self, host_image: np.ndarray, watermark: np.ndarray) -> np.ndarray:
        """
        嵌入水印
        """
        raise NotImplementedError
    
    def extract_watermark(self, watermarked_image: np.ndarray, original_shape: Tuple[int, int]) -> np.ndarray:
         """
        提取水印
        """
        raise NotImplementedError
    
    def calculate_psnr(self, original_image: np.ndarray, watermarked_image: np.ndarray) -> float:
        """
        计算 PSNR
        """
        mse = np.mean((original_image.astype(float) - watermarked_image.astype(float)) ** 2)
        if mse == 0:
            return float('inf')
        return 20 * np.log10(255.0 / np.sqrt(mse))

    def calculate_nc(self, original_watermark: np.ndarray, extracted_watermark: np.ndarray) -> float:
            """
            计算归一化相关系数 (NC)
            """
            if original_watermark.shape != extracted_watermark.shape:
                extracted_watermark = cv2.resize(extracted_watermark, (original_watermark.shape[1], original_watermark.shape[0]))

            original_flat = original_watermark.flatten().astype(float)
            extracted_flat = extracted_watermark.flatten().astype(float)

            numerator = np.sum(original_flat * extracted_flat)
            denominator = np.sqrt(np.sum(original_flat ** 2) * np.sum(extracted_flat ** 2))

            if denominator == 0:
                return 0.0
            return numerator / denominator

class LSBWatermark(WatermarkAlgorithm):
    """
    LSB 水印算法
    """
    def __init__(self, bits: int = 1):
        self.bits = bits

    def embed_watermark(self, host_image: np.ndarray, watermark: np.ndarray) -> np.ndarray:
        """
        嵌入水印
        """
        # 确保图像为灰度图
        if len(host_image.shape) == 3:
            host_image = cv2.cvtColor(host_image, cv2.COLOR_RGB2GRAY)
        if len(watermark.shape) == 3:
            watermark = cv2.cvtColor(watermark, cv2.COLOR_RGB2GRAY)

        height, width = host_image.shape
        wm_height, wm_width = watermark.shape

        if wm_height > height or wm_width > width:
            raise ValueError("水印尺寸过大")

        watermarked_image = host_image.copy()

        for i in range(wm_height):
            for j in range(wm_width):
                # 将水印像素值嵌入到宿主图像的 LSB
                watermarked_image[i, j] = (watermarked_image[i, j] & (255 << self.bits)) | (watermark[i, j] >> (8 - self.bits))
                
        return watermarked_image

    def extract_watermark(self, watermarked_image: np.ndarray, watermark_shape: Tuple[int, int]) -> np.ndarray:
        """
        提取水印
        """
        # 确保图像为灰度图
        if len(watermarked_image.shape) == 3:
             watermarked_image = cv2.cvtColor(watermarked_image, cv2.COLOR_RGB2GRAY)
        
        wm_height, wm_width = watermark_shape
        extracted_watermark = np.zeros(watermark_shape, dtype=np.uint8)

        for i in range(wm_height):
            for j in range(wm_width):
                # 提取 LSB
                extracted_watermark[i, j] = (watermarked_image[i, j] & ((1 << self.bits) - 1)) << (8 - self.bits)

        return extracted_watermark

class DCTWatermark(WatermarkAlgorithm):
    """
    DCT 水印算法
    """
    def __init__(self, block_size: int = 8, alpha: float = 0.1):
        self.block_size = block_size
        self.alpha = alpha

    def embed_watermark(self, host_image: np.ndarray, watermark: np.ndarray) -> np.ndarray:
        """
        嵌入水印
        """
        # 确保图像为灰度图
        if len(host_image.shape) == 3:
            host_image = cv2.cvtColor(host_image, cv2.COLOR_RGB2GRAY)
        if len(watermark.shape) == 3:
            watermark = cv2.cvtColor(watermark, cv2.COLOR_RGB2GRAY)
        
        height, width = host_image.shape
        wm_height, wm_width = watermark.shape

        if wm_height > height // self.block_size or wm_width > width // self.block_size:
            raise ValueError("水印尺寸过大")
        
        watermarked_image = host_image.copy().astype(np.float32) # 使用 float32 进行计算
        
        for i in range(0, height, self.block_size):
            for j in range(0, width, self.block_size):
                # 获取块
                block = watermarked_image[i:i + self.block_size, j:j + self.block_size]
                # DCT 变换
                dct_block = cv2.dct(block)
                
                # 提取水印在当前块中的对应位置 (简化实现，只使用左上角低频系数)
                wm_i = i // self.block_size
                wm_j = j // self.block_size
                
                if wm_i < wm_height and wm_j < wm_width:  # 检查是否越界
                  # 嵌入水印
                  dct_block[2, 2] += self.alpha * watermark[wm_i, wm_j] # 在(2, 2)位置嵌入，增加鲁棒性
                
                # IDCT 变换
                watermarked_image[i:i + self.block_size, j:j + self.block_size] = cv2.idct(dct_block)

        return watermarked_image.astype(np.uint8)
    
    def extract_watermark(self, watermarked_image: np.ndarray, watermark_shape: Tuple[int, int]) -> np.ndarray:
        """
        提取水印
        """
        # 确保图像为灰度图
        if len(watermarked_image.shape) == 3:
            watermarked_image = cv2.cvtColor(watermarked_image, cv2.COLOR_RGB2GRAY)
        
        wm_height, wm_width = watermark_shape
        extracted_watermark = np.zeros((wm_height, wm_width), dtype=np.uint8)
        
        height, width = watermarked_image.shape
        
        for i in range(0, height, self.block_size):
            for j in range(0, width, self.block_size):
                
                block = watermarked_image[i:i + self.block_size, j:j + self.block_size].astype(np.float32)
                dct_block = cv2.dct(block)
                
                wm_i = i // self.block_size
                wm_j = j // self.block_size
                
                if wm_i < wm_height and wm_j < wm_width:
                    # 提取水印  (提取时需要判断是否小于等于0， 取绝对值)
                    watermark_value = dct_block[2, 2] / self.alpha
                    extracted_watermark[wm_i, wm_j] = int(watermark_value) # 需要取整
                    #extracted_watermark[wm_i, wm_j] = abs(dct_block[2, 2] / self.alpha)  #尝试使用绝对值
        return extracted_watermark
