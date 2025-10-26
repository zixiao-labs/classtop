# Named Pipes / IPC 通信设计方案

## 概述

为 Classtop-Management-Server 和 ClassTop 客户端实现**双通道**局域网通信方案：
- **gRPC（主推）**: 现代、高性能、跨平台的 RPC 框架
- **SMB Named Pipes（备选）**: 类似 SQL Server 的传统方案，默认禁用，需在开发者选项中启用

## 背景

### SQL Server Named Pipes 的实现原理

SQL Server 的 "Named Pipes" 网络通信实际上是：
- **本地**: 使用真正的 Named Pipes (`\\.\pipe\sql\query`)
- **远程**: 通过 **SMB/CIFS 协议** (`\\server\pipe\sql\query`)
- **端口**: SMB 使用 TCP 445 端口

### 问题

1. **跨平台复杂**: Linux/macOS 需要 Samba，配置复杂
2. **防火墙**: SMB 端口常被阻止
3. **性能**: SMB 协议开销较大
4. **安全**: SMB 有安全隐患

## 推荐方案

### 方案 1: gRPC（推荐用于局域网）

**优势**:
- ✅ 高性能 (HTTP/2, 二进制协议)
- ✅ 跨语言支持 (Rust, Python, JavaScript)
- ✅ 双向流
- ✅ 内置负载均衡、超时、重试
- ✅ 支持 TLS 加密

**架构**:
```
ClassTop Client (Python)
  ↓ gRPC (HTTP/2)
Management Server (Rust - tonic)
  ↓ gRPC (HTTP/2)
PostgreSQL/MSSQL
```

### 方案 2: Unix Domain Sockets + TCP 混合

**优势**:
- ✅ 本地通信极快 (Unix Sockets)
- ✅ 远程通信简单 (TCP)
- ✅ 轻量级
- ✅ 易于实现

**架构**:
```
本地客户端 → Unix Socket (/tmp/classtop.sock)
远程客户端 → TCP Socket (0.0.0.0:9000)
  ↓
Management Server (Rust)
```

### 方案 3: 增强现有 WebSocket（最简单）

**优势**:
- ✅ 已有实现
- ✅ 无需新依赖
- ✅ 支持二进制帧
- ✅ 双向通信

**改进**:
- 添加二进制协议（MessagePack/CBOR）
- 添加连接池
- 添加心跳机制

### 方案 4: SMB Named Pipes（开发者选项，类似 SQL Server）

**适用场景**:
- 需要与 SQL Server 风格一致的环境
- 纯 Windows 局域网环境
- 已有 SMB 基础设施的企业

**优势**:
- ✅ 与 SQL Server 风格一致
- ✅ Windows 原生支持
- ✅ 熟悉的连接字符串格式

**劣势**:
- ⚠️ 跨平台需要 Samba
- ⚠️ SMB 端口常被防火墙阻止
- ⚠️ 性能开销较大
- ⚠️ 安全隐患

**安全警告**:
```
⚠️ 警告：SMB Named Pipes 默认禁用
- 仅在受信任的局域网环境中启用
- 确保防火墙已正确配置
- 建议仅用于兼容性测试
- 生产环境推荐使用 gRPC + TLS
```

**架构**:
```
ClassTop Client (Python)
  ↓ SMB/CIFS (TCP 445)
  ↓ \\server\pipe\classtop
Management Server (Rust - named pipes)
  ↓
PostgreSQL/MSSQL
```

## 详细设计：方案 1 - gRPC

### 1. 技术栈

**服务端 (Management Server)**:
- `tonic` - Rust gRPC 框架
- `prost` - Protocol Buffers
- `tokio` - 异步运行时

**客户端 (ClassTop)**:
- Python: `grpcio`, `grpcio-tools`
- 或通过 PyO3 调用 Rust gRPC 客户端

### 2. Protocol Buffers 定义

```protobuf
// classtop.proto
syntax = "proto3";

package classtop;

service ClassTopService {
  // 获取客户端列表
  rpc ListClients(ListClientsRequest) returns (ListClientsResponse);

  // 发送命令到客户端
  rpc SendCommand(SendCommandRequest) returns (SendCommandResponse);

  // 双向流：实时同步
  rpc StreamSync(stream SyncMessage) returns (stream SyncMessage);

  // 服务器推送
  rpc Subscribe(SubscribeRequest) returns (stream ServerEvent);
}

message ListClientsRequest {
  int32 page = 1;
  int32 page_size = 2;
}

message ListClientsResponse {
  repeated Client clients = 1;
  int32 total = 2;
}

message Client {
  string uuid = 1;
  string name = 2;
  string ip_address = 3;
  int64 last_seen = 4;
  bool online = 5;
}

message SendCommandRequest {
  string client_uuid = 1;
  string command = 2;
  bytes payload = 3;
}

message SendCommandResponse {
  bool success = 1;
  string message = 2;
  bytes result = 3;
}

message SyncMessage {
  enum MessageType {
    HEARTBEAT = 0;
    DATA_UPDATE = 1;
    COMMAND = 2;
    RESPONSE = 3;
  }

  MessageType type = 1;
  string client_uuid = 2;
  bytes payload = 3;
  int64 timestamp = 4;
}

message SubscribeRequest {
  repeated string event_types = 1;
}

message ServerEvent {
  string event_type = 1;
  bytes payload = 2;
  int64 timestamp = 3;
}
```

### 3. 服务端实现 (Rust)

**Cargo.toml 添加依赖**:
```toml
[dependencies]
tonic = "0.12"
prost = "0.13"
tokio = { version = "1", features = ["full"] }
tokio-stream = "0.1"

[build-dependencies]
tonic-build = "0.12"
```

