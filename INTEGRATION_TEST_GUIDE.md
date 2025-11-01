# ClassTop Management Server 集成测试指南

## 集成完成概述

已成功实现 ClassTop 客户端与 Management Server 的基础 HTTP REST API 同步功能。

### 实现内容

#### 1. 新增文件
- **sync_client.py**: 同步客户端模块，负责与 Management Server 通信
  - `register_client()`: 注册客户端
  - `sync_to_server()`: 同步数据
  - `test_connection()`: 测试连接
  - `start_auto_sync()`: 启动自动同步线程

#### 2. 修改文件
- **schedule_manager.py**:
  - `get_all_courses()`: 获取所有课程（用于同步）
  - `get_all_schedule_entries()`: 获取所有课程表条目（用于同步）

- **settings_manager.py**:
  - 添加默认配置:
    - `client_name`: 客户端名称
    - `sync_enabled`: 是否启用自动同步
    - `sync_interval`: 同步间隔（秒）

- **__init__.py**:
  - 集成 SyncClient 初始化
  - 支持自动注册和启动同步

- **commands.py**:
  - `test_server_connection()`: 测试服务器连接命令
  - `sync_now()`: 立即同步命令
  - `register_to_server()`: 注册到服务器命令

- **pyproject.toml**:
  - 添加 `requests` 依赖

## 测试步骤

### 前置条件

1. **Management Server 已运行**:
   ```bash
   cd /Users/logos/RustroverProjects/Classtop-Management-Server
   cargo run --release
   ```
   - 访问 http://localhost:8765 确认服务器运行正常

2. **PostgreSQL 数据库已配置**

### 测试流程

#### 步骤 1: 启动 ClassTop 客户端

```bash
cd /Users/logos/fleet/classtop
npm run tauri dev
```

#### 步骤 2: 配置同步设置

通过 Python 命令或前端设置（需要前端 UI 支持）配置：

```python
# 可以通过浏览器控制台调用（如果前端已实现）
# 或者直接修改数据库
```

**必需配置**:
- `server_url`: `http://localhost:8765`
- `client_name`: `测试客户端-01`
- `sync_enabled`: `true`
- `sync_interval`: `60` (测试用，1分钟)

#### 步骤 3: 测试连接

在客户端应用中调用（通过前端或 Python 控制台）:
```javascript
// 前端调用示例（需要在前端实现）
await invoke('test_server_connection')
```

**预期结果**:
- 返回 `{"success": true, "message": "连接成功"}`
- 日志中显示 "连接成功"

#### 步骤 4: 注册客户端

```javascript
await invoke('register_to_server')
```

**预期结果**:
- 返回 `{"success": true, "message": "注册成功"}`
- 日志中显示 "客户端注册成功: 测试客户端-01"
- Management Server 数据库中新增客户端记录

#### 步骤 5: 添加测试数据

在 ClassTop 客户端中添加课程和课程表:
1. 课程: 高等数学、大学英语
2. 课程表: 周一 08:00-09:40 高等数学

#### 步骤 6: 手动同步

```javascript
await invoke('sync_now')
```

**预期结果**:
- 返回 `{"success": true, "message": "同步成功"}`
- 日志显示: "同步成功: 2 门课程, 1 个课程表条目"

#### 步骤 7: 验证同步结果

访问 Management Server 管理界面:
- http://localhost:8765
- 进入"客户端"页面，查看注册的客户端
- 查看客户端的课程和课程表数据

#### 步骤 8: 测试自动同步

等待 1 分钟（sync_interval），观察日志:
- 应该看到 "同步成功，等待 60 秒"
- 自动同步线程正常运行

### 验证清单

- [ ] 客户端成功注册到 Management Server
- [ ] 课程数据正确同步
- [ ] 课程表数据正确同步
- [ ] 周次数据（JSON 数组）正确处理
- [ ] 更新课程后再次同步，服务端数据被更新
- [ ] 自动同步线程正常运行
- [ ] 日志记录完整清晰

## 常见问题排查

### 问题 1: 无法连接到服务器

**症状**: `test_server_connection` 返回 "无法连接到服务器"

**排查步骤**:
1. 检查 Management Server 是否运行: `curl http://localhost:8765/api/health`
2. 检查防火墙配置
3. 确认 `server_url` 配置正确

### 问题 2: 注册失败

**症状**: `register_to_server` 返回失败

**可能原因**:
- UUID 格式错误
- 数据库连接失败
- 服务器日志中有错误信息

**解决方法**:
- 查看 ClassTop 日志: `~/.classtop/logs/`
- 查看 Management Server 日志

### 问题 3: 同步数据不完整

**症状**: 部分课程或课程表未同步

**可能原因**:
- location 字段缺失（已解决）
- JSON 格式错误
- 外键约束失败

**解决方法**:
- 检查 ClassTop 数据库: `~/.classtop/app_config.db`
- 使用 SQLite 查看 `courses` 表结构
- 确认 `weeks` 字段为有效 JSON 数组

### 问题 4: 同步失败但无错误日志

**可能原因**:
- requests 库未安装

**解决方法**:
```bash
cd /Users/logos/fleet/classtop/src-tauri
pip install requests
# 或者重新安装项目依赖
uv pip install -e .
```

## 下一步计划

### 短期 (完成基础集成)

1. **前端 UI 集成**:
   - 在设置页面添加服务器配置界面
   - 显示同步状态指示器
   - 添加手动同步按钮

2. **完善错误处理**:
   - 添加重试机制
   - 改进错误提示
   - 记录详细日志

3. **测试验证**:
   - 多客户端同步测试
   - 网络异常场景测试
   - 数据冲突处理测试

### 中期 (功能增强)

1. **增量同步**:
   - 仅同步变更的数据
   - 减少网络带宽使用

2. **冲突解决**:
   - 时间戳比较
   - 手动解决冲突

3. **离线支持**:
   - 离线队列
   - 恢复连接后自动同步

### 长期 (高级功能)

1. **实时同步**:
   - WebSocket 实时推送
   - 双向数据同步

2. **gRPC 集成**:
   - 替换 HTTP 为 gRPC
   - 提升性能和效率

3. **安全加固**:
   - TLS 加密
   - API Key 认证
   - 权限控制

## 文档参考

- [快速开始指南](./docs/QUICK_START_SYNC.md)
- [客户端适配指南](./docs/CLIENT_ADAPTATION.md)
- [双轨架构方案](./docs/DUAL_TRACK_ARCHITECTURE.md)
- [Management Server 仓库](https://github.com/Zixiao-System/Classtop-Management-Server)

## 提交信息

```bash
git add .
git commit -m "feat: integrate Management Server basic HTTP sync

- Add sync_client.py module for HTTP REST API communication
- Extend schedule_manager.py with get_all_courses() and get_all_schedule_entries()
- Add sync-related commands: test_server_connection, sync_now, register_to_server
- Update settings with sync configuration (sync_enabled, sync_interval, client_name)
- Add requests dependency to pyproject.toml
- Implement auto-sync thread with configurable interval

Implements basic HTTP sync as documented in docs/QUICK_START_SYNC.md
Ref: https://github.com/Zixiao-System/Classtop-Management-Server"
```
