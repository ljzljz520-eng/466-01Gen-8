import cv2
import numpy as np
import os
from typing import Tuple, List, Dict, Optional


class CalibrationError(Exception):
    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(message)


class CameraCalibrator:
    BLUR_THRESHOLD = 100.0
    MIN_CORNER_RATIO = 0.8

    def __init__(self, rows: int, cols: int, square_size: float):
        self.rows = rows
        self.cols = cols
        self.square_size = square_size
        self.objp = self._prepare_object_points()

    def _prepare_object_points(self) -> np.ndarray:
        objp = np.zeros((self.rows * self.cols, 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.cols, 0:self.rows].T.reshape(-1, 2)
        objp *= self.square_size
        return objp

    @staticmethod
    def detect_blur(image_path: str) -> float:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise CalibrationError('image_error', f'无法读取图像: {image_path}')
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        return float(laplacian_var)

    def detect_corners(self, image_path: str) -> Tuple[Optional[np.ndarray], int, np.ndarray]:
        img = cv2.imread(image_path)
        if img is None:
            raise CalibrationError('image_error', f'无法读取图像: {image_path}')
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(
            gray, (self.cols, self.rows),
            cv2.CALIB_CB_ADAPTIVE_THRESH +
            cv2.CALIB_CB_NORMALIZE_IMAGE +
            cv2.CALIB_CB_FAST_CHECK
        )
        
        expected_corners = self.rows * self.cols
        if ret and corners is not None:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            return corners_refined, expected_corners, gray.shape[::-1]
        return None, 0, gray.shape[::-1]

    def validate_photo(self, image_path: str) -> Dict:
        blur_score = self.detect_blur(image_path)
        
        if blur_score < self.BLUR_THRESHOLD:
            return {
                'valid': False,
                'error_type': 'blur',
                'error_message': f'图像过于模糊，清晰度得分: {blur_score:.2f} (阈值: {self.BLUR_THRESHOLD})',
                'blur_score': blur_score,
                'corner_count': 0
            }
        
        corners, corner_count, image_size = self.detect_corners(image_path)
        
        if corners is None or corner_count == 0:
            return {
                'valid': False,
                'error_type': 'insufficient_corners',
                'error_message': f'未检测到足够的角点，期望: {self.rows * self.cols}，实际: 0',
                'blur_score': blur_score,
                'corner_count': 0
            }
        
        return {
            'valid': True,
            'blur_score': blur_score,
            'corner_count': corner_count,
            'corners': corners,
            'image_size': image_size
        }

    def _check_consistency(self, all_image_points: List[np.ndarray], all_object_points: List[np.ndarray]) -> Tuple[bool, str]:
        if len(all_image_points) < 3:
            return False, '有效图像数量不足，至少需要3张有效照片'
        
        corner_counts = [len(pts) for pts in all_image_points]
        expected_count = self.rows * self.cols
        
        inconsistent = [i for i, cnt in enumerate(corner_counts) if cnt != expected_count]
        if inconsistent:
            return False, f'参数不一致: 第{[i+1 for i in inconsistent]}张照片检测到的角点数量不一致'
        
        corner_variances = []
        for i in range(len(all_image_points)):
            for j in range(i + 1, len(all_image_points)):
                pts1 = all_image_points[i]
                pts2 = all_image_points[j]
                dist = np.mean(np.linalg.norm(pts1 - pts2, axis=2))
                corner_variances.append(dist)
        
        if len(corner_variances) > 0:
            mean_dist = np.mean(corner_variances)
            if mean_dist < 5:
                return False, '参数不一致: 拍摄角度过于相似，照片间差异性不足'
        
        return True, ''

    def calibrate(self, image_paths: List[str]) -> Dict:
        valid_results = []
        all_object_points = []
        all_image_points = []
        image_size = None
        
        blur_errors = []
        corner_errors = []
        
        for idx, path in enumerate(image_paths):
            result = self.validate_photo(path)
            if result['valid']:
                valid_results.append((idx + 1, result))
                all_object_points.append(self.objp)
                all_image_points.append(result['corners'])
                if image_size is None:
                    image_size = result['image_size']
            else:
                if result['error_type'] == 'blur':
                    blur_errors.append(f'第{idx+1}张: {result["error_message"]}')
                elif result['error_type'] == 'insufficient_corners':
                    corner_errors.append(f'第{idx+1}张: {result["error_message"]}')
        
        total_photos = len(image_paths)
        valid_count = len(valid_results)
        
        if valid_count == 0:
            error_type = 'blur' if blur_errors and not corner_errors else \
                        'insufficient_corners' if corner_errors and not blur_errors else \
                        'multiple_errors'
            all_errors = blur_errors + corner_errors
            raise CalibrationError(
                error_type,
                f'所有 {total_photos} 张照片均无效。' + '; '.join(all_errors[:5]) + ('...' if len(all_errors) > 5 else '')
            )
        
        if valid_count < max(3, total_photos * 0.6):
            error_type = 'multiple_errors'
            all_errors = blur_errors + corner_errors
            raise CalibrationError(
                error_type,
                f'有效照片数量不足: {valid_count}/{total_photos} (至少需要{max(3, int(total_photos*0.6))}张)。' +
                '; '.join(all_errors[:3])
            )
        
        consistent, msg = self._check_consistency(all_image_points, all_object_points)
        if not consistent:
            raise CalibrationError('parameter_inconsistency', msg)
        
        try:
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                all_object_points, all_image_points, image_size, None, None
            )
        except cv2.error as e:
            raise CalibrationError(
                'calibration_failed',
                f'标定计算失败: {str(e)}'
            )
        
        if not ret or mtx is None or dist is None:
            raise CalibrationError(
                'calibration_failed',
                '标定计算未能收敛，请检查照片质量和拍摄角度'
            )
        
        fx = mtx[0, 0]
        fy = mtx[1, 1]
        cx = mtx[0, 2]
        cy = mtx[1, 2]
        
        aspect_ratio = fx / fy
        if aspect_ratio < 0.9 or aspect_ratio > 1.1:
            raise CalibrationError(
                'parameter_inconsistency',
                f'内参计算结果异常，焦距比例: {aspect_ratio:.3f} (正常应接近1.0)，可能存在参数不一致'
            )
        
        total_error = 0
        for i in range(len(all_object_points)):
            imgpoints2, _ = cv2.projectPoints(
                all_object_points[i], rvecs[i], tvecs[i], mtx, dist
            )
            error = cv2.norm(all_image_points[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            total_error += error
        
        mean_reprojection_error = total_error / len(all_object_points) if all_object_points else float('inf')
        
        if mean_reprojection_error > 1.0:
            raise CalibrationError(
                'calibration_failed',
                f'重投影误差过大: {mean_reprojection_error:.4f}像素 (阈值: 1.0像素)，请检查照片质量'
            )
        
        return {
            'success': True,
            'reprojection_error': float(mean_reprojection_error),
            'intrinsic': {
                'fx': float(fx),
                'fy': float(fy),
                'cx': float(cx),
                'cy': float(cy),
                'matrix': mtx.tolist()
            },
            'distortion': {
                'k1': float(dist[0][0]),
                'k2': float(dist[0][1]),
                'p1': float(dist[0][2]),
                'p2': float(dist[0][3]),
                'k3': float(dist[0][4]) if len(dist[0]) > 4 else 0.0,
                'coefficients': dist.tolist()
            },
            'valid_photo_count': valid_count,
            'total_photo_count': total_photos,
            'blur_errors': blur_errors,
            'corner_errors': corner_errors
        }
