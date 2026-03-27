"""
重构功能测试
测试URL解析、异常处理和搜索功能
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from exceptions import PlatformError, URLError, APIError, AddRoomResult
from url_utils import (
    normalize_url,
    parse_douyin_url,
    parse_bilibili_url,
    parse_douyu_url,
    parse_live_url,
    is_valid_url,
    is_room_id,
    build_live_url,
)


class TestExceptions:
    """测试异常类"""
    
    def test_platform_error(self):
        """测试PlatformError"""
        error = PlatformError("douyin", "API返回错误", 500, "详细错误信息")
        
        assert error.platform == "douyin"
        assert error.message == "API返回错误"
        assert error.code == 500
        assert error.details == "详细错误信息"
        
        # 测试to_dict
        error_dict = error.to_dict()
        assert error_dict['platform'] == 'douyin'
        assert error_dict['code'] == 500
        
        # 测试get_user_message
        user_msg = error.get_user_message()
        assert "系统错误" in user_msg
    
    def test_platform_error_404(self):
        """测试404错误"""
        error = PlatformError("douyin", "未找到直播间", 404)
        user_msg = error.get_user_message()
        assert "未找到匹配的直播间" in user_msg
        assert "房间ID" in user_msg
    
    def test_platform_error_403(self):
        """测试403错误"""
        error = PlatformError("douyin", "API验证失败", 403)
        user_msg = error.get_user_message()
        assert "API访问受限" in user_msg
    
    def test_url_error(self):
        """测试URLError"""
        error = URLError("https://invalid-url.com", "不支持的域名")
        assert error.url == "https://invalid-url.com"
        assert error.message == "不支持的域名"
        
        user_msg = error.get_user_message()
        assert "URL解析失败" in user_msg
        assert error.url in user_msg
    
    def test_api_error(self):
        """测试APIError"""
        error = APIError("bilibili", "/room/info", "服务器错误", 500)
        assert error.platform == "bilibili"
        assert error.endpoint == "/room/info"
        assert error.status_code == 500
        
        user_msg = error.get_user_message()
        assert "API请求失败" in user_msg
    
    def test_add_room_result_success(self):
        """测试成功的AddRoomResult"""
        result = AddRoomResult(
            success=True,
            data=[{"platform": "douyin", "room_id": "123456"}]
        )
        
        assert result.success is True
        assert result.data is not None
        assert result.error is None
        
        result_dict = result.to_dict()
        assert result_dict['success'] is True
        assert result_dict['error'] is None
        
        user_msg = result.get_user_message()
        assert "成功" in user_msg
    
    def test_add_room_result_failure(self):
        """测试失败的AddRoomResult"""
        error = PlatformError("douyin", "未找到直播间", 404)
        result = AddRoomResult(
            success=False,
            error=error
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error is not None
        
        result_dict = result.to_dict()
        assert result_dict['success'] is False
        assert result_dict['error'] is not None
        
        user_msg = result.get_user_message()
        assert "未找到匹配的直播间" in user_msg


class TestURLUtils:
    """测试URL工具函数"""
    
    def test_normalize_url(self):
        """测试URL标准化"""
        # 测试添加协议
        assert normalize_url("live.douyin.com/123456") == "https://live.douyin.com/123456"
        
        # 测试移除参数
        url_with_params = "https://live.douyin.com/123456?share_device=xxx&utm_source=web"
        normalized = normalize_url(url_with_params)
        assert "share_device" not in normalized
        assert "utm_source" not in normalized
        
        # 测试保持协议
        assert normalize_url("https://live.bilibili.com/789012") == "https://live.bilibili.com/789012"
    
    def test_parse_douyin_url(self):
        """测试抖音URL解析"""
        assert parse_douyin_url("https://live.douyin.com/123456") == "123456"
        assert parse_douyin_url("https://v.douyin.com/abc123") == "abc123"
        assert parse_douyin_url("https://douyin.com/user/789012") == "789012"
        assert parse_douyin_url("https://www.bilibili.com/123456") is None
    
    def test_parse_bilibili_url(self):
        """测试B站URL解析"""
        assert parse_bilibili_url("https://live.bilibili.com/123456") == "123456"
        assert parse_bilibili_url("https://bilibili.com/123456") == "123456"
        assert parse_bilibili_url("https://live.bilibili.com/live/123456") == "123456"
        assert parse_bilibili_url("https://live.douyin.com/123456") is None
    
    def test_parse_douyu_url(self):
        """测试斗鱼URL解析"""
        assert parse_douyu_url("https://www.douyu.com/123456") == "123456"
        assert parse_douyu_url("https://m.douyu.com/abc123") == "abc123"
        assert parse_douyu_url("https://live.bilibili.com/123456") is None
    
    def test_parse_live_url(self):
        """测试通用URL解析"""
        assert parse_live_url("https://live.douyin.com/123456") == ("douyin", "123456")
        assert parse_live_url("https://live.bilibili.com/789012") == ("bilibili", "789012")
        assert parse_live_url("https://www.douyu.com/abc123") == ("douyu", "abc123")
        assert parse_live_url("https://www.baidu.com") is None
    
    def test_is_valid_url(self):
        """测试URL有效性检查"""
        assert is_valid_url("https://live.douyin.com/123456") is True
        assert is_valid_url("https://live.bilibili.com/789012") is True
        assert is_valid_url("https://www.douyu.com/abc123") is True
        assert is_valid_url("https://www.baidu.com") is False
        assert is_valid_url("invalid-url") is False
    
    def test_is_room_id(self):
        """测试房间ID判断"""
        # 抖音和B站使用数字ID
        assert is_room_id("123456", "douyin") is True
        assert is_room_id("123456", "bilibili") is True
        assert is_room_id("not-an-id", "douyin") is False
        
        # 斗鱼使用字母数字组合
        assert is_room_id("abc123", "douyu") is True
        assert is_room_id("123456", "douyu") is True
        
        # 不指定平台时,默认判断为数字
        assert is_room_id("123456", None) is True
        assert is_room_id("not-an-id", None) is False
    
    def test_build_live_url(self):
        """测试构建直播URL"""
        assert build_live_url("douyin", "123456") == "https://live.douyin.com/123456"
        assert build_live_url("bilibili", "789012") == "https://live.bilibili.com/789012"
        assert build_live_url("douyu", "abc123") == "https://www.douyu.com/abc123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
