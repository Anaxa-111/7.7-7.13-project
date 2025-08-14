import os
import cv2
import numpy as np
from robustness_test import RobustnessTest, create_sample_images # 导入 create_sample_images 函数.

if __name__ == '__main__':
    # 检查示例图像是否存在，如果不存在，则创建.
    if not os.path.exists("sample_images/host_image.png") or not os.path.exists("sample_images/watermark.png"):
        host_image_path, watermark_path = create_sample_images()  # 创建图片
    else:
        host_image_path = "sample_images/host_image.png"
        watermark_path = "sample_images/watermark.png"

    # 初始化鲁棒性测试器
    robustness_tester = RobustnessTest()
    
    # 运行综合测试
    all_results = robustness_tester.run_comprehensive_test(
        host_image_path=host_image_path,
        watermark_path=watermark_path,
        output_dir="robustness_results" # 指定输出文件夹
    )
    
    # 打印总结(可选)
    print("\n测试完成, 结果如下:")
    for alg_name, results in all_results.items():
        print(f"\n{alg_name} 算法:")
        if 'error' in results:
            print(f"  测试失败: {results['error']}")
        else:
            print(f"  PSNR (嵌入): {results['psnr']:.2f} dB")
            for attack_name, attack_result in results['attacks'].items():
                if 'error' in attack_result:
                    print(f"    {attack_name}: 测试失败 - {attack_result['error']}")
                else:
                    print(f"    {attack_name}: NC = {attack_result['nc']:.4f}, PSNR = {attack_result['psnr']:.2f} dB")
