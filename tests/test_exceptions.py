"""
测试异常处理体系
验证新的异常架构是否正常工作
"""
import unittest
from exceptions import (
    AppException,
    PlatformException,
    PlatformAPIError,
    PlatformNotFoundError,
    RoomException,
    RoomAlreadyExistsException,
    RoomNotFoundError,
    URLException,
    URLParseError,
    URLValidationError,
    RecordingException,
    RecordingStartError,
    RecordingStopError,
    RecordingTimeoutError,
    ConfigException,
    ConfigLoadError,
    ConfigValidationError,
    SearchException,
    SearchNoResultError,
    SearchAPIError,
    OperationResult,
    ExceptionHandler,
    ErrorContext,
    # 向后兼容
    PlatformError,
    URLError,
    APIError,
    RoomAlreadyExistsError,
    AddRoomResult,
)


class TestExceptionHierarchy(unittest.TestCase):
    """测试异常层次结构"""
    
    def test_app_exception_base(self):
        """测试应用异常基类"""
        exc = AppException(
            message="测试消息",
            error_code=1000,
            details="详细信息"
        )
        self.assertEqual(exc.message, "测试消息")
        self.assertEqual(exc.error_code, 1000)
        self.assertEqual(exc.details, "详细信息")
        self.assertIsInstance(exc.context, ErrorContext)
    
    def test_platform_exception_inheritance(self):
        """测试平台异常继承"""
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/api/test",
            message="API错误",
            status_code=500
        )
        self.assertIsInstance(exc, PlatformException)
        self.assertIsInstance(exc, AppException)
        self.assertEqual(exc.platform, "douyin")
        self.assertEqual(exc.endpoint, "/api/test")
    
    def test_room_exception_inheritance(self):
        """测试房间异常继承"""
        exc = RoomAlreadyExistsException(
            platform="douyin",
            room_id="123456"
        )
        self.assertIsInstance(exc, RoomException)
        self.assertIsInstance(exc, AppException)
        self.assertEqual(exc.context.platform, "douyin")
        self.assertEqual(exc.context.room_id, "123456")


class TestPlatformExceptions(unittest.TestCase):
    """测试平台相关异常"""
    
    def test_platform_not_found(self):
        """测试平台不存在异常"""
        exc = PlatformNotFoundError("unknown_platform")
        self.assertIn("不支持的平台", exc.get_user_message())
        self.assertEqual(exc.error_code, 4001)
    
    def test_platform_api_error_404(self):
        """测试API 404错误"""
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/room/info",
            message="房间不存在",
            status_code=404
        )
        user_msg = exc.get_user_message()
        self.assertIn("未找到相关内容", user_msg)
        # 状态码在extra_data中
        self.assertEqual(exc.context.extra_data.get("status_code"), 404)
    
    def test_platform_api_error_403(self):
        """测试API 403错误"""
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/room/info",
            message="访问受限",
            status_code=403
        )
        user_msg = exc.get_user_message()
        self.assertIn("API访问受限", user_msg)
    
    def test_platform_api_error_500(self):
        """测试API 500错误"""
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/room/info",
            message="服务器错误",
            status_code=500
        )
        user_msg = exc.get_user_message()
        self.assertIn("平台服务器错误", user_msg)
        self.assertIn("稍后重试", user_msg)


class TestRoomExceptions(unittest.TestCase):
    """测试房间相关异常"""
    
    def test_room_not_found(self):
        """测试房间不存在异常"""
        exc = RoomNotFoundError("douyin", "123456")
        user_msg = exc.get_user_message()
        self.assertIn("房间不存在", user_msg)
        self.assertIn("douyin", user_msg)
        self.assertIn("123456", user_msg)
        self.assertEqual(exc.error_code, 3001)
    
    def test_room_already_exists(self):
        """测试房间已存在异常"""
        exc = RoomAlreadyExistsException("douyin", "123456")
        user_msg = exc.get_user_message()
        self.assertIn("房间已存在", user_msg)
        self.assertIn("监控列表中", user_msg)
        self.assertEqual(exc.error_code, 3002)


class TestURLExceptions(unittest.TestCase):
    """测试URL相关异常"""
    
    def test_url_parse_error(self):
        """测试URL解析错误"""
        exc = URLParseError(
            url="https://invalid.com",
            reason="不支持的域名"
        )
        user_msg = exc.get_user_message()
        self.assertIn("URL解析失败", user_msg)
        self.assertIn("不支持的域名", user_msg)
        self.assertEqual(exc.error_code, 2001)
    
    def test_url_validation_error(self):
        """测试URL验证错误"""
        exc = URLValidationError(
            url="invalid-url",
            reason="格式不正确"
        )
        user_msg = exc.get_user_message()
        self.assertIn("URL验证失败", user_msg)
        self.assertEqual(exc.error_code, 2002)


class TestRecordingExceptions(unittest.TestCase):
    """测试录制相关异常"""
    
    def test_recording_start_error(self):
        """测试录制启动失败"""
        exc = RecordingStartError(
            platform="douyin",
            room_id="123456",
            reason="流地址无效"
        )
        user_msg = exc.get_user_message()
        self.assertIn("录制启动失败", user_msg)
        self.assertIn("流地址无效", user_msg)
        self.assertEqual(exc.error_code, 5001)
    
    def test_recording_stop_error(self):
        """测试录制停止失败"""
        exc = RecordingStopError(
            platform="douyin",
            room_id="123456",
            reason="进程不存在"
        )
        user_msg = exc.get_user_message()
        self.assertIn("录制停止失败", user_msg)
        self.assertEqual(exc.error_code, 5002)
    
    def test_recording_timeout_error(self):
        """测试录制超时"""
        exc = RecordingTimeoutError(
            platform="douyin",
            room_id="123456",
            timeout_seconds=30
        )
        user_msg = exc.get_user_message()
        self.assertIn("录制超时", user_msg)
        self.assertIn("30秒", user_msg)
        self.assertEqual(exc.error_code, 5003)


