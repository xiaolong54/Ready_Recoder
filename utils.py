"""
工具函数模块
提供通用的格式化和辅助函数
"""


def format_follower_count(count: int) -> str:
    """
    格式化粉丝数为友好显示
    
    Args:
        count: 粉丝数原始数值
        
    Returns:
        格式化后的字符串,如 "12.3万", "1.5亿"
        
    Examples:
        >>> format_follower_count(12345)
        '12345'
        >>> format_follower_count(123456)
        '12.3万'
        >>> format_follower_count(12345678)
        '1234.6万'
        >>> format_follower_count(1234567890)
        '12.3亿'
    """
    if not isinstance(count, (int, float)) or count < 0:
        return "0"
    
    count = int(count)
    
    if count >= 100000000:  # 1亿以上
        return f"{count / 100000000:.1f}亿"
    elif count >= 10000:  # 1万以上
        return f"{count / 10000:.1f}万"
    else:
        return str(count)


def get_live_status_text(is_live: bool) -> str:
    """
    获取开播状态的文本描述
    
    Args:
        is_live: 是否在线
        
    Returns:
        状态文本,如 "在线" 或 "离线"
    """
    return "在线" if is_live else "离线"


def get_live_status_symbol(is_live: bool) -> str:
    """
    获取开播状态的符号标识
    
    Args:
        is_live: 是否在线
        
    Returns:
        状态符号,如 "✓" 或 "✗"
    """
    return "✓" if is_live else "✗"


if __name__ == "__main__":
    # 测试粉丝数格式化
    test_cases = [
        0,
        999,
        12345,
        123456,
        1234567,
        12345678,
        123456789,
        1234567890,
        12345678901,
    ]
    
    print("粉丝数格式化测试:")
    print("-" * 30)
    for count in test_cases:
        print(f"{count:>15} -> {format_follower_count(count)}")
    
    # 测试状态函数
    print("\n状态函数测试:")
    print("-" * 30)
    print(f"在线状态: {get_live_status_text(True)} {get_live_status_symbol(True)}")
    print(f"离线状态: {get_live_status_text(False)} {get_live_status_symbol(False)}")
