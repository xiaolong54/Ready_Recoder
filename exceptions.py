"""
统一异常定义模块
提供项目内所有自定义异常类

异常层次结构:
- BaseException (Python内置)
  └─ AppException (应用异常基类)
     ├─ PlatformException (平台相关异常)
     │  ├─ PlatformNotFoundError (平台不存在)
     │  ├─ PlatformAPIError (API请求错误)
     │  └─ PlatformUnsupportedError (平台不支持)
     ├─ RoomException (房间相关异常)
     │  ├─ RoomNotFoundError (房间不存在)
     │  ├─ RoomAlreadyExistsException (房间已存在)
     │  └─ RoomOperationException (房间操作失败)
     ├─ URLException (URL相关异常)
     │  ├─ URLParseError (URL解析错误)
     │  └─ URLValidationError (URL验证失败)
     ├─ RecordingException (录制相关异常)
     │  ├─ RecordingStartError (录制启动失败)
     │  ├─ RecordingStopError (录制停止失败)
     │  └─ RecordingTimeoutError (录制超时)
     ├─ ConfigException (配置相关异常)
     │  ├─ ConfigLoadError (配置加载失败)
     │  └─ ConfigValidationError (配置验证失败)
     └─ SearchException (搜索相关异常)
        ├─ SearchNoResultError (无搜索结果)
        └─ SearchAPIError (搜索API错误)
"""

import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ErrorContext:
    """错误上下文信息"""
    timestamp: datetime = field(default_factory=datetime.now)
    operation: str = ""
    platform: Optional[str] = None
    room_id: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "operation": self.operation,
            "platform": self.platform,
            "room_id": self.room_id,
            "extra_data": self.extra_data,
        }


class AppException(Exception):
    """应用异常基类
    
    所有自定义异常的基类,提供统一的异常处理接口
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        details: Optional[str] = None,
        context: Optional[ErrorContext] = None,
        inner_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        self.context = context or ErrorContext()
        self.inner_exception = inner_exception
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式,用于API响应和日志"""
        result = {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }
        
        if self.context:
            result["context"] = self.context.to_dict()
        
        if self.inner_exception:
            result["inner_exception"] = str(self.inner_exception)
        
        return result
    
    def get_user_message(self) -> str:
        """获取用户友好的错误消息"""
        msg = self.message
        if self.details:
            msg += f"\n\n{self.details}"
        return msg
    
    def get_log_message(self) -> str:
        """获取日志消息"""
        parts = [f"[{self.__class__.__name__}]"]
        
        if self.context.platform:
            parts.append(f"Platform: {self.context.platform}")
        if self.context.room_id:
            parts.append(f"Room: {self.context.room_id}")
        if self.context.operation:
            parts.append(f"Operation: {self.context.operation}")
        
        parts.append(f"Message: {self.message}")
        
        return " | ".join(parts)


# ==================== 平台相关异常 ====================

