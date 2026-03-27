"""
核心数据模型模块
定义项目中使用的所有数据结构
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class PlatformType(str, Enum):
    """支持的平台类型"""
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    DOUYU = "douyu"
    HUYA = "huya"
    KUAISHOU = "kuaishou"


class LiveStatus(str, Enum):
    """直播状态"""
    LIVE = "live"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class RecordingStatus(str, Enum):
    """录制状态"""
    RECORDING = "recording"
    IDLE = "idle"
    ERROR = "error"


@dataclass
class StreamerInfo:
    """主播信息"""
    uid: str
    nickname: str
    avatar: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uid": self.uid,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "follower_count": self.follower_count,
            "following_count": self.following_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamerInfo":
        return cls(
            uid=data.get("uid", ""),
            nickname=data.get("nickname", ""),
            avatar=data.get("avatar"),
            follower_count=data.get("follower_count", 0),
            following_count=data.get("following_count", 0),
        )


@dataclass
class RoomInfo:
    """直播间信息"""
    platform: PlatformType
    room_id: str
    title: str = ""
    streamer: Optional[StreamerInfo] = None
    live_status: LiveStatus = LiveStatus.UNKNOWN
    cover: Optional[str] = None
    url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "room_id": self.room_id,
            "title": self.title,
            "streamer": self.streamer.to_dict() if self.streamer else None,
            "live_status": self.live_status.value,
            "cover": self.cover,
            "url": self.url,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoomInfo":
        streamer_data = data.get("streamer")
        streamer = StreamerInfo.from_dict(streamer_data) if streamer_data else None
        
        return cls(
            platform=PlatformType(data.get("platform", "")),
            room_id=data.get("room_id", ""),
            title=data.get("title", ""),
            streamer=streamer,
            live_status=LiveStatus(data.get("live_status", LiveStatus.UNKNOWN)),
            cover=data.get("cover"),
            url=data.get("url"),
        )
    
    @property
    def streamer_name(self) -> str:
        """获取主播名称"""
        return self.streamer.nickname if self.streamer else ""


@dataclass
class StreamInfo:
    """流媒体信息"""
    platform: PlatformType
    room_id: str
    stream_url: Optional[str] = None
    quality: Optional[str] = None
    real_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "room_id": self.room_id,
            "stream_url": self.stream_url,
            "quality": self.quality,
            "real_url": self.real_url,
        }


@dataclass
class RecordingTask:
    """录制任务"""
    platform: PlatformType
    room_id: str
    recording_id: str
    stream_url: str
    output_dir: str
    filename: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: RecordingStatus = RecordingStatus.IDLE
    file_size: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "room_id": self.room_id,
            "recording_id": self.recording_id,
            "stream_url": self.stream_url,
            "output_dir": self.output_dir,
            "filename": self.filename,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
            "status": self.status.value,
            "file_size": self.file_size,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordingTask":
        start_time = None
        if data.get("start_time"):
            start_time = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M:%S")
        
        end_time = None
        if data.get("end_time"):
            end_time = datetime.strptime(data["end_time"], "%Y-%m-%d %H:%M:%S")
        
        return cls(
            platform=PlatformType(data.get("platform", "")),
            room_id=data.get("room_id", ""),
            recording_id=data.get("recording_id", ""),
            stream_url=data.get("stream_url", ""),
            output_dir=data.get("output_dir", ""),
            filename=data.get("filename", ""),
            start_time=start_time,
            end_time=end_time,
            status=RecordingStatus(data.get("status", RecordingStatus.IDLE)),
            file_size=data.get("file_size", 0),
            error_message=data.get("error_message"),
        )


@dataclass
class MonitoredRoom:
    """监控的直播间"""
    platform: PlatformType
    room_id: str
    name: str = ""
    auto_record: bool = True
    room_info: Optional[RoomInfo] = None
    is_recording: bool = False
    recording_task: Optional[RecordingTask] = None
    last_check_time: Optional[datetime] = None
    check_interval: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "room_id": self.room_id,
            "name": self.name,
            "auto_record": self.auto_record,
            "room_info": self.room_info.to_dict() if self.room_info else None,
            "is_recording": self.is_recording,
            "recording_task": self.recording_task.to_dict() if self.recording_task else None,
            "last_check_time": self.last_check_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_check_time else None,
            "check_interval": self.check_interval,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitoredRoom":
        room_info_data = data.get("room_info")
        room_info = RoomInfo.from_dict(room_info_data) if room_info_data else None
        
        recording_task_data = data.get("recording_task")
        recording_task = RecordingTask.from_dict(recording_task_data) if recording_task_data else None
        
        last_check_time = None
        if data.get("last_check_time"):
            last_check_time = datetime.strptime(data["last_check_time"], "%Y-%m-%d %H:%M:%S")
        
        return cls(
            platform=PlatformType(data.get("platform", "")),
            room_id=data.get("room_id", ""),
            name=data.get("name", ""),
            auto_record=data.get("auto_record", True),
            room_info=room_info,
            is_recording=data.get("is_recording", False),
            recording_task=recording_task,
            last_check_time=last_check_time,
            check_interval=data.get("check_interval", 60),
        )
    
    @property
    def key(self) -> str:
        """获取房间唯一标识"""
        return f"{self.platform.value}:{self.room_id}"
    
    @property
    def is_live(self) -> bool:
        """是否在线"""
        return self.room_info.live_status == LiveStatus.LIVE if self.room_info else False
    
    @property
    def streamer_name(self) -> str:
        """获取主播名称"""
        return self.room_info.streamer_name if self.room_info else ""


@dataclass
class SearchResult:
    """搜索结果"""
    platform: PlatformType
    room_id: str
    nickname: str
    follower_count: int = 0
    is_live: Optional[bool] = None
    source: str = ""  # url/id/name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "room_id": self.room_id,
            "nickname": self.nickname,
            "follower_count": self.follower_count,
            "is_live": self.is_live,
            "source": self.source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        return cls(
            platform=PlatformType(data.get("platform", "")),
            room_id=data.get("room_id", ""),
            nickname=data.get("nickname", ""),
            follower_count=data.get("follower_count", 0),
            is_live=data.get("is_live"),
            source=data.get("source", ""),
        )


@dataclass
class OperationResult:
    """操作结果"""
    success: bool
    message: str = ""
    data: Optional[Any] = None
    error_code: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error_code": self.error_code,
        }


if __name__ == "__main__":
    # 测试数据模型
    print("测试数据模型:")
    print("=" * 60)
    
    # 测试 StreamerInfo
    streamer = StreamerInfo(
        uid="123456",
        nickname="测试主播",
        follower_count=12345678
    )
    print(f"主播信息: {streamer.to_dict()}")
    
    # 测试 RoomInfo
    room = RoomInfo(
        platform=PlatformType.DOUYIN,
        room_id="789012",
        title="测试直播间",
        streamer=streamer,
        live_status=LiveStatus.LIVE
    )
    print(f"房间信息: {room.to_dict()}")
    print(f"主播名称: {room.streamer_name}")
    
    # 测试 MonitoredRoom
    monitored = MonitoredRoom(
        platform=PlatformType.DOUYIN,
        room_id="789012",
        name="监控测试",
        auto_record=True,
        room_info=room
    )
    print(f"监控房间: {monitored.to_dict()}")
    print(f"房间Key: {monitored.key}")
    print(f"是否在线: {monitored.is_live}")
    
    # 测试 OperationResult
    success_result = OperationResult(
        success=True,
        message="操作成功",
        data={"room_id": "789012"}
    )
    print(f"成功结果: {success_result.to_dict()}")
    
    fail_result = OperationResult(
        success=False,
        message="操作失败",
        error_code=500
    )
    print(f"失败结果: {fail_result.to_dict()}")
