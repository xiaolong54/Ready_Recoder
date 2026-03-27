"""
URL工具模块
提供URL解析、标准化和处理功能
"""
import re
import urllib.parse
from typing import Optional, Tuple
import requests
from exceptions import URLParseError, URLValidationError


def normalize_url(url: str) -> str:
    """
    标准化URL
    
    Args:
        url: 原始URL
        
    Returns:
        标准化后的URL
        
    Examples:
        >>> normalize_url("https://live.douyin.com/123456?share_device=xxx")
        'https://live.douyin.com/123456'
        >>> normalize_url("live.douyin.com/123456")
        'https://live.douyin.com/123456'
    """
    if not url:
        return url
    
    url = url.strip()
    
    # 添加协议
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # 解析URL
    try:
        parsed = urllib.parse.urlparse(url)
        
        # 移除常见的追踪参数
        query_params = urllib.parse.parse_qs(parsed.query)
        params_to_remove = [
            'share_device', 'share_type', 'share_version',
            'utm_source', 'utm_medium', 'utm_campaign',
            'utm_term', 'utm_content', 'from',
            'share_id', 'timestamp'
        ]
        
        for param in params_to_remove:
            query_params.pop(param, None)
        
        # 重建URL
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        normalized_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ''  # 移除fragment
        ))
        
        return normalized_url
    except Exception as e:
        raise URLParseError(url, f"URL标准化失败: {e}")