**build.rs**:
```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::compile_protos("proto/classtop.proto")?;
    Ok(())
}
```

**src/grpc/server.rs**:
```rust
use tonic::{transport::Server, Request, Response, Status};
use tokio::sync::mpsc;
use tokio_stream::wrappers::ReceiverStream;

pub mod classtop {
    tonic::include_proto!("classtop");
}

use classtop::{
    class_top_service_server::{ClassTopService, ClassTopServiceServer},
    *,
};

#[derive(Debug, Default)]
pub struct ClassTopServiceImpl {
    // 数据库连接池
    db: Arc<PgPool>,
    // 客户端连接管理器
    clients: Arc<RwLock<HashMap<String, ClientConnection>>>,
}

#[tonic::async_trait]
impl ClassTopService for ClassTopServiceImpl {
    async fn list_clients(
        &self,
        request: Request<ListClientsRequest>,
    ) -> Result<Response<ListClientsResponse>, Status> {
        let req = request.into_inner();

        // 从数据库查询客户端
        let clients = sqlx::query_as!(
            Client,
            "SELECT uuid, name, ip_address, last_seen, online
             FROM clients
             LIMIT $1 OFFSET $2",
            req.page_size,
            req.page * req.page_size
        )
        .fetch_all(&*self.db)
        .await
        .map_err(|e| Status::internal(e.to_string()))?;

        let total = sqlx::query_scalar!("SELECT COUNT(*) FROM clients")
            .fetch_one(&*self.db)
            .await
            .map_err(|e| Status::internal(e.to_string()))?
            .unwrap_or(0);

        Ok(Response::new(ListClientsResponse {
            clients,
            total: total as i32,
        }))
    }

    async fn send_command(
        &self,
        request: Request<SendCommandRequest>,
    ) -> Result<Response<SendCommandResponse>, Status> {
        let req = request.into_inner();

        // 查找客户端连接
        let clients = self.clients.read().await;
        let client = clients
            .get(&req.client_uuid)
            .ok_or_else(|| Status::not_found("Client not found or offline"))?;

        // 发送命令
        let result = client
            .send_command(&req.command, &req.payload)
            .await
            .map_err(|e| Status::internal(e.to_string()))?;

        Ok(Response::new(SendCommandResponse {
            success: true,
            message: "Command sent successfully".to_string(),
            result,
        }))
    }

    type StreamSyncStream = ReceiverStream<Result<SyncMessage, Status>>;

    async fn stream_sync(
        &self,
        request: Request<tonic::Streaming<SyncMessage>>,
    ) -> Result<Response<Self::StreamSyncStream>, Status> {
        let mut stream = request.into_inner();
        let (tx, rx) = mpsc::channel(128);

        tokio::spawn(async move {
            while let Some(result) = stream.next().await {
                match result {
                    Ok(msg) => {
                        // 处理客户端消息
                        match msg.r#type {
                            0 => {}, // HEARTBEAT
                            1 => {}, // DATA_UPDATE
                            2 => {}, // COMMAND
                            3 => {}, // RESPONSE
                            _ => {},
                        }

                        // 发送响应
                        let response = SyncMessage {
                            r#type: msg.r#type,
                            client_uuid: msg.client_uuid,
                            payload: vec![],
                            timestamp: chrono::Utc::now().timestamp(),
                        };

                        if tx.send(Ok(response)).await.is_err() {
                            break;
                        }
                    }
                    Err(e) => {
                        let _ = tx.send(Err(e)).await;
                        break;
                    }
                }
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }

    type SubscribeStream = ReceiverStream<Result<ServerEvent, Status>>;

    async fn subscribe(
        &self,
        request: Request<SubscribeRequest>,
    ) -> Result<Response<Self::SubscribeStream>, Status> {
        let (tx, rx) = mpsc::channel(128);
        let req = request.into_inner();

        // 订阅事件
        tokio::spawn(async move {
            // 示例：定期发送心跳
            let mut interval = tokio::time::interval(Duration::from_secs(30));

            loop {
                interval.tick().await;

                let event = ServerEvent {
                    event_type: "heartbeat".to_string(),
                    payload: vec![],
                    timestamp: chrono::Utc::now().timestamp(),
                };

                if tx.send(Ok(event)).await.is_err() {
                    break;
                }
            }
        });

        Ok(Response::new(ReceiverStream::new(rx)))
    }
}

pub async fn start_grpc_server(
    addr: &str,
    db: Arc<PgPool>,
) -> Result<(), Box<dyn std::error::Error>> {
    let addr = addr.parse()?;

    let service = ClassTopServiceImpl {
        db,
        clients: Arc::new(RwLock::new(HashMap::new())),
    };

    println!("gRPC server listening on {}", addr);

    Server::builder()
        .add_service(ClassTopServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
```

### 4. 客户端实现 (Python)

**安装依赖**:
```bash
pip install grpcio grpcio-tools
```

**生成 Python 代码**:
```bash
python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./src-tauri/python/tauri_app \
    --grpc_python_out=./src-tauri/python/tauri_app \
    proto/classtop.proto
```

