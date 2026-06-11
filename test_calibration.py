#!/usr/bin/env python3
"""
测试相机标定核心算法功能
"""
import numpy as np
import cv2
import os
import tempfile
from app.calibration import CameraCalibrator, CalibrationError

def generate_test_chessboard(rows, cols, square_size, image_size=(800, 600)):
    """生成测试用的棋盘格图像"""
    board_width = cols * square_size
    board_height = rows * square_size
    scale = min(image_size[0] / board_width, image_size[1] / board_height) * 0.8
    
    img = np.ones((image_size[1], image_size[0]), dtype=np.uint8) * 255
    
    offset_x = int((image_size[0] - cols * square_size * scale) / 2)
    offset_y = int((image_size[1] - rows * square_size * scale) / 2)
    
    for i in range(rows + 1):
        for j in range(cols + 1):
            if (i + j) % 2 == 0:
                x1 = int(offset_x + j * square_size * scale)
                y1 = int(offset_y + i * square_size * scale)
                x2 = int(offset_x + (j + 1) * square_size * scale)
                y2 = int(offset_y + (i + 1) * square_size * scale)
                cv2.rectangle(img, (x1, y1), (x2, y2), 0, -1)
    
    return img

def generate_calibration_images(calibrator, num_images=10, save_dir=None):
    """生成模拟的标定图像（带不同角度的变换）"""
    if save_dir is None:
        save_dir = tempfile.mkdtemp()
    
    image_paths = []
    rows, cols = calibrator.rows, calibrator.cols
    square_size = calibrator.square_size
    
    base_img = generate_test_chessboard(rows, cols, square_size)
    
    angles = [
        (0, 0, 0),
        (8, 0, 0),
        (-8, 0, 0),
        (0, 8, 0),
        (0, -8, 0),
        (5, 5, 0),
        (-5, 5, 0),
        (5, -5, 0),
        (-5, -5, 0),
        (3, 3, 3),
    ]
    
    for i, (rx, ry, rz) in enumerate(angles[:num_images]):
        h, w = base_img.shape
        center = (w // 2, h // 2)
        
        M_rot = cv2.getRotationMatrix2D(center, rz, 1.0)
        img_rot = cv2.warpAffine(base_img, M_rot, (w, h))
        
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        
        offset_x = ry * 1.5
        offset_y = rx * 1.5
        pts2 = np.float32([
            [offset_x, offset_y],
            [w - offset_x, offset_y + 3],
            [offset_x + 3, h - offset_y],
            [w - offset_x - 3, h - offset_y - 3]
        ])
        
        M_persp = cv2.getPerspectiveTransform(pts1, pts2)
        img_warped = cv2.warpPerspective(img_rot, M_persp, (w, h))
        
        img_color = cv2.cvtColor(img_warped, cv2.COLOR_GRAY2BGR)
        
        filename = os.path.join(save_dir, f'calib_{i:02d}.jpg')
        cv2.imwrite(filename, img_color)
        image_paths.append(filename)
    
    return image_paths, save_dir

def test_blur_detection():
    """测试模糊检测功能"""
    print("=" * 60)
    print("测试1: 模糊检测功能")
    print("=" * 60)
    
    calibrator = CameraCalibrator(6, 8, 25)
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img_clear = np.random.randint(0, 255, (300, 300), dtype=np.uint8)
        cv2.imwrite(f.name, img_clear)
        blur_score_clear = calibrator.detect_blur(f.name)
        print(f"  清晰图像模糊得分: {blur_score_clear:.2f}")
        
        img_blur = cv2.GaussianBlur(img_clear, (31, 31), 0)
        cv2.imwrite(f.name, img_blur)
        blur_score_blur = calibrator.detect_blur(f.name)
        print(f"  模糊图像模糊得分: {blur_score_blur:.2f}")
        
        os.unlink(f.name)
    
    assert blur_score_clear > calibrator.BLUR_THRESHOLD, "清晰图像应该通过模糊检测"
    assert blur_score_blur < calibrator.BLUR_THRESHOLD, "模糊图像应该未通过模糊检测"
    print("  ✅ 模糊检测测试通过")
    return True

def test_corner_detection():
    """测试角点检测功能"""
    print("\n" + "=" * 60)
    print("测试2: 角点检测功能")
    print("=" * 60)
    
    calibrator = CameraCalibrator(6, 8, 25)
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img = generate_test_chessboard(6, 8, 25)
        img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.imwrite(f.name, img_color)
        
        corners, count, size = calibrator.detect_corners(f.name)
        print(f"  检测到角点数量: {count} / 期望: {6 * 8}")
        print(f"  图像尺寸: {size}")
        
        os.unlink(f.name)
    
    assert corners is not None, "应该检测到角点"
    assert count == 6 * 8, f"角点数量应该是 {6 * 8}"
    print("  ✅ 角点检测测试通过")
    return True

def test_photo_validation():
    """测试照片验证功能"""
    print("\n" + "=" * 60)
    print("测试3: 照片验证功能")
    print("=" * 60)
    
    calibrator = CameraCalibrator(6, 8, 25)
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img = generate_test_chessboard(6, 8, 25)
        img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.imwrite(f.name, img_color)
        
        result = calibrator.validate_photo(f.name)
        print(f"  验证结果: {'✅ 有效' if result['valid'] else '❌ 无效'}")
        print(f"  模糊得分: {result['blur_score']:.2f}")
        print(f"  角点数量: {result['corner_count']}")
        
        os.unlink(f.name)
    
    assert result['valid'], "标准棋盘格应该通过验证"
    print("  ✅ 照片验证测试通过")
    return True

def test_full_calibration():
    """测试完整的标定流程"""
    print("\n" + "=" * 60)
    print("测试4: 完整标定流程")
    print("=" * 60)
    
    calibrator = CameraCalibrator(6, 8, 25)
    
    print("  正在生成模拟标定图像...")
    image_paths, temp_dir = generate_calibration_images(calibrator, num_images=10)
    print(f"  生成了 {len(image_paths)} 张测试图像到: {temp_dir}")
    
    try:
        result = calibrator.calibrate(image_paths)
        print(f"\n  标定结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"  有效照片: {result['valid_photo_count']}/{result['total_photo_count']}")
        print(f"  重投影误差: {result['reprojection_error']:.6f} 像素")
        print(f"\n  内参结果:")
        print(f"    fx = {result['intrinsic']['fx']:.2f}")
        print(f"    fy = {result['intrinsic']['fy']:.2f}")
        print(f"    cx = {result['intrinsic']['cx']:.2f}")
        print(f"    cy = {result['intrinsic']['cy']:.2f}")
        print(f"\n  畸变系数:")
        print(f"    k1 = {result['distortion']['k1']:.6f}")
        print(f"    k2 = {result['distortion']['k2']:.6f}")
        print(f"    p1 = {result['distortion']['p1']:.6f}")
        print(f"    p2 = {result['distortion']['p2']:.6f}")
        print(f"    k3 = {result['distortion']['k3']:.6f}")
        
        assert result['success'], "标定应该成功"
        assert result['reprojection_error'] < 1.0, f"重投影误差应该小于1.0，实际: {result['reprojection_error']}"
        print("\n  ✅ 完整标定流程测试通过")
        return True
    except CalibrationError as e:
        print(f"\n  ❌ 标定失败: {e.error_type} - {e.message}")
        raise
    finally:
        for path in image_paths:
            if os.path.exists(path):
                os.unlink(path)
        os.rmdir(temp_dir)

def test_error_detection():
    """测试错误检测功能"""
    print("\n" + "=" * 60)
    print("测试5: 错误类型检测")
    print("=" * 60)
    
    calibrator = CameraCalibrator(6, 8, 25)
    
    print("  测试模糊错误检测...")
    with tempfile.TemporaryDirectory() as tmpdir:
        blur_paths = []
        for i in range(3):
            img = np.ones((400, 400), dtype=np.uint8) * 200
            img = cv2.GaussianBlur(img, (51, 51), 0)
            path = os.path.join(tmpdir, f'blur_{i}.jpg')
            cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
            blur_paths.append(path)
        
        try:
            calibrator.calibrate(blur_paths)
            print("  ❌ 应该抛出模糊错误")
            return False
        except CalibrationError as e:
            print(f"  ✅ 正确检测到错误类型: {e.error_type}")
            assert e.error_type in ['blur', 'insufficient_corners', 'multiple_errors'], "错误类型不正确"
    
    print("\n  测试角点不足错误检测...")
    with tempfile.TemporaryDirectory() as tmpdir:
        no_corner_paths = []
        for i in range(3):
            img = np.random.randint(0, 255, (400, 400), dtype=np.uint8)
            path = os.path.join(tmpdir, f'nocorner_{i}.jpg')
            cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
            no_corner_paths.append(path)
        
        try:
            calibrator.calibrate(no_corner_paths)
            print("  ❌ 应该抛出角点不足错误")
            return False
        except CalibrationError as e:
            print(f"  ✅ 正确检测到错误类型: {e.error_type}")
            assert e.error_type in ['insufficient_corners', 'multiple_errors'], "错误类型不正确"
    
    print("\n  ✅ 错误检测测试通过")
    return True

def main():
    print("\n" + "🚀" * 30)
    print("开始测试相机标定核心算法")
    print("🚀" * 30 + "\n")
    
    tests = [
        test_blur_detection,
        test_corner_detection,
        test_photo_validation,
        test_full_calibration,
        test_error_detection,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！算法功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查。")
        return 1

if __name__ == '__main__':
    exit(main())
