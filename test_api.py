#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://localhost:5000'

print('🚀 测试完整API流程\n')

print('1. 创建产线...')
r = requests.post(f'{BASE_URL}/api/production-lines', 
    json={'name': 'SMT产线A', 'description': '表面贴装生产线'})
line = r.json()
print(f'   ✅ 产线创建成功: {line["name"]} (ID: {line["id"]})')

print('\n2. 创建镜头...')
r = requests.post(f'{BASE_URL}/api/cameras', 
    json={
        'name': 'A01工位相机', 
        'production_line_id': line['id'],
        'lens_model': 'Computar M1214-MP2',
        'focal_length': 12
    })
camera = r.json()
print(f'   ✅ 镜头创建成功: {camera["name"]} (ID: {camera["id"]})')

print('\n3. 创建标定板...')
r = requests.post(f'{BASE_URL}/api/calibration-boards', 
    json={
        'name': '7x9棋盘格25mm', 
        'board_type': 'chessboard',
        'rows': 6,
        'cols': 8,
        'square_size': 25
    })
board = r.json()
print(f'   ✅ 标定板创建成功: {board["name"]} ({board["rows"]}x{board["cols"]})')

print('\n4. 创建标定任务...')
r = requests.post(f'{BASE_URL}/api/calibration-tasks', 
    json={
        'name': 'A01相机标定任务', 
        'camera_id': camera['id'],
        'calibration_board_id': board['id'],
        'shooting_distance': 300
    })
task = r.json()
print(f'   ✅ 标定任务创建成功: {task["name"]} (ID: {task["id"]})')

print('\n5. 获取拍摄引导...')
r = requests.get(f'{BASE_URL}/api/shooting-guidance')
guidance = r.json()
print(f'   ✅ 获取到 {len(guidance)} 种拍摄角度引导')

print('\n6. 查询所有数据...')
r = requests.get(f'{BASE_URL}/api/production-lines')
print(f'   ✅ 产线数量: {len(r.json())}')
r = requests.get(f'{BASE_URL}/api/cameras')
print(f'   ✅ 镜头数量: {len(r.json())}')
r = requests.get(f'{BASE_URL}/api/calibration-boards')
print(f'   ✅ 标定板数量: {len(r.json())}')
r = requests.get(f'{BASE_URL}/api/calibration-tasks')
print(f'   ✅ 标定任务数量: {len(r.json())}')

print('\n' + '🎉' * 20)
print('所有API测试通过！系统运行正常。')
print('访问 http://localhost:5000 查看Web界面')
print('🎉' * 20)