**Python 客户端**:
```python
# src-tauri/python/tauri_app/grpc_client.py
import grpc
import classtop_pb2
import classtop_pb2_grpc
from typing import Optional, List
import asyncio

class ClassTopGrpcClient:
    def __init__(self, server_address: str = "localhost:50051"):
        self.server_address = server_address
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[classtop_pb2_grpc.ClassTopServiceStub] = None

    async def connect(self):
        """连接到 gRPC 服务器"""
        self.channel = grpc.aio.insecure_channel(self.server_address)
        self.stub = classtop_pb2_grpc.ClassTopServiceStub(self.channel)

    async def close(self):
        """关闭连接"""
        if self.channel:
            await self.channel.close()

    async def list_clients(self, page: int = 0, page_size: int = 50):
        """获取客户端列表"""
        request = classtop_pb2.ListClientsRequest(
            page=page,
            page_size=page_size
        )
        response = await self.stub.ListClients(request)
        return response

    async def send_command(
        self,
        client_uuid: str,
        command: str,
        payload: bytes = b""
    ):
        """发送命令到客户端"""
        request = classtop_pb2.SendCommandRequest(
            client_uuid=client_uuid,
            command=command,
            payload=payload
        )
        response = await self.stub.SendCommand(request)
        return response

    async def stream_sync(self):
        """双向流同步"""
        async def request_generator():
            while True:
                # 发送心跳
                yield classtop_pb2.SyncMessage(
                    type=classtop_pb2.SyncMessage.HEARTBEAT,
                    client_uuid="local-client",
                    payload=b"",
                    timestamp=int(time.time())
                )
                await asyncio.sleep(30)

        async for response in self.stub.StreamSync(request_generator()):
            print(f"Received sync message: {response}")

    async def subscribe_events(self, event_types: List[str]):
        """订阅服务器事件"""
        request = classtop_pb2.SubscribeRequest(event_types=event_types)

        async for event in self.stub.Subscribe(request):
            print(f"Received event: {event.event_type}")
            yield event


# 使用示例
async def main():
    client = ClassTopGrpcClient("management-server.local:50051")
    await client.connect()

    try:
        # 获取客户端列表
        clients = await client.list_clients()
        print(f"Total clients: {clients.total}")

        # 发送命令
        if clients.clients:
            response = await client.send_command(
                clients.clients[0].uuid,
                "get_schedule",
                b"{}"
            )
            print(f"Command response: {response}")

        # 订阅事件
        async for event in client.subscribe_events(["schedule_update"]):
            print(f"Event: {event}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 集成到 Management Server

**main.rs**:
```rust
mod grpc;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // 初始化日志
    env_logger::init();

    // 加载配置
    let config = Config::from_env();

    // 数据库连接
    let db_pool = create_db_pool(&config).await?;

    // 启动 gRPC 服务器（独立线程）
    let db_clone = db_pool.clone();
    tokio::spawn(async move {
        if let Err(e) = grpc::start_grpc_server(&config.grpc_addr, db_clone).await {
            eprintln!("gRPC server error: {}", e);
        }
    });

    // 启动 HTTP/WebSocket 服务器
    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(db_pool.clone()))
            // ... 其他路由
    })
    .bind(&config.http_addr)?
    .run()
    .await
}
```

## 详细设计：方案 4 - SMB Named Pipes（开发者选项）

### 1. 技术栈

**服务端 (Management Server)**:
- **Windows**: `named_pipe` crate (Windows 原生)
- **Linux/macOS**: `pamsm` + Samba (SMB 模拟)
- **跨平台推荐**: `interprocess` crate（支持所有平台的 Named Pipes）

**客户端 (ClassTop)**:
- **Windows**: `pywin32` (`win32pipe`, `win32file`)
- **Linux/macOS**: `smbprotocol` (Pure Python SMB 客户端)

### 2. 服务端实现 (Rust - Windows 平台)

**Cargo.toml 添加依赖**:
```toml
[dependencies]
# Windows 原生 Named Pipes
[target.'cfg(windows)'.dependencies]
named_pipe = "0.4"
winapi = { version = "0.3", features = ["winbase", "namedpipeapi", "winerror"] }

# 跨平台方案（推荐）
interprocess = "2.2"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

**src/named_pipes/server.rs (Windows 原生实现)**:
```rust
use std::io::{Read, Write};
use std::sync::Arc;
use tokio::sync::Mutex;
use serde::{Deserialize, Serialize};

#[cfg(windows)]
use named_pipe::PipeOptions;

#[derive(Debug, Serialize, Deserialize)]
pub struct PipeMessage {
    pub command: String,
    pub client_uuid: Option<String>,
    pub payload: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PipeResponse {
    pub success: bool,
    pub message: String,
    pub data: serde_json::Value,
}

#[cfg(windows)]
pub async fn start_named_pipe_server(
    pipe_name: &str,
    db: Arc<PgPool>,
) -> Result<(), Box<dyn std::error::Error>> {
    let pipe_path = format!(r"\\.\pipe\{}", pipe_name);

    println!("⚠️ Named Pipes server starting on {}", pipe_path);
    println!("⚠️ WARNING: This is a compatibility feature. Use gRPC for production.");

    loop {
        // 创建命名管道实例
        let server = PipeOptions::new(&pipe_path)
            .single()? // 单个连接
            .access_inbound(true)
            .access_outbound(true)
            .create()?;

        println!("Waiting for client connection on {}...", pipe_path);

        // 等待客户端连接
        let db_clone = db.clone();
        tokio::task::spawn_blocking(move || {
            if let Err(e) = handle_pipe_client(server, db_clone) {
                eprintln!("Pipe client error: {}", e);
            }
        });
    }
}

#[cfg(windows)]
fn handle_pipe_client(
    mut pipe: named_pipe::PipeServer,
    db: Arc<PgPool>,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut buffer = vec![0u8; 65536]; // 64KB buffer

    loop {
        // 读取客户端请求
        let bytes_read = pipe.read(&mut buffer)?;
        if bytes_read == 0 {
            break; // 客户端断开连接
        }

        let request_data = &buffer[..bytes_read];
        let request: PipeMessage = serde_json::from_slice(request_data)?;

        println!("Received command: {}", request.command);

        // 处理请求
        let response = match request.command.as_str() {
            "list_clients" => {
                // 查询客户端列表（同步版本）
                let clients = futures::executor::block_on(async {
                    sqlx::query!("SELECT uuid, name, ip_address FROM clients")
                        .fetch_all(&*db)
                        .await
                })?;

                PipeResponse {
                    success: true,
                    message: "OK".to_string(),
                    data: serde_json::to_value(clients)?,
                }
            }
            "send_command" => {
                // 发送命令到客户端
                PipeResponse {
                    success: true,
                    message: "Command sent".to_string(),
                    data: serde_json::json!({}),
                }
            }
            _ => {
                PipeResponse {
                    success: false,
                    message: format!("Unknown command: {}", request.command),
                    data: serde_json::json!({}),
                }
            }
        };

        // 发送响应
        let response_data = serde_json::to_vec(&response)?;
        pipe.write_all(&response_data)?;
        pipe.flush()?;
    }

    Ok(())
}

// 非 Windows 平台返回错误
#[cfg(not(windows))]
pub async fn start_named_pipe_server(
    _pipe_name: &str,
    _db: Arc<PgPool>,
) -> Result<(), Box<dyn std::error::Error>> {
    Err("Named Pipes server is only supported on Windows. Use gRPC instead.".into())
}
```

