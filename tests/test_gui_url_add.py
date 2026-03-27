"""
测试GUI URL添加功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from url_utils import parse_live_url
from platform_parser import PlatformParser
from main import LiveRecorderApp

def test_add_room_by_url():
    """测试通过URL添加房间"""
    print('=' * 70)
    print('测试 add_room_by_url 功能')
    print('=' * 70)
    print()
    
    # 创建应用实例
    app = LiveRecorderApp()
    
    # 测试URL列表
    test_urls = [
        'https://v.douyin.com/rsTV9YUi7gI/',  # 抖音短链接
        'https://live.douyin.com/123456',  # 抖音标准链接
        'https://live.bilibili.com/789012',  # B站链接
    ]
    
    for idx, url in enumerate(test_urls, 1):
        print(f'测试 {idx}: {url}')
        print('-' * 70)
        
        # 解析URL
        result = parse_live_url(url)
        if result:
            platform, room_id = result
            print(f'✓ URL解析成功')
            print(f'  平台: {platform}')
            print(f'  房间ID: {room_id}')
        else:
            print(f'✗ URL解析失败')
            print()
            continue
        
        # 测试add_room_by_url方法
        success = app.add_room_by_url(url, name=f"测试房间{idx}", auto_record=False)
        if success:
            print(f'✓ add_room_by_url 成功')
            # 检查是否真的添加了
            rooms = app.get_rooms()
            print(f'  当前房间数: {len(rooms)}')
        else:
            print(f'✗ add_room_by_url 失败 (房间可能已存在)')
        
        print()
    
    print('=' * 70)
    print('测试完成!')
    print('=' * 70)

if __name__ == '__main__':
    test_add_room_by_url()
