from flask import Blueprint, request, jsonify, send_from_directory, current_app
from app import db
from app.models import ProductionLine, Camera, CalibrationBoard, CalibrationTask, CalibrationPhoto
from app.calibration import CameraCalibrator, CalibrationError
from datetime import datetime
import os
import uuid
import json

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)


@main_bp.route('/')
def index():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    return send_from_directory(static_dir, 'index.html')


@api_bp.route('/production-lines', methods=['GET'])
def get_production_lines():
    lines = ProductionLine.query.order_by(ProductionLine.created_at.desc()).all()
    return jsonify([line.to_dict() for line in lines])


@api_bp.route('/production-lines', methods=['POST'])
def create_production_line():
    data = request.json
    line = ProductionLine(
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(line)
    db.session.commit()
    return jsonify(line.to_dict()), 201


@api_bp.route('/production-lines/<int:id>', methods=['DELETE'])
def delete_production_line(id):
    line = ProductionLine.query.get_or_404(id)
    db.session.delete(line)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@api_bp.route('/cameras', methods=['GET'])
def get_cameras():
    cameras = Camera.query.order_by(Camera.created_at.desc()).all()
    return jsonify([cam.to_dict() for cam in cameras])


@api_bp.route('/cameras', methods=['POST'])
def create_camera():
    data = request.json
    camera = Camera(
        name=data['name'],
        lens_model=data.get('lens_model', ''),
        focal_length=data.get('focal_length'),
        production_line_id=data['production_line_id']
    )
    db.session.add(camera)
    db.session.commit()
    return jsonify(camera.to_dict()), 201


@api_bp.route('/cameras/<int:id>', methods=['DELETE'])
def delete_camera(id):
    camera = Camera.query.get_or_404(id)
    db.session.delete(camera)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@api_bp.route('/calibration-boards', methods=['GET'])
def get_calibration_boards():
    boards = CalibrationBoard.query.order_by(CalibrationBoard.created_at.desc()).all()
    return jsonify([board.to_dict() for board in boards])


@api_bp.route('/calibration-boards', methods=['POST'])
def create_calibration_board():
    data = request.json
    board = CalibrationBoard(
        name=data['name'],
        board_type=data.get('board_type', 'chessboard'),
        rows=data['rows'],
        cols=data['cols'],
        square_size=data['square_size']
    )
    db.session.add(board)
    db.session.commit()
    return jsonify(board.to_dict()), 201


@api_bp.route('/calibration-boards/<int:id>', methods=['DELETE'])
def delete_calibration_board(id):
    board = CalibrationBoard.query.get_or_404(id)
    db.session.delete(board)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@api_bp.route('/calibration-tasks', methods=['GET'])
def get_calibration_tasks():
    tasks = CalibrationTask.query.order_by(CalibrationTask.created_at.desc()).all()
    return jsonify([task.to_dict() for task in tasks])


@api_bp.route('/calibration-tasks/<int:id>', methods=['GET'])
def get_calibration_task(id):
    task = CalibrationTask.query.get_or_404(id)
    return jsonify(task.to_dict())


@api_bp.route('/calibration-tasks', methods=['POST'])
def create_calibration_task():
    data = request.json
    task = CalibrationTask(
        name=data['name'],
        camera_id=data['camera_id'],
        calibration_board_id=data['calibration_board_id'],
        shooting_distance=data['shooting_distance'],
        status='pending'
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@api_bp.route('/calibration-tasks/<int:id>', methods=['DELETE'])
def delete_calibration_task(id):
    task = CalibrationTask.query.get_or_404(id)
    for photo in task.photos:
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@api_bp.route('/calibration-tasks/<int:id>/photos', methods=['GET'])
def get_task_photos(id):
    photos = CalibrationPhoto.query.filter_by(task_id=id).order_by(CalibrationPhoto.uploaded_at.desc()).all()
    return jsonify([photo.to_dict() for photo in photos])


@api_bp.route('/calibration-tasks/<int:id>/photos', methods=['POST'])
def upload_photo(id):
    task = CalibrationTask.query.get_or_404(id)
    
    if 'photo' not in request.files:
        return jsonify({'error': '未找到上传文件'}), 400
    
    file = request.files['photo']
    angle = request.form.get('angle', '')
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
        return jsonify({'error': '不支持的文件格式，请上传 JPG, PNG 或 BMP 格式的图片'}), 400
    
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    board = task.calibration_board
    calibrator = CameraCalibrator(board.rows, board.cols, board.square_size)
    
    blur_score = None
    corner_count = None
    status = 'valid'
    error_msg = None
    
    try:
        result = calibrator.validate_photo(filepath)
        blur_score = result['blur_score']
        corner_count = result['corner_count']
        if not result['valid']:
            status = 'invalid'
            error_msg = result['error_message']
    except CalibrationError as e:
        status = 'invalid'
        error_msg = e.message
    except Exception as e:
        status = 'invalid'
        error_msg = f'处理照片时出错: {str(e)}'
    
    photo = CalibrationPhoto(
        task_id=id,
        filename=filename,
        original_filename=file.filename,
        angle=angle,
        blur_score=blur_score,
        corner_count=corner_count,
        status=status,
        error_message=error_msg
    )
    db.session.add(photo)
    db.session.commit()
    
    return jsonify(photo.to_dict()), 201


@api_bp.route('/photos/<int:id>', methods=['DELETE'])
def delete_photo(id):
    photo = CalibrationPhoto.query.get_or_404(id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(photo)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@api_bp.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@api_bp.route('/calibration-tasks/<int:id>/calibrate', methods=['POST'])
def calibrate(id):
    task = CalibrationTask.query.get_or_404(id)
    board = task.calibration_board
    
    photos = CalibrationPhoto.query.filter_by(task_id=id).all()
    valid_photos = [p for p in photos if p.status == 'valid']
    
    if len(valid_photos) < 3:
        return jsonify({
            'success': False,
            'error_type': 'insufficient_photos',
            'error_message': f'有效照片数量不足，当前有效: {len(valid_photos)} 张，至少需要 3 张'
        }), 400
    
    calibrator = CameraCalibrator(board.rows, board.cols, board.square_size)
    
    image_paths = []
    for p in valid_photos:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], p.filename)
        if os.path.exists(path):
            image_paths.append(path)
    
    try:
        result = calibrator.calibrate(image_paths)
        
        task.status = 'completed'
        task.intrinsic_params = json.dumps(result['intrinsic'])
        task.distortion_params = json.dumps(result['distortion'])
        task.reprojection_error = result['reprojection_error']
        task.completed_at = datetime.utcnow()
        task.error_type = None
        task.error_message = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': task.to_dict(),
            'details': {
                'valid_photo_count': result['valid_photo_count'],
                'total_photo_count': result['total_photo_count'],
                'blur_errors': result['blur_errors'],
                'corner_errors': result['corner_errors']
            }
        })
        
    except CalibrationError as e:
        task.status = 'failed'
        task.error_type = e.error_type
        task.error_message = e.message
        db.session.commit()
        
        return jsonify({
            'success': False,
            'error_type': e.error_type,
            'error_message': e.message,
            'task': task.to_dict()
        }), 400
    
    except Exception as e:
        task.status = 'failed'
        task.error_type = 'unknown'
        task.error_message = f'标定时发生未知错误: {str(e)}'
        db.session.commit()
        
        return jsonify({
            'success': False,
            'error_type': 'unknown',
            'error_message': task.error_message,
            'task': task.to_dict()
        }), 500