def parse_douyin_url(url: str) -> Optional[str]:
    """
    解析抖音URL,提取房间ID
    
    Args:
        url: 抖音URL
        
    Returns:
        房间ID或None
        
    Examples:
        >>> parse_douyin_url("https://live.douyin.com/123456")
        '123456'
        >>> parse_douyin_url("https://v.douyin.com/abc123")
        'abc123'
    """
    # 标准化URL
    url = normalize_url(url)
    
    # 尝试直接从URL提取房间ID
    patterns = [
        r'live\.douyin\.com/(\w+)',
        r'douyin\.com/user/(\w+)',
        r'iesdouyin\.com/share/user/(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # 处理短链接 (v.douyin.com)
    if 'v.douyin.com' in url:
        # 提取短链接ID
        short_id_match = re.search(r'v\.douyin\.com/(\w+)', url)
        if short_id_match:
            short_id = short_id_match.group(1)
            # 返回短链接ID,需要后续通过重定向获取真实房间ID
            # 这里返回一个特殊标记,表示需要重定向
            return f"short:{short_id}"
    
    return None


def parse_bilibili_url(url: str) -> Optional[str]:
    """
    解析B站URL,提取房间ID
    
    Args:
        url: B站URL
        
    Returns:
        房间ID或None
        
    Examples:
        >>> parse_bilibili_url("https://live.bilibili.com/123456")
        '123456'
        >>> parse_bilibili_url("https://bilibili.com/123456")
        '123456'
    """
    patterns = [
        r'live\.bilibili\.com/(\d+)',
        r'bilibili\.com/(\d+)',
        r'live\.bilibili\.com/live/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def parse_douyu_url(url: str) -> Optional[str]:
    """
    解析斗鱼URL,提取房间ID
    
    Args:
        url: 斗鱼URL
        
    Returns:
        房间ID或None
        
    Examples:
        >>> parse_douyu_url("https://www.douyu.com/123456")
        '123456'
        >>> parse_douyu_url("https://m.douyu.com/abc123")
        'abc123'
    """
    patterns = [
        r'douyu\.com/(\w+)',
        r'live\.douyu\.com/(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def resolve_douyin_short_url(short_url: str) -> Optional[str]:
    """
    解析抖音短链接,获取真实房间ID
    
    Args:
        short_url: 抖音短链接 (如: https://v.douyin.com/abc123)
        
    Returns:
        真实房间ID,或None
        
    Examples:
        >>> resolve_douyin_short_url("https://v.douyin.com/abc123")
        '123456789'
    """
    try:
        # 发送HEAD请求获取重定向URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        # 使用HEAD请求避免下载完整页面
        response = requests.head(short_url, headers=headers, allow_redirects=True, timeout=10)
        
        # 获取最终URL
        final_url = response.url
        print(f"[URL Utils] 短链接重定向到: {final_url}")
        
        # 从最终URL提取房间ID - 支持多种格式
        patterns = [
            # 标准 live.douyin.com 格式
            r'live\.douyin\.com/(\d+)',
            r'live\.douyin\.com/(\w+)',
            # webcast.amemv.com 格式 (抖音海外版)
            r'webcast\.amemv\.com/douyin/webcast/reflow/(\d+)',
            r'webcast\.amemv\.com.*reflow[/?]([^\&\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, final_url)
            if match:
                room_id = match.group(1)
                print(f"[URL Utils] 从URL提取房间ID: {room_id}")
                return room_id
        
        # 如果HEAD请求失败,尝试GET请求
        if 'v.douyin.com' in final_url or 'webcast.amemv.com' in final_url:
            try:
                response = requests.get(final_url, headers=headers, allow_redirects=True, timeout=10)
                final_url = response.url
                print(f"[URL Utils] GET重定向到: {final_url}")
                
                for pattern in patterns:
                    match = re.search(pattern, final_url)
                    if match:
                        room_id = match.group(1)
                        print(f"[URL Utils] 从GET URL提取房间ID: {room_id}")
                        return room_id
            except Exception as e:
                print(f"[URL Utils] GET请求失败: {e}")
        
        return None
        
    except requests.exceptions.Timeout:
        print(f"[URL Utils] 解析抖音短链接超时: {short_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[URL Utils] 解析抖音短链接网络错误: {e}")
        return None
    except Exception as e:
        print(f"[URL Utils] 解析抖音短链接失败: {e}")
        return None


def parse_live_url(url: str) -> Optional[Tuple[str, str]]:
    """
    解析任意直播平台URL
    
    Args:
        url: 直播URL
        
    Returns:
        (platform, room_id) 元组,或None
        
    Examples:
        >>> parse_live_url("https://live.douyin.com/123456")
        ('douyin', '123456')
        >>> parse_live_url("https://live.bilibili.com/789012")
        ('bilibili', '789012')
        >>> parse_live_url("https://www.douyu.com/abc123")
        ('douyu', 'abc123')
    """
    url = normalize_url(url)
    
    # 尝试抖音
    douyin_id = parse_douyin_url(url)
    if douyin_id:
        # 检查是否是短链接标记
        if douyin_id.startswith('short:'):
            short_id = douyin_id[6:]  # 移除 "short:" 前缀
            # 解析短链接获取真实房间ID
            real_room_id = resolve_douyin_short_url(url)
            if real_room_id:
                return ('douyin', real_room_id)
            # 如果解析失败,使用短链接ID作为备选
            return ('douyin', short_id)
        return ('douyin', douyin_id)
    
    # 尝试B站
    bilibili_id = parse_bilibili_url(url)
    if bilibili_id:
        return ('bilibili', bilibili_id)
    
    # 尝试斗鱼
    douyu_id = parse_douyu_url(url)
    if douyu_id:
        return ('douyu', douyu_id)
    
    return None


def is_valid_url(url: str) -> bool:
    """
    检查URL是否是有效的直播URL
    
    Args:
        url: 待检查的URL
        
    Returns:
        是否是有效的直播URL
    """
    try:
        result = parse_live_url(url)
        return result is not None
    except Exception:
        return False


def is_room_id(query: str, platform: str = None) -> bool:
    """
    判断输入是否是房间ID
    
    Args:
        query: 输入内容
        platform: 平台名称(可选)
        
    Returns:
        是否是房间ID
    """
    query = query.strip()
    
    if platform is None or platform in ('douyin', 'bilibili'):
        # 抖音和B站使用数字ID
        return query.isdigit()
    
    if platform == 'douyu':
        # 斗鱼使用字母数字组合
        return bool(re.match(r'^[A-Za-z0-9_]+$', query))
    
    return False


def build_live_url(platform: str, room_id: str) -> str:
    """
    构建直播URL
    
    Args:
        platform: 平台名称
        room_id: 房间ID
        
    Returns:
        完整的直播URL
    """
    url_templates = {
        'douyin': f'https://live.douyin.com/{room_id}',
        'bilibili': f'https://live.bilibili.com/{room_id}',
        'douyu': f'https://www.douyu.com/{room_id}',
    }
    
    return url_templates.get(platform, '')


if __name__ == "__main__":
    # 测试URL工具函数
    print("测试URL工具函数:")
    print("=" * 60)
    
    # 测试normalize_url
    test_urls = [
        "live.douyin.com/123456",
        "https://live.douyin.com/123456?share_device=xxx&utm_source=web",
        "https://live.bilibili.com/789012",
        "www.douyu.com/abc123",
    ]
    
    print("\n1. URL标准化测试:")
    print("-" * 60)
    for url in test_urls:
        try:
            normalized = normalize_url(url)
            print(f"{url}\n  -> {normalized}")
        except URLParseError as e:
            print(f"{url}\n  -> ERROR: {e}")
    
    # 测试parse_live_url
    print("\n2. URL解析测试:")
    print("-" * 60)
    for url in test_urls:
        try:
            result = parse_live_url(url)
            print(f"{url}")
            if result:
                platform, room_id = result
                print(f"  -> 平台: {platform}, 房间ID: {room_id}")
            else:
                print(f"  -> 无法解析")
        except Exception as e:
            print(f"{url}")
            print(f"  -> ERROR: {e}")
    
    # 测试is_valid_url
    print("\n3. URL有效性测试:")
    print("-" * 60)
    test_valid_urls = [
        "https://live.douyin.com/123456",
        "https://www.baidu.com",
        "invalid-url",
    ]
    
    for url in test_valid_urls:
        result = is_valid_url(url)
        print(f"{url}: {'有效' if result else '无效'}")
    
    # 测试is_room_id
    print("\n4. 房间ID判断测试:")
    print("-" * 60)
    test_ids = [
        ("123456", "douyin"),
        ("abc123", "douyu"),
        ("123456", None),
        ("not-an-id", "douyin"),
    ]
    
    for query, platform in test_ids:
        result = is_room_id(query, platform)
        print(f"'{query}' (平台: {platform}): {'是ID' if result else '不是ID'}")
    
    # 测试build_live_url
    print("\n5. 构建URL测试:")
    print("-" * 60)
    test_build = [
        ("douyin", "123456"),
        ("bilibili", "789012"),
        ("douyu", "abc123"),
    ]
    
    for platform, room_id in test_build:
        url = build_live_url(platform, room_id)
        print(f"{platform}/{room_id} -> {url}")