**src/named_pipes/server_cross_platform.rs (跨平台实现)**:
```rust
use interprocess::local_socket::{LocalSocketListener, LocalSocketStream};
use std::io::{Read, Write};
use std::sync::Arc;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct PipeMessage {
    pub command: String,
    pub payload: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PipeResponse {
    pub success: bool,
    pub message: String,
    pub data: serde_json::Value,
}

pub async fn start_cross_platform_pipe_server(
    pipe_name: &str,
    db: Arc<PgPool>,
) -> Result<(), Box<dyn std::error::Error>> {
    // Windows: \\.\pipe\classtop
    // Unix: /tmp/classtop.sock
    let socket_path = if cfg!(windows) {
        format!(r"\\.\pipe\{}", pipe_name)
    } else {
        format!("/tmp/{}.sock", pipe_name)
    };

    println!("⚠️ Cross-platform Named Pipes server starting on {}", socket_path);

    let listener = LocalSocketListener::bind(socket_path)?;

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let db_clone = db.clone();
                tokio::spawn(async move {
                    if let Err(e) = handle_client(stream, db_clone).await {
                        eprintln!("Client error: {}", e);
                    }
                });
            }
            Err(e) => {
                eprintln!("Connection error: {}", e);
            }
        }
    }

    Ok(())
}

async fn handle_client(
    mut stream: LocalSocketStream,
    db: Arc<PgPool>,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut buffer = vec![0u8; 65536];

    loop {
        let bytes_read = stream.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }

        let request: PipeMessage = serde_json::from_slice(&buffer[..bytes_read])?;

        let response = match request.command.as_str() {
            "list_clients" => {
                let clients = sqlx::query!("SELECT uuid, name FROM clients")
                    .fetch_all(&*db)
                    .await?;

                PipeResponse {
                    success: true,
                    message: "OK".to_string(),
                    data: serde_json::to_value(clients)?,
                }
            }
            _ => PipeResponse {
                success: false,
                message: "Unknown command".to_string(),
                data: serde_json::json!({}),
            },
        };

        let response_data = serde_json::to_vec(&response)?;
        stream.write_all(&response_data)?;
        stream.flush()?;
    }

    Ok(())
}
```

### 3. 客户端实现 (Python - Windows)

**安装依赖**:
```bash
# Windows 平台
pip install pywin32

# Linux/macOS 平台（通过 SMB 访问）
pip install smbprotocol
```

**Python 客户端 (Windows 原生)**:
```python
# src-tauri/python/tauri_app/named_pipe_client.py
import win32pipe
import win32file
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NamedPipeClient:
    """Windows Named Pipes 客户端（类似 SQL Server）"""

    def __init__(self, server_name: str = ".", pipe_name: str = "classtop"):
        """
        初始化 Named Pipe 客户端

        Args:
            server_name: 服务器名称或 IP（"." 表示本地）
            pipe_name: 管道名称
        """
        self.pipe_path = f"\\\\{server_name}\\pipe\\{pipe_name}"
        self.handle: Optional[int] = None

    def connect(self, timeout: int = 5000) -> bool:
        """
        连接到 Named Pipe 服务器

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            连接是否成功
        """
        try:
            # 等待命名管道可用
            win32pipe.WaitNamedPipe(self.pipe_path, timeout)

            # 打开管道
            self.handle = win32file.CreateFile(
                self.pipe_path,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,  # no sharing
                None,  # default security
                win32file.OPEN_EXISTING,
                0,  # default attributes
                None  # no template file
            )

            # 设置管道模式
            win32pipe.SetNamedPipeHandleState(
                self.handle,
                win32pipe.PIPE_READMODE_MESSAGE,
                None,
                None
            )

            logger.info(f"Connected to Named Pipe: {self.pipe_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Named Pipe: {e}")
            return False

    def send_command(
        self,
        command: str,
        payload: Dict[str, Any] = None,
        client_uuid: str = None
    ) -> Dict[str, Any]:
        """
        发送命令到服务器

        Args:
            command: 命令名称
            payload: 命令参数
            client_uuid: 客户端 UUID

        Returns:
            服务器响应
        """
        if not self.handle:
            raise RuntimeError("Not connected to Named Pipe")

        # 构造请求
        request = {
            "command": command,
            "client_uuid": client_uuid,
            "payload": payload or {}
        }

        request_data = json.dumps(request).encode('utf-8')

        # 发送请求
        win32file.WriteFile(self.handle, request_data)

        # 读取响应
        result, response_data = win32file.ReadFile(self.handle, 65536)

        if result == 0:  # 成功
            response = json.loads(response_data.decode('utf-8'))
            return response
        else:
            raise RuntimeError(f"Failed to read response: {result}")

    def list_clients(self, page: int = 0, page_size: int = 50) -> Dict[str, Any]:
        """获取客户端列表"""
        return self.send_command("list_clients", {
            "page": page,
            "page_size": page_size
        })

    def disconnect(self):
        """断开连接"""
        if self.handle:
            win32file.CloseHandle(self.handle)
            self.handle = None
            logger.info("Disconnected from Named Pipe")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# 使用示例
if __name__ == "__main__":
    # 本地连接
    with NamedPipeClient(server_name=".", pipe_name="classtop") as client:
        response = client.list_clients()
        print(f"Clients: {response}")

    # 远程连接（通过 SMB）
    with NamedPipeClient(server_name="192.168.1.100", pipe_name="classtop") as client:
        response = client.send_command("get_schedule", {"week": 1})
        print(f"Schedule: {response}")
```

