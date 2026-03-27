# 重构计划 - 基于StreamCap架构

## 概述

参考StreamCap架构,对SocialMediaCut直播录制系统进行完整的架构重构,实现模块化、插件化、可扩展的设计,仅保留国内直播平台(抖音、B站、斗鱼)。

## 重构目标

1. **清晰的分层架构**: 核心层、平台层、服务层、UI层
2. **插件化平台支持**: 易于添加新平台
3. **统一的数据模型**: 使用dataclass定义数据结构
4. **业务逻辑分离**: 服务层独立,便于测试和维护
5. **依赖注入**: 降低模块间耦合

## 架构设计

### 1. 核心层 (Core)

#### models.py
- **目的**: 定义统一的数据模型
- **包含**:
  - `PlatformType`: 平台类型枚举
  - `LiveStatus`: 直播状态枚举
  - `StreamerInfo`: 主播信息
  - `RoomInfo`: 房间信息
  - `StreamInfo`: 流媒体信息
  - `RecordingTask`: 录制任务
  - `MonitoredRoom`: 监控房间
  - `SearchResult`: 搜索结果
  - `OperationResult`: 操作结果

### 2. 平台层 (Platforms)

#### platforms/base.py
- **接口**: `IPlatformParser`
- **基类**: `BasePlatformParser`
- **功能**: 定义平台解析器接口和通用功能

#### platforms/douyin.py
- **实现**: `DouyinParser`
- **功能**: 抖音平台URL解析、房间信息获取、流信息获取、主播搜索

#### platforms/bilibili.py
- **实现**: `BilibiliParser`
- **功能**: B站平台URL解析、房间信息获取、流信息获取

#### platforms/douyu.py
- **实现**: `DouyuParser`
- **功能**: 斗鱼平台URL解析、房间信息获取、流信息获取

#### platforms/__init__.py
- **注册中心**: `PlatformRegistry`
- **功能**: 统一管理所有平台解析器,提供统一的访问接口

### 3. 服务层 (Services)

#### services/room_service.py
- **类**: `RoomService`
- **职责**:
  - 房间的增删改查
  - 房间状态检查
  - 录制控制
  - 与录制器集成

#### services/search_service.py
- **类**: `SearchService`
- **职责**:
  - URL/ID/名称搜索
  - 开播状态查询
  - 结果去重

#### services/monitor_service.py
- **类**: `MonitorService`
- **职责**:
  - 自动监控循环
  - 状态变化检测
  - 自动录制触发

### 4. 应用层 (Application)

#### app_core.py
- **类**: `LiveRecorderApp`
- **职责**:
  - 整合所有服务
  - 提供统一的API接口
  - 服务生命周期管理

### 5. 表现层 (UI)

#### gui.py (待重构)
- **类**: `DashboardGUI`
- **职责**:
  - 用户界面展示
  - 用户交互处理
  - 调用应用层API

## 关键改进

### 1. 插件化架构
- **之前**: 平台解析逻辑耦合在一起
- **之后**: 每个平台独立实现,通过注册中心管理
- **优势**: 添加新平台只需实现接口并注册

### 2. 统一数据模型
- **之前**: 使用字典传递数据,类型不明确
- **之后**: 使用dataclass,类型安全,有验证
- **优势**: 减少错误,提高代码可读性

### 3. 业务逻辑分离
- **之前**: GUI直接调用底层API
- **之后**: 通过服务层封装
- **优势**: 便于测试,逻辑清晰

### 4. 依赖注入
- **之前**: 模块间直接依赖
- **之后**: 通过构造函数注入
- **优势**: 降低耦合,便于替换实现

## 目录结构

```
socialmedia_cut/
├── models.py                    # 核心数据模型
├── app_core.py                  # 应用程序核心
├── platforms/                   # 平台解析器层
│   ├── __init__.py              # 平台注册中心
│   ├── base.py                  # 基类和接口
│   ├── douyin.py                # 抖音实现
│   ├── bilibili.py              # B站实现
│   └── douyu.py                 # 斗鱼实现
├── services/                    # 服务层
│   ├── __init__.py
│   ├── room_service.py          # 房间管理服务
│   ├── search_service.py       # 搜索服务
│   └── monitor_service.py       # 监控服务
├── config_manager.py           # 配置管理
├── recorder_core.py             # 录制核心
├── api_client.py                # API客户端
├── url_utils.py                 # URL工具
├── utils.py                     # 通用工具
├── exceptions.py                # 异常定义
├── gui.py                       # GUI(待重构)
├── main.py                      # 主入口(待重构)
└── config.yaml                  # 配置文件
```

## 实施计划

### Phase 1: 核心层 ✅
- [x] 创建models.py,定义所有数据模型

### Phase 2: 平台层 ✅
- [x] 创建platforms/base.py,定义接口和基类
- [x] 创建platforms/douyin.py,实现抖音平台
- [x] 创建platforms/bilibili.py,实现B站平台
- [x] 创建platforms/douyu.py,实现斗鱼平台
- [x] 创建platforms/__init__.py,实现注册中心

### Phase 3: 服务层 ✅
- [x] 创建services/room_service.py,实现房间管理
- [x] 创建services/search_service.py,实现搜索功能
- [x] 创建services/monitor_service.py,实现监控功能

### Phase 4: 应用层 ✅
- [x] 创建app_core.py,整合所有服务

### Phase 5: GUI层 (进行中)
- [ ] 重构gui.py,使用新架构
- [ ] 实现MVC模式分离

### Phase 6: 主入口 (待完成)
- [ ] 重构main.py,使用新架构

### Phase 7: 测试 (待完成)
- [ ] 更新测试文件
- [ ] 添加新架构的单元测试

## 使用示例

### 添加房间
```python
from app_core import LiveRecorderApp

app = LiveRecorderApp()

# 通过平台和ID添加
app.add_room("douyin", "123456", "测试房间")

# 通过URL添加
app.add_room_by_url("https://live.douyin.com/789012", "URL测试")
```

### 搜索直播间
```python
# 搜索主播
results = app.search_targets("douyin", "测试", limit=20)

# 通过URL搜索
results = app.search_targets("", "https://live.douyin.com/123456")
```

### 控制录制
```python
# 开始录制
app.start_recording("douyin", "123456")

# 停止录制
app.stop_recording("douyin", "123456")
```

### 自动监控
```python
# 启动监控
app.start_monitor()

# 停止监控
app.stop_monitor()
```

## 兼容性说明

新架构保持了与旧API的兼容性,可以平滑迁移:

1. **房间管理**: 方法签名保持不变
2. **搜索功能**: 返回格式保持兼容
3. **录制控制**: 接口保持一致
4. **监控功能**: 行为保持一致

## 测试建议

1. **单元测试**: 为每个服务类编写单元测试
2. **集成测试**: 测试服务间的协作
3. **平台测试**: 测试各平台解析器的正确性
4. **性能测试**: 测试并发监控的性能

## 后续优化方向

1. **添加更多平台**: 虎牙、快手等
2. **缓存机制**: 缓存房间信息,减少API请求
3. **重试机制**: 添加请求重试,提高可靠性
4. **日志系统**: 完善日志记录
5. **配置验证**: 添加配置项验证
6. **性能监控**: 添加性能指标收集

## 总结

本次重构实现了:
- ✅ 清晰的分层架构
- ✅ 插件化平台支持
- ✅ 统一的数据模型
- ✅ 业务逻辑分离
- ✅ 降低模块耦合

新架构为后续功能扩展和维护打下了坚实基础。
