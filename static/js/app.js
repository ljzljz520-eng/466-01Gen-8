const API_BASE = '/api';

let currentTaskId = null;
let selectedAngle = null;
let guidanceList = [];

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadAllData();
    loadGuidance();
});

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(tab).classList.add('active');
        });
    });
}

async function apiCall(url, method = 'GET', data = null, isFormData = false) {
    try {
        const options = {
            method,
            headers: isFormData ? {} : { 'Content-Type': 'application/json' }
        };
        if (data && !isFormData) {
            options.body = JSON.stringify(data);
        } else if (data && isFormData) {
            options.body = data;
        }
        const response = await fetch(API_BASE + url, options);
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error_message || result.error || '请求失败');
        }
        return result;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function showModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

async function loadAllData() {
    await Promise.all([
        loadProductionLines(),
        loadCameras(),
        loadCalibrationBoards(),
        loadTasks()
    ]);
}

async function loadGuidance() {
    try {
        guidanceList = await apiCall('/shooting-guidance');
    } catch (e) {
        console.error('Failed to load guidance:', e);
    }
}

async function loadProductionLines() {
    try {
        const lines = await apiCall('/production-lines');
        renderLines(lines);
        populateLineSelect(lines);
    } catch (e) {
        console.error('Failed to load lines:', e);
    }
}

async function loadCameras() {
    try {
        const cameras = await apiCall('/cameras');
        renderCameras(cameras);
        populateCameraSelect(cameras);
    } catch (e) {
        console.error('Failed to load cameras:', e);
    }
}

async function loadCalibrationBoards() {
    try {
        const boards = await apiCall('/calibration-boards');
        renderBoards(boards);
        populateBoardSelect(boards);
    } catch (e) {
        console.error('Failed to load boards:', e);
    }
}

async function loadTasks() {
    try {
        const tasks = await apiCall('/calibration-tasks');
        renderTasks(tasks);
    } catch (e) {
        console.error('Failed to load tasks:', e);
    }
}

function populateLineSelect(lines) {
    const select = document.getElementById('camera-line-id');
    if (!select) return;
    select.innerHTML = lines.map(l => 
        `<option value="${l.id}">${l.name}</option>`
    ).join('');
}

function populateCameraSelect(cameras) {
    const select = document.getElementById('task-camera-id');
    if (!select) return;
    select.innerHTML = cameras.map(c => 
        `<option value="${c.id}">${c.name} (${c.production_line_name || '未分配'})</option>`
    ).join('');
}

function populateBoardSelect(boards) {
    const select = document.getElementById('task-board-id');
    if (!select) return;
    select.innerHTML = boards.map(b => 
        `<option value="${b.id}">${b.name} (${b.rows}×${b.cols}, ${b.square_size}mm)</option>`
    ).join('');
}

function renderLines(lines) {
    const container = document.getElementById('line-list');
    if (!lines.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🏭</div>
                <h3>暂无产线</h3>
                <p>点击上方按钮创建第一条产线</p>
            </div>
        `;
        return;
    }
    container.innerHTML = lines.map(line => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">🏭 ${line.name}</div>
            </div>
            <div class="card-body">
                <p>${line.description || '暂无描述'}</p>
                <p style="color: #a0aec0; font-size: 0.8rem;">创建于: ${formatDate(line.created_at)}</p>
            </div>
            <div class="card-footer">
                <button class="btn btn-danger" onclick="deleteLine(${line.id})">删除</button>
            </div>
        </div>
    `).join('');
}

function renderCameras(cameras) {
    const container = document.getElementById('camera-list');
    if (!cameras.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📷</div>
                <h3>暂无镜头</h3>
                <p>点击上方按钮创建第一个镜头</p>
            </div>
        `;
        return;
    }
    container.innerHTML = cameras.map(cam => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">📷 ${cam.name}</div>
            </div>
            <div class="card-body">
                <p>产线: ${cam.production_line_name || '未分配'}</p>
                <p>型号: ${cam.lens_model || '未设置'}</p>
                <p>焦距: ${cam.focal_length || '未设置'} mm</p>
                <p style="color: #a0aec0; font-size: 0.8rem;">创建于: ${formatDate(cam.created_at)}</p>
            </div>
            <div class="card-footer">
                <button class="btn btn-danger" onclick="deleteCamera(${cam.id})">删除</button>
            </div>
        </div>
    `).join('');
}