**Python 客户端 (跨平台 - 通过 SMB)**:
```python
# src-tauri/python/tauri_app/smb_pipe_client.py
from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.open import CreateDisposition, FileAttributes, ImpersonationLevel, Open
import json
from typing import Dict, Any

class SMBNamedPipeClient:
    """通过 SMB 协议访问 Windows Named Pipes（Linux/macOS）"""

    def __init__(self, server: str, pipe_name: str = "classtop",
                 username: str = None, password: str = None):
        self.server = server
        self.pipe_name = pipe_name
        self.username = username
        self.password = password
        self.connection = None
        self.session = None
        self.pipe_handle = None

    def connect(self) -> bool:
        """连接到 SMB 服务器并打开 Named Pipe"""
        try:
            # 建立 SMB 连接
            self.connection = Connection(uuid.uuid4(), self.server, 445)
            self.connection.connect()

            # 创建会话
            self.session = Session(self.connection, self.username, self.password)
            self.session.connect()

            # 打开命名管道
            tree = r"\\{}\IPC$".format(self.server)
            pipe_path = self.pipe_name

            self.pipe_handle = Open(tree, pipe_path)
            self.pipe_handle.create(
                ImpersonationLevel.Impersonation,
                FileAttributes.FILE_ATTRIBUTE_NORMAL,
                CreateDisposition.FILE_OPEN,
                0
            )

            return True

        except Exception as e:
            print(f"SMB connection failed: {e}")
            return False

    def send_command(self, command: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送命令"""
        request = {
            "command": command,
            "payload": payload or {}
        }

        request_data = json.dumps(request).encode('utf-8')
        self.pipe_handle.write(request_data)

        response_data = self.pipe_handle.read(0, 65536)
        return json.loads(response_data.decode('utf-8'))

    def disconnect(self):
        """断开连接"""
        if self.pipe_handle:
            self.pipe_handle.close()
        if self.session:
            self.session.disconnect()
        if self.connection:
            self.connection.disconnect()
```

### 4. 双通道集成到 Management Server

**main.rs**:
```rust
mod grpc;
mod named_pipes;

use std::env;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();

    let config = Config::from_env();
    let db_pool = create_db_pool(&config).await?;

    // ========== gRPC 服务器（默认启用）==========
    if config.grpc_enabled {
        let db_clone = db_pool.clone();
        tokio::spawn(async move {
            if let Err(e) = grpc::start_grpc_server(&config.grpc_addr, db_clone).await {
                eprintln!("gRPC server error: {}", e);
            }
        });
        println!("✅ gRPC server enabled on {}", config.grpc_addr);
    }

    // ========== Named Pipes 服务器（开发者选项，默认禁用）==========
    if config.named_pipes_enabled {
        #[cfg(windows)]
        {
            println!("⚠️ WARNING: Named Pipes (SMB) is enabled!");
            println!("⚠️ This is a compatibility feature. Use gRPC for production.");

            let db_clone = db_pool.clone();
            tokio::spawn(async move {
                if let Err(e) = named_pipes::start_named_pipe_server(
                    &config.pipe_name,
                    db_clone
                ).await {
                    eprintln!("Named Pipes server error: {}", e);
                }
            });
        }

        #[cfg(not(windows))]
        {
            eprintln!("❌ Named Pipes is only supported on Windows");
            eprintln!("   Please use gRPC or cross-platform pipe server instead");
        }
    }

    // ========== HTTP/WebSocket 服务器 ==========
    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(db_pool.clone()))
            // ... 路由
    })
    .bind(&config.http_addr)?
    .run()
    .await
}
```

### 5. 配置系统

**config.toml**:
```toml
# ========== gRPC 配置（推荐，默认启用）==========
[grpc]
enabled = true
addr = "0.0.0.0:50051"

# ========== Named Pipes 配置（开发者选项，默认禁用）==========
[named_pipes]
enabled = false  # ⚠️ 默认禁用
pipe_name = "classtop"  # Windows: \\.\pipe\classtop

# 安全警告
# ⚠️ 启用 Named Pipes 前请确保：
# 1. 仅在受信任的局域网环境中使用
# 2. 防火墙已正确配置（TCP 445 端口）
# 3. 了解 SMB 协议的安全风险
# 4. 生产环境推荐使用 gRPC + TLS

[http]
addr = "0.0.0.0:8080"
```

**环境变量配置**:
```bash
# gRPC（推荐）
GRPC_ENABLED=true
GRPC_ADDR=0.0.0.0:50051

# Named Pipes（开发者选项）
NAMED_PIPES_ENABLED=false  # 默认禁用
PIPE_NAME=classtop
```