class TestSearchExceptions(unittest.TestCase):
    """测试搜索相关异常"""
    
    def test_search_no_result(self):
        """测试无搜索结果"""
        exc = SearchNoResultError(
            platform="douyin",
            query="test123"
        )
        user_msg = exc.get_user_message()
        self.assertIn("无搜索结果", user_msg)
        self.assertIn("test123", user_msg)
        self.assertIn("使用房间ID直接添加", user_msg)
        self.assertEqual(exc.error_code, 7001)
    
    def test_search_api_error(self):
        """测试搜索API错误"""
        exc = SearchAPIError(
            platform="douyin",
            query="test123",
            reason="网络错误"
        )
        user_msg = exc.get_user_message()
        self.assertIn("搜索失败", user_msg)
        self.assertEqual(exc.error_code, 7002)


class TestOperationResult(unittest.TestCase):
    """测试操作结果封装"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = OperationResult.success_result(
            message="操作成功",
            data={"room_id": "123456"}
        )
        self.assertTrue(result.success)
        self.assertEqual(result.message, "操作成功")
        self.assertEqual(result.data, {"room_id": "123456"})
        self.assertIsNone(result.error)
    
    def test_failure_result(self):
        """测试失败结果"""
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/test",
            message="错误",
            status_code=500
        )
        result = OperationResult.failure_result(exc, message="操作失败")
        self.assertFalse(result.success)
        self.assertEqual(result.message, "操作失败")
        self.assertEqual(result.error, exc)
    
    def test_to_dict(self):
        """测试转换为字典"""
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/test",
            message="错误",
            status_code=500
        )
        result = OperationResult.failure_result(exc)
        d = result.to_dict()
        self.assertIn("success", d)
        self.assertIn("message", d)
        self.assertIn("data", d)
        self.assertIn("error", d)
        self.assertFalse(d["success"])
        self.assertIn("error_type", d["error"])
    
    def test_get_user_message(self):
        """测试获取用户消息"""
        success_result = OperationResult.success_result(
            message="成功",
            data={"test": "data"}
        )
        self.assertEqual(success_result.get_user_message(), "成功")
        
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/test",
            message="错误",
            status_code=404
        )
        fail_result = OperationResult.failure_result(exc)
        user_msg = fail_result.get_user_message()
        self.assertIn("未找到相关内容", user_msg)


class TestExceptionHandler(unittest.TestCase):
    """测试异常处理器"""
    
    def test_handle_app_exception(self):
        """测试处理应用异常"""
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/test",
            message="错误",
            status_code=500
        )
        user_msg = ExceptionHandler.handle_exception(exc)
        self.assertIn("平台服务器错误", user_msg)
    
    def test_handle_generic_exception(self):
        """测试处理普通异常"""
        exc = ValueError("普通错误")
        user_msg = ExceptionHandler.handle_exception(exc)
        self.assertIn("普通错误", user_msg)
    
    def test_wrap_exception(self):
        """测试包装异常"""
        original_exc = ValueError("原始错误")
        wrapped = ExceptionHandler.wrap_exception(
            original_exc,
            RecordingStartError,
            platform="douyin",
            room_id="123456",
            reason="未知"
        )
        self.assertIsInstance(wrapped, RecordingStartError)
        self.assertEqual(wrapped.inner_exception, original_exc)
    
    def test_create_error_context(self):
        """测试创建错误上下文"""
        context = ExceptionHandler.create_error_context(
            operation="add_room",
            platform="douyin",
            room_id="123456",
            test="value"
        )
        self.assertEqual(context.operation, "add_room")
        self.assertEqual(context.platform, "douyin")
        self.assertEqual(context.room_id, "123456")
        self.assertEqual(context.extra_data["test"], "value")


class TestBackwardCompatibility(unittest.TestCase):
    """测试向后兼容性"""
    
    def test_platform_error_alias(self):
        """测试PlatformError别名"""
        exc = PlatformError(
            platform="douyin",
            endpoint="/test",
            message="错误",
            status_code=500
        )
        self.assertIsInstance(exc, PlatformAPIError)
        self.assertIsInstance(exc, PlatformException)
    
    def test_url_error_alias(self):
        """测试URLError别名"""
        exc = URLError(
            url="https://test.com",
            reason="错误"
        )
        self.assertIsInstance(exc, URLParseError)
        self.assertIsInstance(exc, URLException)
    
    def test_room_already_exists_error_alias(self):
        """测试RoomAlreadyExistsError别名"""
        exc = RoomAlreadyExistsError("douyin", "123456")
        self.assertIsInstance(exc, RoomAlreadyExistsException)
        self.assertIsInstance(exc, RoomException)
    
    def test_add_room_result(self):
        """测试AddRoomResult向后兼容"""
        result = AddRoomResult(
            success=True,
            data=[{"platform": "douyin", "room_id": "123456"}]
        )
        self.assertTrue(result.success)
        self.assertIn("1个直播间", result.get_user_message())
        
        exc = PlatformAPIError(
            platform="douyin",
            endpoint="/test",
            message="错误",
            status_code=404
        )
        fail_result = AddRoomResult(success=False, error=exc)
        self.assertFalse(fail_result.success)
        self.assertIn("未找到相关内容", fail_result.get_user_message())


if __name__ == "__main__":
    unittest.main()