class PlatformException(AppException):
    """平台相关异常基类"""
    
    def __init__(
        self,
        platform: str,
        message: str,
        error_code: Optional[int] = None,
        details: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.platform = platform
        super().__init__(message, error_code, details, context, **kwargs)
        self.platform = platform


class PlatformNotFoundError(PlatformException):
    """平台不存在异常"""
    
    def __init__(self, platform: str, **kwargs):
        super().__init__(
            platform=platform,
            message=f"不支持的平台: {platform}",
            error_code=4001,
            **kwargs
        )
    
    def get_user_message(self) -> str:
        supported = ["douyin", "bilibili", "douyu", "huya", "kuaishou"]
        return (
            f"不支持的平台: {self.platform}\n\n"
            f"当前支持的平台:\n"
            f"{', '.join(supported)}\n\n"
            f"建议: 请检查平台名称是否正确"
        )


class PlatformAPIError(PlatformException):
    """平台API请求异常"""
    
    def __init__(
        self,
        platform: str,
        endpoint: str,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
        **kwargs
    ):
        details = f"Endpoint: {endpoint}"
        if status_code:
            details += f"\nStatus Code: {status_code}"
        
        context = kwargs.pop('context', None) or ErrorContext()
        context.extra_data.update({
            "endpoint": endpoint,
            "status_code": status_code,
            "response_data": response_data
        })
        
        super().__init__(
            platform=platform,
            message=message,
            error_code=4100 if status_code != status_code else status_code,
            details=details,
            context=context,
            **kwargs
        )
        
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_data = response_data or {}
    
    def get_user_message(self) -> str:
        msg = f"{self.platform} 平台API请求失败\n\n"
        
        if self.status_code == 404:
            msg += (
                "未找到相关内容\n\n"
                "可能原因:\n"
                "1. 房间ID不正确\n"
                "2. 直播间不存在\n"
                "3. 直播间已被封禁\n\n"
                "建议: 请检查房间ID是否正确"
            )
        elif self.status_code == 403:
            msg += (
                "API访问受限\n\n"
                "可能原因:\n"
                "1. 需要登录才能访问\n"
                "2. 直播间已设置隐私\n\n"
                "建议: 请尝试使用其他方式添加"
            )
        elif self.status_code and self.status_code >= 500:
            msg += (
                "平台服务器错误\n\n"
                f"状态码: {self.status_code}\n\n"
                "建议: 请稍后重试"
            )
        else:
            msg += f"{self.message}"
        
        return msg


# ==================== 房间相关异常 ====================

class RoomException(AppException):
    """房间相关异常基类"""
    
    def __init__(
        self,
        platform: Optional[str],
        room_id: Optional[str],
        message: str,
        error_code: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.platform = platform
        context.room_id = room_id
        super().__init__(message, error_code, context=context, **kwargs)


class RoomNotFoundError(RoomException):
    """房间不存在异常"""
    
    def __init__(
        self,
        platform: Optional[str],
        room_id: Optional[str],
        **kwargs
    ):
        super().__init__(
            platform=platform,
            room_id=room_id,
            message=f"房间不存在: {platform}/{room_id}",
            error_code=3001,
            **kwargs
        )
    
    def get_user_message(self) -> str:
        return (
            f"房间不存在\n\n"
            f"平台: {self.context.platform}\n"
            f"房间ID: {self.context.room_id}\n\n"
            f"该直播间不在监控列表中"
        )


class RoomAlreadyExistsException(RoomException):
    """房间已存在异常"""
    
    def __init__(
        self,
        platform: str,
        room_id: str,
        **kwargs
    ):
        super().__init__(
            platform=platform,
            room_id=room_id,
            message=f"房间已存在: {platform}/{room_id}",
            error_code=3002,
            **kwargs
        )
    
    def get_user_message(self) -> str:
        return (
            f"房间已存在\n\n"
            f"平台: {self.context.platform}\n"
            f"房间ID: {self.context.room_id}\n\n"
            f"该直播间已在监控列表中"
        )


class RoomOperationException(RoomException):
    """房间操作失败异常"""
    
    def __init__(
        self,
        platform: str,
        room_id: str,
        operation: str,
        reason: str,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.operation = operation
        super().__init__(
            platform=platform,
            room_id=room_id,
            message=f"房间操作失败: {operation}",
            details=reason,
            error_code=3003,
            context=context,
            **kwargs
        )
        
        self.operation = operation
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"{self.operation} 失败\n\n"
            f"平台: {self.context.platform}\n"
            f"房间ID: {self.context.room_id}\n\n"
            f"原因: {self.reason}"
        )


# ==================== URL相关异常 ====================

class URLException(AppException):
    """URL相关异常基类"""
    
    def __init__(
        self,
        url: str,
        message: str,
        error_code: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.extra_data["url"] = url
        super().__init__(message, error_code, context=context, **kwargs)
        self.url = url


class URLParseError(URLException):
    """URL解析错误"""
    
    def __init__(self, url: str, reason: str, **kwargs):
        super().__init__(
            url=url,
            message=f"URL解析失败: {url}",
            details=reason,
            error_code=2001,
            **kwargs
        )
        
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"URL解析失败\n\n"
            f"URL: {self.url}\n\n"
            f"原因: {self.reason}\n\n"
            f"建议:\n"
            f"1. 检查URL格式是否正确\n"
            f"2. 确保是支持的直播平台\n"
            f"3. 尝试使用房间ID添加"
        )


class URLValidationError(URLException):
    """URL验证错误"""
    
    def __init__(self, url: str, reason: str, **kwargs):
        super().__init__(
            url=url,
            message=f"URL验证失败: {url}",
            details=reason,
            error_code=2002,
            **kwargs
        )
        
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"URL验证失败\n\n"
            f"URL: {self.url}\n\n"
            f"原因: {self.reason}\n\n"
            f"建议: 请检查URL是否正确"
        )


# ==================== 录制相关异常 ====================

class RecordingException(AppException):
    """录制相关异常基类"""
    
    def __init__(
        self,
        platform: str,
        room_id: str,
        message: str = "",
        error_code: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.platform = platform
        context.room_id = room_id
        super().__init__(message, error_code, context=context, **kwargs)


class RecordingStartError(RecordingException):
    """录制启动失败异常"""
    
    def __init__(
        self,
        platform: str,
        room_id: str,
        reason: str,
        **kwargs
    ):
        super().__init__(
            platform=platform,
            room_id=room_id,
            message=f"录制启动失败",
            details=reason,
            error_code=5001,
            **kwargs
        )
        
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"录制启动失败\n\n"
            f"平台: {self.context.platform}\n"
            f"房间ID: {self.context.room_id}\n\n"
            f"原因: {self.reason}\n\n"
            f"建议:\n"
            f"1. 检查直播间是否在直播\n"
            f"2. 检查网络连接\n"
            f"3. 检查录制路径权限"
        )


class RecordingStopError(RecordingException):
    """录制停止失败异常"""
    
    def __init__(
        self,
        platform: str,
        room_id: str,
        reason: str,
        **kwargs
    ):
        super().__init__(
            platform=platform,
            room_id=room_id,
            message=f"录制停止失败",
            details=reason,
            error_code=5002,
            **kwargs
        )
        
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"录制停止失败\n\n"
            f"平台: {self.context.platform}\n"
            f"房间ID: {self.context.room_id}\n\n"
            f"原因: {self.reason}"
        )


