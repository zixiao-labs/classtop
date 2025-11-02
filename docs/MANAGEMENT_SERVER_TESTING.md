# Management-Server 集成功能测试指南

本文档为 ClassTop 维护者提供完整的 Management-Server 集成功能测试步骤和验证标准。

## 📋 测试环境准备

### 1. 前置条件

**必需软件:**
- Node.js 18+
- Python 3.10+
- Rust 1.75+ (用于运行 Management-Server)
- PostgreSQL 14+ (用于 Management-Server)
- SQLite 3 (ClassTop 客户端使用)

**必需项目:**
1. ClassTop 客户端项目 (本仓库)
2. [Classtop-Management-Server](https://github.com/Zixiao-System/Classtop-Management-Server)

### 2. 启动 Management-Server

```bash
# 克隆 Management-Server (如果还没有)
git clone https://github.com/Zixiao-System/Classtop-Management-Server.git
cd Classtop-Management-Server

# 配置数据库
cp .env.example .env
# 编辑 .env 文件，配置 PostgreSQL 连接:
# DATABASE_URL=postgres://username:password@localhost/classtop_management

# 初始化数据库
createdb classtop_management  # 或使用 psql

# 构建前端
cd frontend
npm install
npm run build
cd ..

# 运行数据库迁移（如果有）
# diesel migration run

# 启动服务器
cargo run --release
```

**验证 Management-Server 启动成功:**
```bash
# 测试健康检查接口
curl http://localhost:8765/api/health

# 预期输出:
# {"success":true,"message":"OK","data":{"status":"running","version":"1.0.0"}}
```

访问 http://localhost:8765 应看到管理界面。

### 3. 启动 ClassTop 客户端

```bash
# 在 ClassTop 项目根目录
npm install
npm run tauri dev
```

**预期行为:**
- 启动两个窗口：主窗口(1200x800) 和 TopBar 窗口(1400x50)
- 控制台应显示 "应用初始化完成" 日志

### 4. 准备测试数据

在客户端主窗口中添加一些测试课程数据:

**推荐测试数据:**
1. **课程 1:**
   - 名称: "软件工程"
   - 教师: "张老师"
   - 颜色: #6750A4
   - 时间: 周一 08:00-09:40, 周次 [1,2,3,4,5]

2. **课程 2:**
   - 名称: "数据结构"
   - 教师: "李老师"
   - 颜色: #FF5722
   - 时间: 周三 14:00-15:40, 周次 [1,3,5,7,9]

3. **课程 3:**
   - 名称: "计算机网络"
   - 教师: "王老师"
   - 颜色: #4CAF50
   - 时间: 周五 10:00-11:40, 周次 [2,4,6,8,10]

## 🧪 功能测试清单

### 核心同步功能
- [ ] TC-001: 测试服务器连接
- [ ] TC-002: 客户端注册
- [ ] TC-003: 手动同步数据
- [ ] TC-004: 自动同步启用/禁用
- [ ] TC-005: 同步间隔配置
- [ ] TC-006: 同步状态显示

### 数据完整性
- [ ] TC-007: 课程数据同步
- [ ] TC-008: 课程表条目同步
- [ ] TC-009: 多周次数据处理
- [ ] TC-010: 特殊字符处理

### 错误处理
- [ ] TC-011: 服务器不可达
- [ ] TC-012: 无效的服务器地址
- [ ] TC-013: 网络超时
- [ ] TC-014: 重复注册处理

### UI 组件
- [ ] TC-015: 同步设置界面
- [ ] TC-016: TopBar 同步状态图标
- [ ] TC-017: 状态图标显示/隐藏

## 📝 详细测试步骤

### TC-001: 测试服务器连接

**目标:** 验证客户端能够正确检测 Management-Server 的连接状态。

**前置条件:**
- Management-Server 正在运行于 http://localhost:8765

**步骤:**
1. 打开 ClassTop 主窗口
2. 点击底部导航的"设置"图标
3. 滚动到"Management Server 同步"部分
4. 在"服务器地址"输入框中输入: `http://localhost:8765`
5. 点击"测试连接"按钮

**预期结果:**
- 按钮显示加载状态（旋转图标）
- 2-3 秒后显示绿色成功消息："连接成功！服务器运行正常"
- 状态指示器显示绿色文字："连接成功"

**验证点:**
- [ ] URL 输入框接受有效的 HTTP/HTTPS URL
- [ ] 测试按钮在请求期间禁用
- [ ] 成功消息以绿色显示
- [ ] 控制台无错误日志

**失败场景测试:**
1. 停止 Management-Server
2. 再次点击"测试连接"
3. 应显示红色错误消息："无法连接到服务器"

---

### TC-002: 客户端注册

**目标:** 验证客户端能够成功注册到 Management-Server。

**前置条件:**
- TC-001 通过（服务器连接正常）
- 服务器地址已保存

**步骤:**
1. 在"客户端名称"输入框中输入: `测试客户端-01`
2. 点击"注册客户端"按钮
3. 等待注册完成

**预期结果:**
- 显示成功消息："客户端注册成功！"
- ClassTop 日志中显示: "客户端注册成功: 测试客户端-01"

**验证点:**
- [ ] 注册成功后生成 client_uuid 配置
- [ ] client_name 保存到配置
- [ ] Management-Server 客户端列表中出现新客户端

**Management-Server 验证:**
1. 访问 http://localhost:8765
2. 查看"客户端"页面
3. 应看到名为"测试客户端-01"的客户端
4. 客户端状态显示为"已注册"

**数据库验证 (可选):**
```bash
# 检查 ClassTop 客户端配置
sqlite3 ~/.local/share/classtop/classtop.db  # Linux/macOS
# 或 Windows: %APPDATA%\classtop\classtop.db

SELECT key, value FROM config WHERE key IN ('client_uuid', 'client_name');
# 应显示生成的 UUID 和客户端名称
```

---

### TC-003: 手动同步数据

**目标:** 验证客户端能够手动触发数据同步到服务器。

**前置条件:**
- TC-002 通过（客户端已注册）
- 客户端有测试课程数据（见"准备测试数据"）

**步骤:**
1. 确认客户端已添加至少 2 门课程
2. 在设置页面找到"立即同步"按钮
3. 点击"立即同步"按钮

**预期结果:**
- 显示成功消息（例如："同步成功！"）
- ClassTop 日志显示: "同步成功: X 门课程, Y 个课程表条目"

**验证点:**
- [ ] 同步按钮在请求期间显示加载状态
- [ ] 成功消息包含同步的课程数量
- [ ] 无错误日志

**Management-Server 数据验证:**
1. 访问 http://localhost:8765/clients (或相应的数据查看页面)
2. 选择"测试客户端-01"
3. 查看同步的课程数据
4. 验证以下字段正确同步:
   - 课程名称
   - 教师名称
   - 课程颜色
   - 课程表时间 (day_of_week, start_time, end_time)
   - 周次数组 (weeks)

**数据一致性检查:**
```bash
# 比对 ClassTop 和 Management-Server 的数据
# ClassTop:
sqlite3 ~/.local/share/classtop/classtop.db
SELECT COUNT(*) FROM courses;
SELECT COUNT(*) FROM schedule;

# Management-Server (PostgreSQL):
psql classtop_management
SELECT COUNT(*) FROM courses WHERE client_uuid = '<your-uuid>';
SELECT COUNT(*) FROM schedule_entries WHERE client_uuid = '<your-uuid>';

# 数量应该匹配
```

---

### TC-004: 自动同步启用/禁用

**目标:** 验证自动同步功能的启用和禁用。

**前置条件:**
- TC-003 通过（手动同步成功）

**步骤 A: 启用自动同步**
1. 在设置页面找到"启用自动同步"开关
2. 打开开关（切换到 ON 状态）
3. 观察通知消息

**预期结果 A:**
- 显示消息: "自动同步已启用"
- ClassTop 日志显示: "启动自动同步线程"

**步骤 B: 验证自动同步运行**
1. 等待 5-10 分钟（或根据配置的同步间隔）
2. 查看 ClassTop 日志

**预期结果 B:**
- 日志中定期出现: "同步成功，等待 X 秒"
- Management-Server 的客户端"最后同步时间"字段更新

**步骤 C: 禁用自动同步**
1. 关闭"启用自动同步"开关
2. 观察通知消息

**预期结果 C:**
- 显示消息: "自动同步已禁用"
- ClassTop 日志显示: "停止自动同步线程"
- 日志中不再出现自动同步消息

**验证点:**
- [ ] 开关状态正确保存到配置
- [ ] 后台线程正确启动和停止
- [ ] 无内存泄漏（长时间运行测试）

---

### TC-005: 同步间隔配置

**目标:** 验证自动同步间隔可以正确配置。

**前置条件:**
- 自动同步已启用

**测试间隔选项:**
| 选项 | 值（秒） | 说明 |
|-----|---------|------|
| 1分钟 | 60 | 测试用 |
| 5分钟 | 300 | 默认值 |
| 15分钟 | 900 | 生产推荐 |
| 30分钟 | 1800 | 低频同步 |

**步骤:**
1. 在"同步间隔"下拉菜单中选择"1分钟"
2. 观察通知消息
3. 等待 60-70 秒
4. 查看日志确认同步触发

**预期结果:**
- 显示消息: "同步间隔已设置为1分钟"
- 约 60 秒后日志显示同步执行
- 后续每 60 秒触发一次同步

**验证点:**
- [ ] 间隔值正确保存到配置
- [ ] 后台线程使用新的间隔值
- [ ] 时间精度在 ±5 秒内

**长时间测试 (可选):**
1. 设置较短间隔（1分钟）
2. 运行 30 分钟
3. 验证同步次数 ≈ 30 次
4. 检查无异常或崩溃

---

### TC-006: 同步状态显示

**目标:** 验证 TopBar 窗口的同步状态图标正确显示。

**前置条件:**
- 客户端已注册并配置同步

**步骤 A: 显示已连接状态**
1. 确保 sync_enabled = true
2. 确保 show_sync_status = true (默认)
3. 查看 TopBar 窗口右侧

**预期结果 A:**
- 显示绿色 `cloud_done` 图标
- 鼠标悬停显示工具提示:
  - "已连接到 Management Server"
  - "服务器: http://localhost:8765"

**步骤 B: 显示未连接状态**
1. 在设置中禁用自动同步（sync_enabled = false）
2. 查看 TopBar 窗口

**预期结果 B:**
- 显示红色 `cloud_off` 图标
- 鼠标悬停显示: "未连接到 Management Server"

**步骤 C: 隐藏状态图标**
1. 在设置中找到"组件显示 > 同步状态"开关
2. 关闭开关

**预期结果 C:**
- TopBar 窗口不再显示同步状态图标
- 其他组件（时钟、课程表）不受影响

**验证点:**
- [ ] 图标颜色正确（绿色/红色）
- [ ] 图标类型正确（cloud_done/cloud_off）
- [ ] 工具提示内容准确
- [ ] 显示/隐藏功能正常

---

### TC-007: 课程数据同步

**目标:** 验证课程数据的完整性和正确性。

**测试数据:**
创建具有以下特征的课程:

1. **基础课程:**
   - 名称: "测试课程A"
   - 教师: "张三"
   - 颜色: #FF5722
   - 备注: "这是测试课程"

2. **包含特殊字符的课程:**
   - 名称: "高等数学(1)-A班"
   - 教师: "李四&王五"
   - 颜色: #4CAF50
   - 备注: "包含特殊字符: <>&\"'"

3. **长名称课程:**
   - 名称: "计算机科学与技术专业核心课程-软件工程导论与实践"
   - 教师: "赵六"
   - 颜色: #2196F3

**步骤:**
1. 在客户端添加上述 3 门课程
2. 执行手动同步
3. 在 Management-Server 查看同步的数据

**预期结果:**
所有课程字段完整同步，包括:
- [x] 课程 ID (id)
- [x] 课程名称 (name)
- [x] 教师姓名 (teacher)
- [x] 课程颜色 (color)
- [x] 备注信息 (note)

**验证点:**
- [ ] 特殊字符正确转义（不破坏 JSON）
- [ ] 长文本字段无截断
- [ ] 空字段处理正确（teacher 或 note 为空）
- [ ] 颜色值格式正确（十六进制）

**SQL 验证:**
```sql
-- Management-Server (PostgreSQL)
SELECT id, name, teacher, color, note
FROM courses
WHERE client_uuid = '<your-uuid>';

-- 检查特殊字符是否正确存储
SELECT name FROM courses WHERE name LIKE '%(%';
```

---

### TC-008: 课程表条目同步

**目标:** 验证课程表条目的时间和周次数据正确同步。

**测试数据:**
为"测试课程A"添加以下课程表条目:

1. **单次课程:**
   - 星期一 (day_of_week=1)
   - 08:00-09:40
   - 周次: [1]

2. **连续周次课程:**
   - 星期三 (day_of_week=3)
   - 14:00-15:40
   - 周次: [1,2,3,4,5,6,7,8,9,10]

3. **间隔周次课程:**
   - 星期五 (day_of_week=5)
   - 10:00-11:40
   - 周次: [1,3,5,7,9,11,13,15]

**步骤:**
1. 添加上述课程表条目
2. 执行同步
3. 验证 Management-Server 的数据

**预期结果:**
所有条目字段正确同步:
- [x] 条目 ID (id)
- [x] 课程 ID (course_id)
- [x] 星期 (day_of_week: 1-7)
- [x] 开始时间 (start_time: "HH:MM")
- [x] 结束时间 (end_time: "HH:MM")
- [x] 周次数组 (weeks: [1,2,3,...])

**验证点:**
- [ ] 星期数字符合 ISO 8601 (1=周一, 7=周日)
- [ ] 时间格式为 "HH:MM" (24小时制)
- [ ] 周次数组正确解析（JSON）
- [ ] 跨午夜课程处理正确

**JSON 格式验证:**
```sql
-- 检查 weeks 字段是否为有效 JSON 数组
SELECT id, day_of_week, weeks::jsonb
FROM schedule_entries
WHERE client_uuid = '<your-uuid>';

-- 应返回类似: [1,3,5,7,9]
```

---

### TC-009: 多周次数据处理

**目标:** 验证复杂周次配置的正确处理。

**测试场景:**

1. **空周次:**
   - 周次: [] (空数组)
   - 预期: 同步后为空数组，不报错

2. **大周次数组:**
   - 周次: [1,2,3,...,52] (52周)
   - 预期: 完整同步所有周次

3. **无序周次:**
   - 周次: [5,1,9,3,7] (乱序)
   - 预期: 保持原顺序或排序后存储

4. **重复周次:**
   - 周次: [1,1,2,2,3] (包含重复)
   - 预期: 去重或保留重复（根据业务逻辑）

**步骤:**
1. 创建包含上述周次配置的课程表条目
2. 执行同步
3. 验证 Management-Server 的 weeks 字段

**预期结果:**
- [ ] 空数组不导致同步失败
- [ ] 大数组完整传输（无截断）
- [ ] 周次顺序一致
- [ ] 重复值处理符合预期

**边界值测试:**
- 最大周次数: 100
- 最小周次数: 0 (空数组)
- 异常周次值: 负数、0、超大数 (应被过滤或拒绝)

---

### TC-010: 特殊字符处理

**目标:** 验证系统对特殊字符的正确处理。

**测试字符集:**

| 类型 | 示例 | 位置 |
|-----|------|-----|
| HTML 特殊字符 | `<>&"'` | 课程名称、教师 |
| 中文标点 | `，。；：""''` | 备注 |
| Emoji | `📚✏️🎓` | 课程名称 |
| SQL 特殊字符 | `';DROP TABLE--` | 教师名称 (SQL 注入测试) |
| JSON 特殊字符 | `\n\t\r"` | 备注 |

**步骤:**
1. 创建课程，名称为: `测试<script>alert(1)</script>课程`
2. 教师名称: `O'Brien`
3. 备注: `包含换行\n和制表符\t`
4. 执行同步

**预期结果:**
- [ ] 所有特殊字符正确转义
- [ ] 无 XSS 漏洞（Management-Server 界面显示安全）
- [ ] 无 SQL 注入（数据库正常）
- [ ] JSON 解析无错误
- [ ] Emoji 正确存储和显示

**安全验证:**
```sql
-- Management-Server: 检查是否存在未转义的特殊字符
SELECT name FROM courses WHERE name LIKE '%<%';
-- 应返回数据，但 < 应该被正确存储，不执行为 HTML
```

---

### TC-011: 服务器不可达

**目标:** 验证服务器不可用时的错误处理。

**步骤:**
1. 确保同步功能已配置
2. 停止 Management-Server (Ctrl+C)
3. 在客户端点击"测试连接"
4. 点击"立即同步"

**预期结果:**
- [ ] 显示明确的错误消息: "无法连接到服务器"
- [ ] 不崩溃或冻结
- [ ] 日志记录连接失败
- [ ] 自动同步在下次间隔重试

**错误恢复测试:**
1. 重新启动 Management-Server
2. 等待下次自动同步触发
3. 应自动恢复同步

**验证点:**
- [ ] 错误消息用户友好
- [ ] 不泄露敏感信息（如数据库连接字符串）
- [ ] 重试机制正常工作
- [ ] 无内存泄漏

---

### TC-012: 无效的服务器地址

**目标:** 验证对无效 URL 的处理。

**测试用例:**

| 输入 | 预期行为 |
|------|---------|
| `htp://invalid` | 拒绝，提示"URL 格式无效" |
| `localhost:8765` | 拒绝，提示"请输入完整 URL (http://...)" |
| `http://192.168.1.999:8765` | 接受 URL 格式，连接时失败 |
| `https://example.com:8765` | 接受，连接测试失败（假设服务器不存在） |
| `http://localhost:99999` | 拒绝，提示"端口号无效" (可选) |
| `ftp://localhost:8765` | 拒绝，提示"仅支持 HTTP/HTTPS" |

**步骤:**
1. 在服务器地址输入框中输入上述每个测试用例
2. 点击"保存"或"测试连接"

**预期结果:**
- [ ] URL 验证在客户端进行（即时反馈）
- [ ] 无效 URL 无法保存
- [ ] 错误提示清晰明确
- [ ] 已保存的有效 URL 不被意外覆盖

---

### TC-013: 网络超时

**目标:** 验证网络超时的处理。

**步骤:**
1. 配置服务器地址为一个响应极慢的服务器
   - 可以使用模拟工具或网络限速
2. 点击"测试连接"

**预期结果:**
- [ ] 5 秒内超时（根据代码 timeout=5）
- [ ] 显示错误: "连接超时"
- [ ] 用户界面不冻结
- [ ] 可以取消操作（如果实现了）

**压力测试:**
1. 启用自动同步
2. 模拟间歇性网络故障
3. 运行 1 小时
4. 验证客户端稳定，无崩溃

---

### TC-014: 重复注册处理

**目标:** 验证客户端重复注册的处理。

**步骤:**
1. 客户端已注册（TC-002 完成）
2. 再次点击"注册客户端"按钮
3. 观察行为

**预期结果 (根据服务器实现):**

**选项 A: 更新注册信息**
- 显示: "客户端信息已更新"
- Management-Server 更新最后注册时间

**选项 B: 拒绝重复注册**
- 显示: "客户端已注册，无需重复注册"
- 不修改服务器数据

**验证点:**
- [ ] 不创建重复的客户端记录
- [ ] client_uuid 保持不变
- [ ] 客户端名称可以更新
- [ ] 无副作用

---

### TC-015: 同步设置界面

**目标:** 验证设置页面的 UI 组件正常工作。

**检查清单:**

**输入控件:**
- [ ] 服务器地址输入框可编辑
- [ ] 客户端名称输入框可编辑
- [ ] 同步间隔下拉菜单可选择
- [ ] 启用自动同步开关可切换
- [ ] 显示同步状态开关可切换

**按钮:**
- [ ] "测试连接"按钮可点击
- [ ] "注册客户端"按钮可点击
- [ ] "立即同步"按钮可点击
- [ ] 加载状态正确显示（旋转图标）
- [ ] 按钮禁用状态正确（请求期间）

**状态显示:**
- [ ] 同步状态指示器（绿色/红色）
- [ ] 错误消息显示（红色文字）
- [ ] 成功消息显示（绿色文字）
- [ ] Snackbar 通知正确弹出

**响应式:**
- [ ] 窗口缩小时布局正常
- [ ] 字体大小适中
- [ ] 对齐和间距正确

**HTTP 警告测试:**
1. 输入非 localhost 的 HTTP URL: `http://192.168.1.100:8765`
2. 保存时应显示警告: "⚠️ 警告：使用 HTTP 而非 HTTPS..."

---

### TC-016: TopBar 同步状态图标

**目标:** 验证 TopBar 窗口的同步状态图标功能。

**步骤:**
1. 启用同步并注册客户端
2. 确保 show_sync_status = true
3. 观察 TopBar 窗口右侧

**UI 验证:**
- [ ] 图标大小合适（不遮挡其他内容）
- [ ] 图标位置正确（右侧，课程表之后）
- [ ] 图标颜色清晰可见（绿色/红色）
- [ ] 鼠标悬停时出现工具提示
- [ ] 工具提示内容准确

**动态更新测试:**
1. 初始状态：同步已启用，图标为绿色 cloud_done
2. 在设置中禁用同步
3. 返回 TopBar 窗口
4. 图标应变为红色 cloud_off（实时更新）

**验证点:**
- [ ] 状态变化实时反映（无需刷新）
- [ ] 事件监听正常工作
- [ ] 无控制台错误

---

### TC-017: 状态图标显示/隐藏

**目标:** 验证同步状态图标可以显示和隐藏。

**步骤:**
1. 在设置页面找到"组件显示"部分
2. 找到"同步状态"开关
3. 关闭开关
4. 查看 TopBar 窗口

**预期结果:**
- [ ] 同步状态图标立即消失
- [ ] 其他组件（时钟、课程表）保持不变
- [ ] 配置正确保存 (show_sync_status = false)

**恢复测试:**
1. 重新打开"同步状态"开关
2. TopBar 窗口应重新显示同步状态图标
3. 图标状态正确（与当前同步配置一致）

**重启测试:**
1. 隐藏同步状态图标
2. 关闭 ClassTop
3. 重新启动
4. TopBar 窗口仍不显示图标（配置持久化）

---

## 🔍 回归测试

验证 Management-Server 集成没有破坏现有功能。

### 核心功能回归

- [ ] REG-001: 课程 CRUD 操作正常
- [ ] REG-002: 课程表 CRUD 操作正常
- [ ] REG-003: TopBar 课程进度显示正常
- [ ] REG-004: 系统托盘菜单正常
- [ ] REG-005: 周次计算正常
- [ ] REG-006: 主题系统正常
- [ ] REG-007: WebSocket 客户端（LMS）正常工作
- [ ] REG-008: API Server（如果启用）正常工作

### 性能回归

- [ ] REG-009: 应用启动时间无明显增加
- [ ] REG-010: 内存占用无明显增加
- [ ] REG-011: TopBar 刷新性能正常（每秒更新）
- [ ] REG-012: 数据库操作性能正常

**启动时间基准:**
- 无同步: ~2-3 秒
- 有同步（禁用）: ~2-3 秒
- 有同步（启用）: ~3-4 秒

---

## 🐛 故障排查指南

### 问题 1: "Command not found" 错误

**症状:**
```
Error: Command not found: test_server_connection
```

**原因:** 使用了错误的 invoke 函数。

**解决方案:**
确保前端使用 `pyInvoke` 而不是 `invoke`:

```javascript
// 正确 ✅
import { pyInvoke } from 'tauri-plugin-pytauri-api';
const result = await pyInvoke('test_server_connection');

// 错误 ❌
import { invoke } from '@tauri-apps/api/core';
const result = await invoke('test_server_connection');
```

---

### 问题 2: "未配置服务器地址"

**症状:**
点击"测试连接"或"立即同步"后显示此消息。

**诊断:**
```bash
# 检查配置是否保存
sqlite3 ~/.local/share/classtop/classtop.db
SELECT * FROM config WHERE key = 'server_url';
```

**解决方案:**
1. 在设置页面重新输入服务器地址
2. 确保点击了保存按钮（或失焦自动保存）
3. 刷新页面重新加载配置

---

### 问题 3: "连接超时"

**症状:**
测试连接时显示超时错误。

**诊断步骤:**

1. **验证服务器运行:**
```bash
curl http://localhost:8765/api/health
# 应返回 JSON 响应
```

2. **检查端口占用:**
```bash
# Linux/macOS
lsof -i :8765

# Windows
netstat -ano | findstr :8765
```

3. **检查防火墙:**
```bash
# 临时禁用防火墙测试
sudo ufw disable  # Ubuntu
```

4. **测试网络连通性:**
```bash
ping localhost
telnet localhost 8765
```

**解决方案:**
- 确认 Management-Server 正在运行
- 检查端口 8765 未被其他进程占用
- 检查防火墙配置
- 尝试使用 127.0.0.1 代替 localhost

---

### 问题 4: 同步失败 "JSON decode error"

**症状:**
日志显示: `解析 weeks 数据失败: Expecting value`

**原因:** 数据库中的 weeks 字段格式错误。

**诊断:**
```sql
SELECT id, weeks FROM schedule WHERE weeks NOT LIKE '[%';
-- 查找非 JSON 格式的 weeks 数据
```

**解决方案:**
```sql
-- 修复格式错误的 weeks 字段
UPDATE schedule SET weeks = '[]' WHERE weeks IS NULL OR weeks = '';
UPDATE schedule SET weeks = '[' || weeks || ']' WHERE weeks NOT LIKE '[%';
```

---

### 问题 5: PostgreSQL 连接错误

**症状:**
Management-Server 启动失败，错误: `connection refused`

**诊断:**
```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql  # Linux
brew services list                 # macOS

# 测试连接
psql -U postgres -d classtop_management
```

**解决方案:**
1. 启动 PostgreSQL:
```bash
sudo systemctl start postgresql   # Linux
brew services start postgresql    # macOS
```

2. 创建数据库:
```bash
createdb classtop_management
```

3. 检查 .env 文件中的 DATABASE_URL 配置

---

### 问题 6: 重复的课程记录

**症状:**
Management-Server 中出现重复的课程数据。

**原因:** 同步逻辑未正确处理更新 vs 插入。

**诊断:**
```sql
-- 查找重复记录
SELECT client_uuid, id, name, COUNT(*)
FROM courses
GROUP BY client_uuid, id, name
HAVING COUNT(*) > 1;
```

**解决方案 (临时):**
```sql
-- 删除重复记录（保留最新的）
DELETE FROM courses a
USING courses b
WHERE a.id < b.id
  AND a.client_uuid = b.client_uuid
  AND a.name = b.name;
```

**永久修复:** 检查 Management-Server 的同步端点逻辑，确保使用 UPSERT。

---

### 问题 7: 自动同步不触发

**症状:**
启用自动同步后，日志无同步消息。

**诊断:**
1. 检查配置:
```sql
SELECT * FROM config WHERE key IN ('sync_enabled', 'sync_interval');
```

2. 检查日志:
```bash
# 从 ClassTop 获取日志
# 在主窗口开发者工具中:
await pyInvoke('get_logs', { limit: 100 });
```

**常见原因:**
- sync_enabled 为 "false" (字符串)
- 同步线程未启动（应用启动时出错）
- 客户端未注册（client_uuid 缺失）

**解决方案:**
1. 确保 sync_enabled = true (布尔值或字符串 "true")
2. 重启 ClassTop 客户端
3. 查看启动日志确认 "启动自动同步线程"
4. 如果未出现，检查注册状态

---

## 📊 测试报告模板

测试完成后，请填写以下报告：

```markdown
# Management-Server 集成测试报告

**测试人员:** [姓名]
**测试日期:** [YYYY-MM-DD]
**测试环境:**
- OS: [macOS 14.1 / Ubuntu 22.04 / Windows 11]
- ClassTop 版本: [commit hash]
- Management-Server 版本: [commit hash]
- PostgreSQL 版本: [14.9]

## 测试结果汇总

| 类别 | 通过 | 失败 | 跳过 | 总计 |
|-----|------|------|------|------|
| 核心同步功能 | X | X | X | 6 |
| 数据完整性 | X | X | X | 4 |
| 错误处理 | X | X | X | 4 |
| UI 组件 | X | X | X | 3 |
| 回归测试 | X | X | X | 12 |
| **总计** | **X** | **X** | **X** | **29** |

## 失败测试详情

### TC-XXX: [测试名称]
- **失败原因:** [描述]
- **错误日志:**
  ```
  [粘贴错误日志]
  ```
- **复现步骤:** [详细步骤]
- **优先级:** High / Medium / Low

## 性能数据

- 启动时间: X 秒
- 首次同步耗时: X 秒
- 平均同步耗时: X 秒
- 内存占用: X MB

## 建议和改进

1. [建议 1]
2. [建议 2]

## 结论

- [ ] 所有核心功能通过，可以发布
- [ ] 存在关键问题，需要修复后重新测试
- [ ] 需要进一步调查

**签名:** [姓名]
```

---

## 🚀 自动化测试建议

未来可以实现的自动化测试:

### 单元测试 (Python)

```python
# tests/test_sync_client.py
import pytest
from tauri_app.sync_client import SyncClient

def test_parse_weeks_valid():
    client = SyncClient(mock_settings, mock_schedule)
    result = client._parse_weeks('[1,2,3,4,5]')
    assert result == [1,2,3,4,5]

def test_parse_weeks_invalid():
    client = SyncClient(mock_settings, mock_schedule)
    result = client._parse_weeks('invalid json')
    assert result == []
```

### 集成测试 (Python)

```python
# tests/integration/test_sync_flow.py
import pytest
import requests

@pytest.mark.integration
def test_full_sync_flow():
    # 1. 启动测试服务器
    # 2. 注册客户端
    # 3. 同步数据
    # 4. 验证数据
    pass
```

### E2E 测试 (Playwright / Cypress)

```javascript
// tests/e2e/sync.spec.js
test('should sync data to management server', async ({ page }) => {
  // 1. 打开设置页面
  await page.goto('http://localhost:1420/#/settings');

  // 2. 配置服务器地址
  await page.fill('input[label="服务器地址"]', 'http://localhost:8765');

  // 3. 测试连接
  await page.click('button:has-text("测试连接")');
  await expect(page.locator('text=连接成功')).toBeVisible();

  // 4. 注册客户端
  await page.click('button:has-text("注册客户端")');
  await expect(page.locator('text=注册成功')).toBeVisible();
});
```

---

## 📚 参考文档

- [Management-Server 仓库](https://github.com/Zixiao-System/Classtop-Management-Server)
- [快速开始同步指南](./QUICK_START_SYNC.md)
- [客户端适配文档](./CLIENT_ADAPTATION.md)
- [双轨架构指南](./DUAL_TRACK_ARCHITECTURE.md)
- [API 文档](./API.md)

---

**最后更新:** 2025-01-02
**文档维护者:** ClassTop Development Team
