from app import db
from datetime import datetime
import json

class ProductionLine(db.Model):
    __tablename__ = 'production_lines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cameras = db.relationship('Camera', backref='production_line', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

class Camera(db.Model):
    __tablename__ = 'cameras'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lens_model = db.Column(db.String(100))
    focal_length = db.Column(db.Float)
    production_line_id = db.Column(db.Integer, db.ForeignKey('production_lines.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    calibration_tasks = db.relationship('CalibrationTask', backref='camera', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'lens_model': self.lens_model,
            'focal_length': self.focal_length,
            'production_line_id': self.production_line_id,
            'production_line_name': self.production_line.name if self.production_line else None,
            'created_at': self.created_at.isoformat()
        }

class CalibrationBoard(db.Model):
    __tablename__ = 'calibration_boards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    board_type = db.Column(db.String(50), nullable=False, default='chessboard')
    rows = db.Column(db.Integer, nullable=False)
    cols = db.Column(db.Integer, nullable=False)
    square_size = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    calibration_tasks = db.relationship('CalibrationTask', backref='calibration_board', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'board_type': self.board_type,
            'rows': self.rows,
            'cols': self.cols,
            'square_size': self.square_size,
            'created_at': self.created_at.isoformat()
        }

class CalibrationTask(db.Model):
    __tablename__ = 'calibration_tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    calibration_board_id = db.Column(db.Integer, db.ForeignKey('calibration_boards.id'), nullable=False)
    shooting_distance = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    error_type = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    intrinsic_params = db.Column(db.Text)
    distortion_params = db.Column(db.Text)
    reprojection_error = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    photos = db.relationship('CalibrationPhoto', backref='task', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        intrinsic = json.loads(self.intrinsic_params) if self.intrinsic_params else None
        distortion = json.loads(self.distortion_params) if self.distortion_params else None
        return {
            'id': self.id,
            'name': self.name,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'calibration_board_id': self.calibration_board_id,
            'calibration_board_name': self.calibration_board.name if self.calibration_board else None,
            'shooting_distance': self.shooting_distance,
            'status': self.status,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'intrinsic_params': intrinsic,
            'distortion_params': distortion,
            'reprojection_error': self.reprojection_error,
            'photo_count': len(self.photos),
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class CalibrationPhoto(db.Model):
    __tablename__ = 'calibration_photos'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('calibration_tasks.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    angle = db.Column(db.String(100))
    blur_score = db.Column(db.Float)
    corner_count = db.Column(db.Integer)
    status = db.Column(db.String(50), default='pending')
    error_message = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'angle': self.angle,
            'blur_score': self.blur_score,
            'corner_count': self.corner_count,
            'status': self.status,
            'error_message': self.error_message,
            'uploaded_at': self.uploaded_at.isoformat()
        }