class RecordingTimeoutError(RecordingException):
    """录制超时异常"""
    
    def __init__(
        self,
        platform: str,
        room_id: str,
        timeout_seconds: int,
        **kwargs
    ):
        super().__init__(
            platform=platform,
            room_id=room_id,
            message=f"录制超时",
            details=f"超过{timeout_seconds}秒未收到数据",
            error_code=5003,
            **kwargs
        )
        
        self.timeout_seconds = timeout_seconds
    
    def get_user_message(self) -> str:
        return (
            f"录制超时\n\n"
            f"平台: {self.context.platform}\n"
            f"房间ID: {self.context.room_id}\n\n"
            f"原因: 超过{self.timeout_seconds}秒未收到数据\n\n"
            f"建议:\n"
            f"1. 检查网络连接\n"
            f"2. 检查直播间是否正常直播"
        )


# ==================== 配置相关异常 ====================

class ConfigException(AppException):
    """配置相关异常基类"""
    
    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        error_code: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        if config_file:
            context.extra_data["config_file"] = config_file
        super().__init__(message, error_code, context=context, **kwargs)


class ConfigLoadError(ConfigException):
    """配置加载失败异常"""
    
    def __init__(
        self,
        config_file: str,
        reason: str,
        **kwargs
    ):
        super().__init__(
            message=f"配置加载失败",
            config_file=config_file,
            details=reason,
            error_code=6001,
            **kwargs
        )
        
        self.config_file = config_file
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"配置加载失败\n\n"
            f"文件: {self.config_file}\n\n"
            f"原因: {self.reason}\n\n"
            f"建议: 请检查配置文件是否存在且格式正确"
        )


class ConfigValidationError(ConfigException):
    """配置验证失败异常"""
    
    def __init__(
        self,
        field: str,
        reason: str,
        **kwargs
    ):
        super().__init__(
            message=f"配置验证失败",
            details=f"字段: {field}\n原因: {reason}",
            error_code=6002,
            **kwargs
        )
        
        self.field = field
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"配置验证失败\n\n"
            f"字段: {self.field}\n\n"
            f"原因: {self.reason}\n\n"
            f"建议: 请检查配置文件中的该字段"
        )


# ==================== 搜索相关异常 ====================