**客户端配置 (Python)**:
```python
# src-tauri/python/tauri_app/settings.py
MANAGEMENT_SERVER = {
    # 通信方式选择（优先级从高到低）
    "protocol": "grpc",  # 选项: "grpc", "named_pipes", "websocket"

    # gRPC 配置
    "grpc_address": "192.168.1.100:50051",
    "use_tls": False,

    # Named Pipes 配置（Windows only）
    "pipe_server": "192.168.1.100",  # 服务器名称或 IP
    "pipe_name": "classtop",

    # 通用配置
    "timeout": 30,
    "retry_count": 3,
}
```

### 6. 客户端适配层

**src-tauri/python/tauri_app/management_client_adapter.py**:
```python
from typing import Dict, Any, Optional
import platform
from .grpc_client import ClassTopGrpcClient
from .settings import MANAGEMENT_SERVER

# 根据平台和配置动态导入
if platform.system() == "Windows":
    try:
        from .named_pipe_client import NamedPipeClient
    except ImportError:
        NamedPipeClient = None
else:
    try:
        from .smb_pipe_client import SMBNamedPipeClient as NamedPipeClient
    except ImportError:
        NamedPipeClient = None


class ManagementClientAdapter:
    """管理服务器客户端适配器（支持多种通信协议）"""

    def __init__(self):
        self.protocol = MANAGEMENT_SERVER.get("protocol", "grpc")
        self.client: Optional[Any] = None

    async def connect(self) -> bool:
        """连接到管理服务器"""
        if self.protocol == "grpc":
            return await self._connect_grpc()
        elif self.protocol == "named_pipes":
            return self._connect_named_pipes()
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

    async def _connect_grpc(self) -> bool:
        """连接到 gRPC 服务器"""
        try:
            self.client = ClassTopGrpcClient(
                MANAGEMENT_SERVER["grpc_address"]
            )
            await self.client.connect()
            return True
        except Exception as e:
            print(f"gRPC connection failed: {e}")
            return False

    def _connect_named_pipes(self) -> bool:
        """连接到 Named Pipes 服务器"""
        if NamedPipeClient is None:
            raise RuntimeError("Named Pipes client not available on this platform")

        try:
            self.client = NamedPipeClient(
                server_name=MANAGEMENT_SERVER["pipe_server"],
                pipe_name=MANAGEMENT_SERVER["pipe_name"]
            )
            return self.client.connect()
        except Exception as e:
            print(f"Named Pipes connection failed: {e}")
            return False

    async def list_clients(self, page: int = 0, page_size: int = 50):
        """获取客户端列表（统一接口）"""
        if self.protocol == "grpc":
            return await self.client.list_clients(page, page_size)
        elif self.protocol == "named_pipes":
            return self.client.list_clients(page, page_size)

    async def disconnect(self):
        """断开连接"""
        if self.client:
            if self.protocol == "grpc":
                await self.client.close()
            elif self.protocol == "named_pipes":
                self.client.disconnect()


# 使用示例
async def main():
    adapter = ManagementClientAdapter()

    if await adapter.connect():
        clients = await adapter.list_clients()
        print(f"Clients: {clients}")
        await adapter.disconnect()
```

## 双通道架构对比

### 性能对比

| 方案 | 延迟 | 吞吐量 | 内存占用 | 跨平台 | 安全性 | 推荐度 |
|------|------|--------|----------|--------|--------|--------|
| **gRPC** | 1-5ms | 高 | 中 | ✅ | 高（TLS） | ⭐⭐⭐⭐⭐ |
| Unix Socket + TCP | 0.5-3ms | 极高 | 低 | ✅ | 中 | ⭐⭐⭐⭐ |
| WebSocket | 5-10ms | 中 | 中 | ✅ | 高（TLS） | ⭐⭐⭐ |
| **Named Pipes (SMB)** | 10-50ms | 低 | 高 | ⚠️ | 低 | ⭐⭐ |

### 使用场景对比

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| **生产环境** | gRPC + TLS | 性能好、安全、跨平台 |
| **开发测试** | gRPC（无 TLS） | 快速开发，易于调试 |
| **纯 Windows 局域网** | gRPC 或 Named Pipes | gRPC 更优，Named Pipes 仅兼容性测试 |
| **需要 SQL Server 风格** | Named Pipes（开发者选项） | 仅用于特殊兼容性需求 |
| **跨平台部署** | gRPC | Named Pipes 需要 Samba，配置复杂 |
| **浏览器客户端** | WebSocket | 浏览器原生支持 |
| **本地高性能** | Unix Socket + TCP | 本地零拷贝，性能最优 |

### 双通道架构流程图

```
Management Server 启动
    ↓
读取配置文件
    ↓
    ├─→ gRPC 启用？
    │   ├─ 是 → 启动 gRPC 服务器（0.0.0.0:50051）
    │   └─ 否 → 跳过
    │
    └─→ Named Pipes 启用？
        ├─ 是 → 检查平台
        │   ├─ Windows → 启动 Named Pipes 服务器（\\.\pipe\classtop）
        │   └─ Linux/macOS → 报错或启动跨平台 Pipe 服务器
        └─ 否 → 跳过（默认）

ClassTop 客户端连接
    ↓
读取配置（protocol）
    ↓
    ├─→ protocol = "grpc"
    │   └─→ 连接到 gRPC 服务器
    │
    ├─→ protocol = "named_pipes"
    │   └─→ 连接到 Named Pipes 服务器
    │
    └─→ protocol = "websocket"
        └─→ 连接到 WebSocket 服务器
```

## 部署配置

