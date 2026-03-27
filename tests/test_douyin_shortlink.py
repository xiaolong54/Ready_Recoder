"""
测试抖音短链接完整流程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from url_utils import parse_live_url
from platform_parser import PlatformParser
from target_resolver import TargetResolver

def test_douyin_short_link():
    """测试抖音短链接解析"""
    print('=' * 70)
    print('测试抖音短链接完整流程')
    print('=' * 70)
    print()

    # 测试URL
    test_url = 'https://v.douyin.com/rsTV9YUi7gI/'
    print('1. 测试URL: ' + test_url)
    print()

    # 步骤1: URL解析
    print('步骤1: URL解析')
    print('-' * 70)
    result = parse_live_url(test_url)
    if result:
        platform, room_id = result
        print('✓ parse_live_url 成功')
        print('  平台: ' + platform)
        print('  房间ID: ' + room_id)
    else:
        print('✗ parse_live_url 失败')
    print()

    # 步骤2: PlatformParser
    print('步骤2: PlatformParser.parse_url')
    print('-' * 70)
    parsed = PlatformParser.parse_url(test_url)
    if parsed:
        print('✓ PlatformParser.parse_url 成功')
        print('  平台: ' + str(parsed.get('platform')))
        print('  房间ID: ' + str(parsed.get('room_id')))
        print('  URL: ' + str(parsed.get('url')))
        print('  是否短链接: ' + str(parsed.get('is_short_link', False)))
    else:
        print('✗ PlatformParser.parse_url 失败')
    print()

    # 步骤3: TargetResolver
    print('步骤3: TargetResolver.search_targets')
    print('-' * 70)
    resolver = TargetResolver()
    result = resolver.search_targets('douyin', test_url, limit=20)
    if result.success:
        print('✓ TargetResolver.search_targets 成功')
        print('  消息: ' + result.get_user_message())
        if result.data and len(result.data) > 0:
            candidate = result.data[0]
            print('  候选对象:')
            print('    平台: ' + str(candidate.get('platform')))
            print('    房间ID: ' + str(candidate.get('room_id')))
            print('    昵称: ' + str(candidate.get('nickname', '')))
            print('    来源: ' + str(candidate.get('source')))
    else:
        print('✗ TargetResolver.search_targets 失败')
        if result.error:
            print('  错误: ' + str(result.error))

    print()
    print('=' * 70)
    print('测试完成!')
    print('=' * 70)

if __name__ == '__main__':
    test_douyin_short_link()