class SearchException(AppException):
    """搜索相关异常基类"""
    
    def __init__(
        self,
        platform: str,
        message: str,
        error_code: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.platform = platform
        super().__init__(message, error_code, context=context, **kwargs)


class SearchNoResultError(SearchException):
    """无搜索结果异常"""
    
    def __init__(
        self,
        platform: str,
        query: str,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.extra_data["query"] = query
        context.operation = "search"
        
        super().__init__(
            platform=platform,
            message=f"无搜索结果",
            details=f"查询: {query}",
            error_code=7001,
            context=context,
            **kwargs
        )
        
        self.query = query
    
    def get_user_message(self) -> str:
        return (
            f"无搜索结果\n\n"
            f"平台: {self.context.platform}\n"
            f"查询: {self.query}\n\n"
            f"建议:\n"
            f"1. 尝试使用不同的关键词\n"
            f"2. 检查查询是否正确\n"
            f"3. 使用房间ID直接添加"
        )


class SearchAPIError(SearchException):
    """搜索API异常"""
    
    def __init__(
        self,
        platform: str,
        query: str,
        reason: str,
        **kwargs
    ):
        context = kwargs.pop('context', None) or ErrorContext()
        context.extra_data["query"] = query
        context.operation = "search"
        
        super().__init__(
            platform=platform,
            message=f"搜索失败",
            details=reason,
            error_code=7002,
            context=context,
            **kwargs
        )
        
        self.query = query
        self.reason = reason
    
    def get_user_message(self) -> str:
        return (
            f"搜索失败\n\n"
            f"平台: {self.context.platform}\n"
            f"查询: {self.query}\n\n"
            f"原因: {self.reason}\n\n"
            f"建议: 请稍后重试"
        )


# ==================== 结果封装类 ====================

@dataclass
class OperationResult:
    """操作结果封装
    
    统一封装操作结果,成功或失败
    """
    success: bool
    message: str = ""
    data: Optional[Any] = None
    error: Optional[AppException] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'success': self.success,
            'message': self.message,
            'data': self.data,
        }
        
        if self.error:
            if isinstance(self.error, AppException):
                result['error'] = self.error.to_dict()
            else:
                result['error'] = str(self.error)
        
        return result
    
    def get_user_message(self) -> str:
        """获取用户友好的消息"""
        if self.success:
            return self.message or "操作成功"
        else:
            if self.error and isinstance(self.error, AppException):
                return self.error.get_user_message()
            return self.message or "操作失败"
    
    @classmethod
    def success_result(cls, message: str = "操作成功", data: Any = None) -> "OperationResult":
        """创建成功结果"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def failure_result(cls, error: AppException, message: str = None) -> "OperationResult":
        """创建失败结果"""
        return cls(
            success=False,
            message=message or error.message,
            error=error
        )


# ==================== 异常处理工具 ====================

class ExceptionHandler:
    """异常处理器
    
    提供统一的异常处理功能
    """
    
    @staticmethod
    def handle_exception(
        error: Exception,
        show_traceback: bool = False,
        logger=None
    ) -> str:
        """
        处理异常,返回用户友好的消息
        
        Args:
            error: 异常对象
            show_traceback: 是否显示堆栈跟踪
            logger: 日志记录器
            
        Returns:
            用户友好的错误消息
        """
        # 记录日志
        if logger:
            if isinstance(error, AppException):
                logger.error(error.get_log_message())
            else:
                logger.error(f"Unexpected error: {str(error)}")
        
        # 获取用户消息
        if isinstance(error, AppException):
            user_message = error.get_user_message()
        else:
            user_message = str(error)
        
        # 添加堆栈跟踪
        if show_traceback:
            traceback_str = traceback.format_exc()
            user_message += f"\n\nStack Trace:\n{traceback_str}"
        
        return user_message
    
    @staticmethod
    def wrap_exception(
        error: Exception,
        new_exception_class: type,
        **kwargs
    ) -> AppException:
        """
        包装异常为应用异常
        
        Args:
            error: 原始异常
            new_exception_class: 新异常类
            **kwargs: 新异常的构造参数
            
        Returns:
            包装后的应用异常
        """
        if isinstance(error, AppException):
            return error
        
        # 移除message参数,因为RecordingException不需要message参数
        kwargs.pop('message', None)
        
        return new_exception_class(
            inner_exception=error,
            **kwargs
        )
    
    @staticmethod
    def create_error_context(
        operation: str = "",
        platform: Optional[str] = None,
        room_id: Optional[str] = None,
        **extra_data
    ) -> ErrorContext:
        """
        创建错误上下文
        
        Args:
            operation: 操作名称
            platform: 平台名称
            room_id: 房间ID
            **extra_data: 额外数据
            
        Returns:
            错误上下文对象
        """
        return ErrorContext(
            operation=operation,
            platform=platform,
            room_id=room_id,
            extra_data=extra_data
        )


# ==================== 向后兼容 ====================

# 保留旧的异常类名以保持向后兼容
PlatformError = PlatformAPIError
URLError = URLParseError
APIError = PlatformAPIError
RoomAlreadyExistsError = RoomAlreadyExistsException

# 旧的AddRoomResult,使用OperationResult代替
class AddRoomResult(OperationResult):
    """添加房间结果封装(向后兼容)"""
    
    def __init__(self, success: bool, data=None, error: Exception = None):
        if success:
            if isinstance(data, list) and len(data) > 0:
                message = f"成功找到{len(data)}个直播间" if len(data) > 1 else "成功找到1个直播间"
            else:
                message = "操作成功"
        else:
            message = "操作失败"
        
        # 转换为新的异常类型
        new_error = None
        if error:
            if isinstance(error, AppException):
                new_error = error
            elif isinstance(error, (PlatformError, URLError, APIError, RoomAlreadyExistsError)):
                # 已经是兼容的异常类型
                new_error = error
            else:
                # 包装为通用异常
                new_error = AppException(str(error))
        
        super().__init__(success, message, data, new_error)


# 旧的错误处理函数,使用ExceptionHandler代替
def handle_error(error: Exception, title: str = "错误", logger=None) -> str:
    """
    统一错误处理函数(向后兼容)
    
    Args:
        error: 异常对象
        title: 对话框标题(已弃用)
        logger: 日志记录器
        
    Returns:
        用户友好的错误消息
    """
    return ExceptionHandler.handle_exception(error, logger=logger)


if __name__ == "__main__":
    # 测试异常类
    print("测试异常类:")
    print("=" * 60)
    
    # 测试 PlatformAPIError
    try:
        raise PlatformAPIError(
            platform="douyin",
            endpoint="/room/info",
            message="API返回错误",
            status_code=500,
            response_data={"error": "internal error"}
        )
    except PlatformAPIError as e:
        print(f"\n异常消息: {e}")
        print(f"用户消息:\n{e.get_user_message()}")
        print(f"日志消息: {e.get_log_message()}")
        print(f"字典格式: {e.to_dict()}")
    
    print("\n" + "=" * 60)
    
    # 测试 URLParseError
    try:
        raise URLParseError(
            url="https://invalid-url.com",
            reason="不支持的域名"
        )
    except URLParseError as e:
        print(f"\n异常消息: {e}")
        print(f"用户消息:\n{e.get_user_message()}")
        print(f"字典格式: {e.to_dict()}")
    
    print("\n" + "=" * 60)
    
    # 测试 RoomAlreadyExistsException
    try:
        raise RoomAlreadyExistsException(
            platform="douyin",
            room_id="123456"
        )
    except RoomAlreadyExistsException as e:
        print(f"\n异常消息: {e}")
        print(f"用户消息:\n{e.get_user_message()}")
        print(f"字典格式: {e.to_dict()}")
    
    print("\n" + "=" * 60)
    
    # 测试 OperationResult
    success_result = OperationResult.success_result(
        message="成功找到1个直播间",
        data=[{"platform": "douyin", "room_id": "123456"}]
    )
    print(f"\n成功结果: {success_result.get_user_message()}")
    print(f"字典格式: {success_result.to_dict()}")
    
    print("\n" + "=" * 60)
    
    fail_result = OperationResult.failure_result(
        error=PlatformAPIError(
            platform="douyin",
            endpoint="/room/info",
            message="未找到直播间",
            status_code=404
        )
    )
    print(f"\n失败结果: {fail_result.get_user_message()}")
    print(f"字典格式: {fail_result.to_dict()}")
    
    print("\n" + "=" * 60)
    
    # 测试 AddRoomResult(向后兼容)
    result = AddRoomResult(
        success=True,
        data=[{"platform": "douyin", "room_id": "123456"}]
    )
    print(f"\nAddRoomResult: {result.get_user_message()}")
    print(f"字典格式: {result.to_dict()}")
    
    print("\n" + "=" * 60)
    
    # 测试 ExceptionHandler
    try:
        raise ValueError("测试异常")
    except Exception as e:
        wrapped = ExceptionHandler.wrap_exception(
            e,
            RecordingStartError,
            platform="douyin",
            room_id="123456",
            reason="未知原因"
        )
        print(f"\n包装后的异常: {wrapped}")
        print(f"用户消息:\n{wrapped.get_user_message()}")
    
    print("\n" + "=" * 60)
    
    # 测试 ErrorContext
    context = ExceptionHandler.create_error_context(
        operation="add_room",
        platform="douyin",
        room_id="123456",
        extra={"test": "value"}
    )
    print(f"\n错误上下文: {context.to_dict()}")
    
    print("\n" + "=" * 60)
    print("所有测试通过!")