### 服务器配置（双通道）

```toml
# config.toml

# ========== gRPC 配置（主推，默认启用）==========
[grpc]
enabled = true
addr = "0.0.0.0:50051"  # 局域网监听
# addr = "127.0.0.1:50051"  # 仅本地

# TLS 配置（生产环境推荐）
use_tls = false
cert_file = "/path/to/server.crt"
key_file = "/path/to/server.key"

# ========== Named Pipes 配置（开发者选项，默认禁用）==========
[named_pipes]
enabled = false  # ⚠️ 默认禁用，需手动启用
pipe_name = "classtop"

# ⚠️ 安全警告
# 启用 Named Pipes 前请确保：
# 1. 仅在受信任的局域网环境中使用
# 2. 防火墙已正确配置（TCP 445 端口）
# 3. 了解 SMB 协议的安全风险
# 4. 生产环境强烈推荐使用 gRPC + TLS

# ========== HTTP/WebSocket 配置 ==========
[http]
addr = "0.0.0.0:8080"

[websocket]
enabled = true
addr = "0.0.0.0:8081"
```

### 客户端配置（双通道选择）

```python
# settings.py
MANAGEMENT_SERVER = {
    # ========== 通信方式选择 ==========
    # 选项: "grpc" (推荐), "named_pipes" (兼容性), "websocket" (浏览器)
    "protocol": "grpc",

    # ========== gRPC 配置（推荐）==========
    "grpc_address": "192.168.1.100:50051",  # 局域网地址
    "use_tls": False,  # 生产环境建议启用
    "timeout": 30,
    "retry_count": 3,

    # ========== Named Pipes 配置（Windows only，开发者选项）==========
    "pipe_server": "192.168.1.100",  # 服务器名称、IP 或 "." (本地)
    "pipe_name": "classtop",  # 管道名称
    # 远程连接格式: \\192.168.1.100\pipe\classtop

    # ========== WebSocket 配置 ==========
    "websocket_url": "ws://192.168.1.100:8081",
}

# ========== 自动切换策略（可选）==========
# 客户端可以实现自动回退策略
PROTOCOL_FALLBACK = [
    "grpc",         # 优先尝试 gRPC
    "websocket",    # gRPC 失败时回退到 WebSocket
    "named_pipes",  # WebSocket 失败时回退到 Named Pipes（仅 Windows）
]
```

### 环境变量配置

**服务器端**:
```bash
# .env

# gRPC 配置
GRPC_ENABLED=true
GRPC_ADDR=0.0.0.0:50051

# Named Pipes 配置（开发者选项）
NAMED_PIPES_ENABLED=false
PIPE_NAME=classtop

# TLS 配置
USE_TLS=false
CERT_FILE=/path/to/cert.pem
KEY_FILE=/path/to/key.pem
```

**客户端**:
```bash
# .env

# 选择通信协议
PROTOCOL=grpc

# gRPC 配置
GRPC_ADDRESS=192.168.1.100:50051

# Named Pipes 配置
PIPE_SERVER=192.168.1.100
PIPE_NAME=classtop
```

## 安全建议（双通道）

### gRPC 安全配置（推荐）

1. **TLS 加密（生产环境必须）**:
   ```rust
   use tonic::transport::{Server, ServerTlsConfig, Identity};

   let cert = tokio::fs::read("server.crt").await?;
   let key = tokio::fs::read("server.key").await?;
   let identity = Identity::from_pem(cert, key);

   let tls = ServerTlsConfig::new()
       .identity(identity);

   Server::builder()
       .tls_config(tls)?
       .add_service(service)
       .serve(addr)
       .await?;
   ```

2. **认证与授权**:
   ```rust
   use tonic::{Request, Status};

   pub struct AuthInterceptor;

   impl tonic::service::Interceptor for AuthInterceptor {
       fn call(&mut self, request: Request<()>) -> Result<Request<()>, Status> {
           let token = request.metadata()
               .get("authorization")
               .ok_or_else(|| Status::unauthenticated("No token"))?;

           // 验证 Token
           verify_token(token)?;

           Ok(request)
       }
   }

   // 使用拦截器
   Server::builder()
       .add_service(
           ClassTopServiceServer::with_interceptor(service, AuthInterceptor)
       )
       .serve(addr)
       .await?;
   ```

3. **防火墙配置**:
   ```bash
   # 仅允许局域网访问 gRPC 端口
   sudo ufw allow from 192.168.1.0/24 to any port 50051
   sudo ufw deny 50051

   # iptables
   sudo iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 50051 -j ACCEPT
   sudo iptables -A INPUT -p tcp --dport 50051 -j DROP
   ```

### Named Pipes 安全配置（开发者选项）

⚠️ **警告**: Named Pipes over SMB 存在已知安全风险，仅在以下条件下使用：

1. **受信任的局域网环境**
2. **已隔离的测试网络**
3. **兼容性测试目的**

**安全措施**:

1. **限制 SMB 访问**:
   ```bash
   # Windows 防火墙
   netsh advfirewall firewall add rule name="SMB_LAN_Only" ^
       dir=in action=allow protocol=TCP localport=445 ^
       remoteip=192.168.1.0/24

   # 阻止外网访问
   netsh advfirewall firewall add rule name="SMB_Block_Internet" ^
       dir=in action=block protocol=TCP localport=445 ^
       remoteip=0.0.0.0/0
   ```

2. **Named Pipe ACL（访问控制列表）**:
   ```rust
   #[cfg(windows)]
   use winapi::um::securitybaseapi::*;
   use winapi::um::accctrl::*;

   // 创建仅管理员可访问的命名管道
   fn create_secure_pipe(pipe_name: &str) -> Result<PipeServer, Error> {
       let security_attributes = create_admin_only_security_descriptor()?;

       let pipe = PipeOptions::new(pipe_name)
           .access_inbound(true)
           .access_outbound(true)
           .security_attributes(&security_attributes)
           .create()?;

       Ok(pipe)
   }
   ```