function renderBoards(boards) {
    const container = document.getElementById('board-list');
    if (!boards.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⬛</div>
                <h3>暂无标定板</h3>
                <p>点击上方按钮创建第一个标定板</p>
            </div>
        `;
        return;
    }
    container.innerHTML = boards.map(board => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">⬛ ${board.name}</div>
            </div>
            <div class="card-body">
                <p>类型: ${board.board_type === 'chessboard' ? '棋盘格' : board.board_type}</p>
                <p>内角点: ${board.rows} × ${board.cols} = ${board.rows * board.cols} 个</p>
                <p>方格尺寸: ${board.square_size} mm</p>
                <p style="color: #a0aec0; font-size: 0.8rem;">创建于: ${formatDate(board.created_at)}</p>
            </div>
            <div class="card-footer">
                <button class="btn btn-danger" onclick="deleteBoard(${board.id})">删除</button>
            </div>
        </div>
    `).join('');
}

function renderTasks(tasks) {
    const container = document.getElementById('task-list');
    if (!tasks.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <h3>暂无标定任务</h3>
                <p>点击上方按钮创建第一个标定任务</p>
            </div>
        `;
        return;
    }
    container.innerHTML = tasks.map(task => `
        <div class="card">
            <div class="card-header">
                <div class="card-title">📋 ${task.name}</div>
                <span class="status-badge status-${task.status}">${getStatusText(task.status)}</span>
            </div>
            <div class="card-body">
                <p>镜头: ${task.camera_name}</p>
                <p>标定板: ${task.calibration_board_name}</p>
                <p>拍摄距离: ${task.shooting_distance} mm</p>
                <p>照片数量: ${task.photo_count} 张</p>
                ${task.reprojection_error !== null ? 
                    `<p style="color: #48bb78;">重投影误差: ${task.reprojection_error.toFixed(4)} px</p>` : ''}
                ${task.error_message ? 
                    `<p style="color: #f56565; font-size: 0.85rem;">失败原因: ${task.error_message}</p>` : ''}
                <p style="color: #a0aec0; font-size: 0.8rem;">创建于: ${formatDate(task.created_at)}</p>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary" onclick="viewTaskDetail(${task.id})">查看详情</button>
                <button class="btn btn-danger" onclick="deleteTask(${task.id})">删除</button>
            </div>
        </div>
    `).join('');
}

function getStatusText(status) {
    const map = {
        'pending': '待标定',
        'completed': '已完成',
        'failed': '失败',
        'valid': '有效',
        'invalid': '无效'
    };
    return map[status] || status;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showCreateLineModal() {
    document.getElementById('line-name').value = '';
    document.getElementById('line-description').value = '';
    showModal('create-line-modal');
}

function showCreateCameraModal() {
    document.getElementById('camera-name').value = '';
    document.getElementById('camera-lens-model').value = '';
    document.getElementById('camera-focal-length').value = '';
    showModal('create-camera-modal');
}

function showCreateBoardModal() {
    document.getElementById('board-name').value = '';
    document.getElementById('board-rows').value = 6;
    document.getElementById('board-cols').value = 8;
    document.getElementById('board-square-size').value = 25;
    showModal('create-board-modal');
}

function showCreateTaskModal() {
    document.getElementById('task-name').value = '';
    document.getElementById('task-distance').value = '';
    showModal('create-task-modal');
}

async function createLine() {
    const name = document.getElementById('line-name').value.trim();
    const description = document.getElementById('line-description').value.trim();
    if (!name) {
        showToast('请输入产线名称', 'error');
        return;
    }
    await apiCall('/production-lines', 'POST', { name, description });
    showToast('产线创建成功');
    closeModal('create-line-modal');
    loadAllData();
}

async function createCamera() {
    const name = document.getElementById('camera-name').value.trim();
    const production_line_id = parseInt(document.getElementById('camera-line-id').value);
    const lens_model = document.getElementById('camera-lens-model').value.trim();
    const focal_length = parseFloat(document.getElementById('camera-focal-length').value) || null;
    if (!name) {
        showToast('请输入镜头名称', 'error');
        return;
    }
    await apiCall('/cameras', 'POST', { name, production_line_id, lens_model, focal_length });
    showToast('镜头创建成功');
    closeModal('create-camera-modal');
    loadAllData();
}

async function createBoard() {
    const name = document.getElementById('board-name').value.trim();
    const board_type = document.getElementById('board-type').value;
    const rows = parseInt(document.getElementById('board-rows').value);
    const cols = parseInt(document.getElementById('board-cols').value);
    const square_size = parseFloat(document.getElementById('board-square-size').value);
    if (!name) {
        showToast('请输入标定板名称', 'error');
        return;
    }
    if (rows < 2 || cols < 2) {
        showToast('内角点行列数必须大于等于2', 'error');
        return;
    }
    if (square_size <= 0) {
        showToast('方格尺寸必须大于0', 'error');
        return;
    }
    await apiCall('/calibration-boards', 'POST', { name, board_type, rows, cols, square_size });
    showToast('标定板创建成功');
    closeModal('create-board-modal');
    loadAllData();
}

async function createTask() {
    const name = document.getElementById('task-name').value.trim();
    const camera_id = parseInt(document.getElementById('task-camera-id').value);
    const calibration_board_id = parseInt(document.getElementById('task-board-id').value);
    const shooting_distance = parseFloat(document.getElementById('task-distance').value);
    if (!name) {
        showToast('请输入任务名称', 'error');
        return;
    }
    if (!shooting_distance || shooting_distance <= 0) {
        showToast('请输入有效的拍摄距离', 'error');
        return;
    }
    const task = await apiCall('/calibration-tasks', 'POST', { 
        name, camera_id, calibration_board_id, shooting_distance 
    });
    showToast('标定任务创建成功');
    closeModal('create-task-modal');
    loadAllData();
    setTimeout(() => viewTaskDetail(task.id), 300);
}

async function deleteLine(id) {
    if (!confirm('确定要删除这条产线吗？相关镜头不会被删除。')) return;
    await apiCall(`/production-lines/${id}`, 'DELETE');
    showToast('产线删除成功');
    loadAllData();
}

async function deleteCamera(id) {
    if (!confirm('确定要删除这个镜头吗？相关标定任务不会被删除。')) return;
    await apiCall(`/cameras/${id}`, 'DELETE');
    showToast('镜头删除成功');
    loadAllData();
}

async function deleteBoard(id) {
    if (!confirm('确定要删除这个标定板吗？相关标定任务不会被删除。')) return;
    await apiCall(`/calibration-boards/${id}`, 'DELETE');
    showToast('标定板删除成功');
    loadAllData();
}

async function deleteTask(id) {
    if (!confirm('确定要删除这个标定任务吗？相关照片也会被删除。')) return;
    await apiCall(`/calibration-tasks/${id}`, 'DELETE');
    showToast('标定任务删除成功');
    loadAllData();
}

let currentTaskData = null;
let currentTaskPhotos = null;

async function viewTaskDetail(id) {
    currentTaskId = id;
    try {
        const [task, photos] = await Promise.all([
            apiCall(`/calibration-tasks/${id}`),
            apiCall(`/calibration-tasks/${id}/photos`)
        ]);
        currentTaskData = task;
        currentTaskPhotos = photos;
        document.getElementById('detail-task-name').textContent = task.name;
        renderTaskDetail(task, photos);
        showModal('task-detail-modal');
    } catch (e) {
        console.error('Failed to load task detail:', e);
    }
}

function closeTaskDetail() {
    closeModal('task-detail-modal');
    currentTaskId = null;
    loadTasks();
}

function renderTaskDetail(task, photos) {
    const body = document.getElementById('task-detail-body');
    const validPhotos = photos.filter(p => p.status === 'valid');
    
    let html = '';
    
    html += `
        <div class="detail-section">
            <h4>任务信息</h4>
            <div class="detail-row">
                <span class="label">状态</span>
                <span class="value"><span class="status-badge status-${task.status}">${getStatusText(task.status)}</span></span>
            </div>
            <div class="detail-row">
                <span class="label">镜头</span>
                <span class="value">${task.camera_name}</span>
            </div>
            <div class="detail-row">
                <span class="label">标定板</span>
                <span class="value">${task.calibration_board_name}</span>
            </div>
            <div class="detail-row">
                <span class="label">拍摄距离</span>
                <span class="value">${task.shooting_distance} mm</span>
            </div>
            <div class="detail-row">
                <span class="label">创建时间</span>
                <span class="value">${formatDate(task.created_at)}</span>
            </div>
        </div>
    `;
    
    if (task.status === 'failed' && task.error_message) {
        html += `
            <div class="error-box">
                <h4>❌ 标定失败</h4>
                <p><strong>错误类型:</strong> ${getErrorTypeText(task.error_type)}</p>
                <p><strong>详细信息:</strong> ${task.error_message}</p>
            </div>
        `;
    }
    
    if (task.status === 'completed' && task.intrinsic_params) {
        html += `
            <div class="success-box">
                <h4>✅ 标定成功</h4>
                <p>重投影误差: <strong>${task.reprojection_error.toFixed(4)}</strong> 像素 (越小越好, < 1.0 为优秀)</p>
                <p>完成时间: ${formatDate(task.completed_at)}</p>
            </div>
            
            <div class="detail-section">
                <h4>内参结果</h4>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="label">焦距 fx</div>
                        <div class="value">${task.intrinsic_params.fx.toFixed(2)}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">焦距 fy</div>
                        <div class="value">${task.intrinsic_params.fy.toFixed(2)}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">主点 cx</div>
                        <div class="value">${task.intrinsic_params.cx.toFixed(2)}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">主点 cy</div>
                        <div class="value">${task.intrinsic_params.cy.toFixed(2)}</div>
                    </div>
                </div>
                
                <h4 style="margin-top: 24px;">内参矩阵</h4>
                <div class="matrix-display">
                    ${formatMatrix(task.intrinsic_params.matrix)}
                </div>
            </div>
            
            <div class="detail-section">
                <h4>畸变系数</h4>
                <div class="result-grid">
                    <div class="result-item">
                        <div class="label">径向畸变 k1</div>
                        <div class="value">${task.distortion_params.k1.toFixed(6)}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">径向畸变 k2</div>
                        <div class="value">${task.distortion_params.k2.toFixed(6)}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">切向畸变 p1</div>
                        <div class="value">${task.distortion_params.p1.toFixed(6)}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">切向畸变 p2</div>
                        <div class="value">${task.distortion_params.p2.toFixed(6)}</div>
                    </div>
                    <div class="result-item">
                        <div class="label">径向畸变 k3</div>
                        <div class="value">${task.distortion_params.k3.toFixed(6)}</div>
                    </div>
                </div>
                
                <h4 style="margin-top: 24px;">畸变向量</h4>
                <div class="matrix-display">
                    [${task.distortion_params.coefficients[0].map(v => v.toFixed(6)).join(', ')}]
                </div>
            </div>
        `;
    }
    
    html += `
        <div class="detail-section">
            <h4>拍摄引导 (请按不同角度上传照片)</h4>
            <div class="guidance-grid">
                ${guidanceList.map(g => `
                    <div class="guidance-item ${selectedAngle === g.name ? 'selected' : ''}" 
                         onclick="selectAngle('${g.name}')">
                        <div class="angle-icon">${g.icon}</div>
                        <div class="angle-name">${g.name}</div>
                        <div class="angle-desc">${g.description}</div>
                    </div>
                `).join('')}
            </div>
            
            <div class="upload-area" 
                 id="upload-area"
                 onclick="document.getElementById('photo-input').click()"
                 ondragover="handleDragOver(event)"
                 ondragleave="handleDragLeave(event)"
                 ondrop="handleDrop(event)">
                <div class="upload-icon">📸</div>
                <p><strong>点击或拖拽上传照片</strong></p>
                <p class="hint">已选择角度: ${selectedAngle || '请先选择拍摄角度'}</p>
                <p class="hint">支持 JPG, PNG, BMP 格式 | 当前有效: ${validPhotos.length}/${photos.length} 张</p>
                <input type="file" id="photo-input" accept="image/*" style="display: none;" onchange="handleFileSelect(event)">
            </div>
        </div>
        
        <div class="detail-section">
            <h4>已上传照片 (${photos.length} 张)</h4>
            ${photos.length === 0 ? `
                <div class="empty-state" style="padding: 30px;">
                    <div class="empty-icon">🖼️</div>
                    <h3>暂无照片</h3>
                    <p>请按照上方引导上传多角度标定板照片</p>
                </div>
            ` : `
                <div class="photo-grid">
                    ${photos.map(photo => renderPhotoItem(photo)).join('')}
                </div>
            `}
        </div>
    `;
    
    body.innerHTML = html;
    
    const footer = body.parentElement.querySelector('.action-bar') || document.createElement('div');
    if (!body.parentElement.querySelector('.action-bar')) {
        footer.className = 'action-bar';
        body.parentElement.appendChild(footer);
    }
    
    footer.innerHTML = `
        <button class="btn btn-secondary" onclick="closeTaskDetail()">关闭</button>
        <button class="btn btn-primary" onclick="startCalibration()" 
                ${validPhotos.length < 3 ? 'disabled' : ''}>
            ${validPhotos.length < 3 ? 
                `🔒 开始标定 (还需 ${3 - validPhotos.length} 张有效照片)` : 
                '🚀 开始计算内参'}
        </button>
    `;
}

function formatMatrix(matrix) {
    return matrix.map(row => 
        `[${row.map(v => v.toFixed(4).padStart(10)).join(', ')}]`
    ).join('\n');
}

function getErrorTypeText(type) {
    const map = {
        'blur': '照片模糊',
        'insufficient_corners': '角点不足',
        'parameter_inconsistency': '参数不一致',
        'calibration_failed': '标定计算失败',
        'multiple_errors': '多种错误',
        'insufficient_photos': '照片数量不足',
        'unknown': '未知错误'
    };
    return map[type] || type;
}

function selectAngle(angle) {
    selectedAngle = angle;
    if (currentTaskId) {
        renderTaskDetail(currentTaskData, currentTaskPhotos);
    }
}

function renderPhotoItem(photo) {
    const imgSrc = `/api/uploads/${photo.filename}`;
    return `
        <div class="photo-item ${photo.status}">
            <img src="${imgSrc}" alt="${photo.original_filename}" loading="lazy">
            <button class="delete-photo" onclick="deletePhoto(${photo.id}, event)">×</button>
            <div class="photo-overlay">
                <div>${photo.angle || '未标注'}</div>
                <div class="photo-info">
                    ${photo.blur_score !== null ? 
                        `<span class="blur-score">清晰度: ${photo.blur_score.toFixed(0)}</span>` : ''}
                    ${photo.corner_count !== null ? 
                        `<span class="corner-count"> | 角点: ${photo.corner_count}</span>` : ''}
                </div>
                ${photo.error_message ? 
                    `<div style="color: #fc8181; font-size: 0.75rem; margin-top: 4px;">⚠️ ${photo.error_message}</div>` : ''}
            </div>
        </div>
    `;
}

function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('upload-area').classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    document.getElementById('upload-area').classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    document.getElementById('upload-area').classList.remove('dragover');
    const files = e.dataTransfer.files;
    uploadFiles(files);
}

function handleFileSelect(e) {
    uploadFiles(e.target.files);
    e.target.value = '';
}

async function uploadFiles(files) {
    if (!selectedAngle) {
        showToast('请先选择拍摄角度', 'error');
        return;
    }
    
    if (!currentTaskId) return;
    
    for (const file of files) {
        if (!file.type.startsWith('image/')) {
            showToast(`跳过非图片文件: ${file.name}`, 'error');
            continue;
        }
        
        const formData = new FormData();
        formData.append('photo', file);
        formData.append('angle', selectedAngle);
        
        try {
            await apiCall(`/calibration-tasks/${currentTaskId}/photos`, 'POST', formData, true);
            showToast(`${file.name} 上传成功`);
        } catch (e) {
            console.error('Upload failed:', e);
        }
    }
    
    viewTaskDetail(currentTaskId);
}

async function deletePhoto(id, event) {
    event.stopPropagation();
    if (!confirm('确定要删除这张照片吗？')) return;
    await apiCall(`/photos/${id}`, 'DELETE');
    showToast('照片删除成功');
    viewTaskDetail(currentTaskId);
}

async function startCalibration() {
    if (!currentTaskId) return;
    
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="calibrating"></span>正在计算内参...';
    
    try {
        const result = await apiCall(`/calibration-tasks/${currentTaskId}/calibrate`, 'POST');
        if (result.success) {
            showToast('🎉 标定成功！内参已计算完成');
        } else {
            showToast(`标定失败: ${result.error_message}`, 'error');
        }
        viewTaskDetail(currentTaskId);
    } catch (e) {
        viewTaskDetail(currentTaskId);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}