@api_bp.route('/shooting-guidance', methods=['GET'])
def get_shooting_guidance():
    guidance = [
        {
            'id': 1,
            'name': '正面',
            'description': '标定板正对相机，保持水平',
            'icon': '⬆️'
        },
        {
            'id': 2,
            'name': '左偏',
            'description': '标定板向左倾斜约15-30度',
            'icon': '⬅️'
        },
        {
            'id': 3,
            'name': '右偏',
            'description': '标定板向右倾斜约15-30度',
            'icon': '➡️'
        },
        {
            'id': 4,
            'name': '上仰',
            'description': '标定板向上倾斜约15-30度',
            'icon': '⬆️'
        },
        {
            'id': 5,
            'name': '下俯',
            'description': '标定板向下倾斜约15-30度',
            'icon': '⬇️'
        },
        {
            'id': 6,
            'name': '左前',
            'description': '标定板向左前方倾斜',
            'icon': '↖️'
        },
        {
            'id': 7,
            'name': '右前',
            'description': '标定板向右前方倾斜',
            'icon': '↗️'
        },
        {
            'id': 8,
            'name': '左后',
            'description': '标定板向左后方倾斜',
            'icon': '↙️'
        },
        {
            'id': 9,
            'name': '右后',
            'description': '标定板向右后方倾斜',
            'icon': '↘️'
        }
    ]
    return jsonify(guidance)