3. **禁用 SMBv1（已过时，存在严重漏洞）**:
   ```powershell
   # Windows PowerShell（管理员权限）
   Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

   # 确认 SMBv1 已禁用
   Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol
   ```

4. **最小权限原则**:
   - Named Pipes 服务器以受限用户身份运行
   - 不要以管理员权限运行服务
   - 使用 Windows 服务账户

5. **审计日志**:
   ```rust
   use log::{info, warn};

   fn handle_pipe_client(pipe: PipeServer, client_addr: String) {
       info!("Named Pipe client connected from: {}", client_addr);

       // 记录所有命令
       if let Ok(request) = read_request(&mut pipe) {
           info!("Command from {}: {}", client_addr, request.command);
       }

       warn!("Named Pipe connection closed: {}", client_addr);
   }
   ```

### 通用安全建议

1. **网络隔离**:
   - 管理服务器与客户端部署在隔离的 VLAN
   - 使用 VPN 访问管理网络
   - 禁止直接暴露到公网

2. **定期更新**:
   - 及时更新 Rust、Python 依赖
   - 监控安全公告（CVE）
   - 定期审计代码

3. **监控与告警**:
   - 监控异常连接尝试
   - 记录失败的认证尝试
   - 设置流量异常告警

4. **备份与恢复**:
   - 定期备份配置和数据
   - 测试恢复流程
   - 准备应急响应计划

## 总结

### 双通道架构设计原则

本设计采用**双通道并存**的架构，允许根据场景灵活选择通信方式：

1. **gRPC（主推，默认启用）**:
   - ✅ **性能优秀**: HTTP/2 多路复用，1-5ms 延迟
   - ✅ **跨语言**: Rust + Python 无缝集成
   - ✅ **双向流**: 支持实时同步、服务器推送
   - ✅ **生态完善**: 工具链成熟，社区活跃
   - ✅ **类型安全**: Protocol Buffers 强类型定义
   - ✅ **安全性高**: 内置 TLS 支持，认证机制完善
   - ✅ **生产就绪**: 经过 Google、Netflix 等大规模验证

2. **Named Pipes over SMB（开发者选项，默认禁用）**:
   - ⚠️ **兼容性**: 与 SQL Server 风格一致
   - ⚠️ **Windows 原生**: Windows 环境下开发熟悉
   - ⚠️ **特殊场景**: 仅用于需要 SQL Server 风格的兼容性测试
   - ❌ **性能较差**: 10-50ms 延迟，开销大
   - ❌ **跨平台复杂**: Linux/macOS 需要 Samba
   - ❌ **安全风险**: SMB 协议存在已知漏洞
   - ❌ **不推荐生产**: 仅用于开发测试

### 使用建议

**何时使用 gRPC**（推荐 99% 的场景）:
- ✅ 新项目开发
- ✅ 生产环境部署
- ✅ 跨平台环境（Windows、Linux、macOS 混合）
- ✅ 需要高性能、低延迟
- ✅ 需要 TLS 加密
- ✅ 需要双向流通信

**何时使用 Named Pipes**（特殊场景）:
- ⚠️ 纯 Windows 局域网环境
- ⚠️ 需要与现有 SQL Server 风格系统集成
- ⚠️ 兼容性测试
- ⚠️ 概念验证（PoC）
- ❌ **不推荐生产环境使用**

### 迁移路径

**阶段 1: 初始部署（推荐）**
- 启用 gRPC（默认）
- Named Pipes 保持禁用
- 客户端使用 gRPC 连接
- 验证功能完整性

**阶段 2: 兼容性测试（可选）**
- 在开发者选项中启用 Named Pipes
- 测试特定场景（如 SQL Server 风格集成）
- 验证两种通道均可正常工作
- 记录性能对比数据

**阶段 3: 生产部署**
- **主通道**: gRPC + TLS（强烈推荐）
- **备用通道**: WebSocket（浏览器客户端）
- **禁用**: Named Pipes（除非有明确的兼容性需求）

**阶段 4: 优化（可选）**
- 根据监控数据调整 gRPC 配置
- 实现客户端自动回退策略
- 添加负载均衡（多个 gRPC 服务器实例）

### 性能与安全对比总结

| 维度 | gRPC | Named Pipes (SMB) |
|------|------|-------------------|
| **延迟** | 1-5ms | 10-50ms |
| **吞吐量** | 高 | 低 |
| **内存占用** | 中 | 高 |
| **跨平台** | ✅ 原生支持 | ⚠️ 需要 Samba |
| **安全性** | 高（TLS + Auth） | 低（SMB 漏洞） |
| **开发体验** | 优秀（工具链） | 一般 |
| **维护成本** | 低 | 高 |
| **生产就绪** | ✅ | ❌ |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### 最终建议

**默认配置**:
```toml
[grpc]
enabled = true  # ✅ 主推

[named_pipes]
enabled = false  # ⚠️ 默认禁用，仅开发者选项
```

**关键结论**:
1. **gRPC 是现代、高性能、安全的最佳选择**
2. **Named Pipes 仅用于特殊兼容性需求**
3. **生产环境强烈推荐 gRPC + TLS**
4. **双通道架构提供灵活性，但不增加复杂度**（默认禁用 Named Pipes）
5. **客户端适配层确保切换通道时代码无需修改**

**这比传统的 Named Pipes over SMB 更现代、更高效、更安全、更易维护！**
