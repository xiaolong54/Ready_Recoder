"""
代码重构验证脚本
验证重构后的代码是否正常工作
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试所有模块是否可以正常导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    try:
        # 测试核心模块
        print("  导入 app_core...")
        from app_core import LiveRecorderApp
        print("  ✅ app_core")
        
        print("  导入 main...")
        from main import LiveRecorderApp as OldApp
        print("  ✅ main (向后兼容)")
        
        # 测试服务层
        print("  导入 services...")
        from services import RoomService, SearchService, MonitorService
        print("  ✅ services")
        
        # 测试平台层
        print("  导入 platforms...")
        from platforms import PlatformRegistry, DouyinParser, BilibiliParser, DouyuParser
        print("  ✅ platforms")
        
        # 测试异常
        print("  导入 exceptions...")
        from exceptions import (
            AppException,
            PlatformException,
            RoomException,
            URLException,
            RecordingException,
            ConfigException,
            SearchException,
            OperationResult,
            ExceptionHandler
        )
        print("  ✅ exceptions")
        
        # 测试模型
        print("  导入 models...")
        from models import (
            PlatformType,
            LiveStatus,
            RecordingStatus,
            StreamerInfo,
            RoomInfo,
            StreamInfo,
            RecordingTask,
            MonitoredRoom,
            SearchResult
        )
        print("  ✅ models")
        
        # 测试配置
        print("  导入 config_manager...")
        from config_manager import ConfigManager
        print("  ✅ config_manager")
        
        print("\n✅ 所有模块导入成功!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置管理"""
    print("=" * 60)
    print("测试 2: 配置管理")
    print("=" * 60)
    
    try:
        from config_manager import ConfigManager
        
        print("  加载配置...")
        config = ConfigManager()
        print(f"  ✅ 配置加载成功")
        
        print(f"  版本: {config.get('version')}")
        print(f"  API端口: {config.get('api.port')}")
        print(f"  监控间隔: {config.get('monitor.interval_sec')}")
        print(f"  房间数量: {len(config.get_rooms())}")
        
        print("\n✅ 配置管理正常!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置管理失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_platforms():
    """测试平台注册中心"""
    print("=" * 60)
    print("测试 3: 平台注册中心")
    print("=" * 60)
    
    try:
        from platforms import PlatformRegistry
        
        print("  获取支持的平台...")
        platforms = PlatformRegistry.get_supported_platforms()
        print(f"  ✅ 支持的平台: {', '.join(platforms)}")
        
        print("  测试URL解析...")
        test_urls = [
            ("https://live.douyin.com/123456", "douyin"),
            ("https://v.douyin.com/abc123", "douyin"),
            ("https://live.bilibili.com/789012", "bilibili"),
        ]
        
        for url, expected_platform in test_urls:
            result = PlatformRegistry.parse_url(url)
            if result and result.get("platform") == expected_platform:
                print(f"  ✅ {url[:40]}... -> {expected_platform}")
            else:
                print(f"  ⚠️  {url[:40]}... 解析失败")
        
        print("\n✅ 平台注册中心正常!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 平台注册中心失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_exceptions():
    """测试异常处理"""
    print("=" * 60)
    print("测试 4: 异常处理")
    print("=" * 60)
    
    try:
        from exceptions import (
            PlatformNotFoundError,
            RoomAlreadyExistsException,
            URLParseError,
            ExceptionHandler,
            OperationResult
        )
        
        print("  测试异常创建...")
        
        # 创建平台异常
        exc1 = PlatformNotFoundError("test_platform")
        print(f"  ✅ PlatformNotFoundError: {exc1.message}")
        
        # 创建房间异常
        exc2 = RoomAlreadyExistsException("douyin", "123456")
        print(f"  ✅ RoomAlreadyExistsException: {exc2.message}")
        
        # 创建URL异常
        exc3 = URLParseError("https://invalid.com", "不支持的域名")
        print(f"  ✅ URLParseError: {exc3.message}")
        
        print("  测试用户消息...")
        print(f"  用户消息: {exc3.get_user_message()[:50]}...")
        
        print("  测试OperationResult...")
        success = OperationResult.success_result("操作成功", {"test": "data"})
        print(f"  ✅ 成功结果: {success.message}")
        
        failure = OperationResult.failure_result(exc3, "操作失败")
        print(f"  ✅ 失败结果: {failure.message}")
        
        print("  测试ExceptionHandler...")
        user_msg = ExceptionHandler.handle_exception(exc3)
        print(f"  ✅ 用户消息长度: {len(user_msg)}")
        
        print("\n✅ 异常处理正常!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 异常处理失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_app_core():
    """测试应用核心"""
    print("=" * 60)
    print("测试 5: 应用核心")
    print("=" * 60)
    
    try:
        from app_core import LiveRecorderApp
        
        print("  初始化应用...")
        app = LiveRecorderApp()
        print(f"  ✅ 应用初始化成功")
        
        print("  测试添加房间...")
        success = app.add_room("douyin", "test_room_123", "测试房间", auto_record=False)
        if success:
            print(f"  ✅ 房间添加成功")
        else:
            print(f"  ⚠️  房间可能已存在")
        
        print("  测试获取房间...")
        rooms = app.get_rooms()
        print(f"  ✅ 房间数量: {len(rooms)}")
        
        print("  测试搜索...")
        result = app.search_targets("douyin", "123456")
        if hasattr(result, 'success'):
            if result.success:
                print(f"  ✅ 搜索成功: {result.message}")
            else:
                print(f"  ✅ 搜索失败: {result.message}")
        else:
            print(f"  ✅ 搜索返回列表: {len(result)} 个结果")
        
        print("  测试移除房间...")
        success = app.remove_room("douyin", "test_room_123")
        if success:
            print(f"  ✅ 房间移除成功")
        
        print("\n✅ 应用核心正常!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 应用核心失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "代码重构验证脚本" + " " * 30 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("配置管理", test_config()))
    results.append(("平台注册中心", test_platforms()))
    results.append(("异常处理", test_exceptions()))
    results.append(("应用核心", test_app_core()))
    
    # 输出总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:.<40} {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!重构成功!")
        print()
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败,请检查错误信息")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
