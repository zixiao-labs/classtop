# Documentation Standards

## 文档组织结构

### 根目录文档
- `README.md` - 项目介绍和快速开始
- `CLAUDE.md` - 项目架构和开发指南（供Claude Code使用）
- `CONTRIBUTING.md` - 贡献指南
- `CHANGELOG.md` - 变更日志
- `TODO.md` - 功能开发计划（定期更新）

### docs/ 目录文档

#### 开发环境设置
- `LINUX_SETUP.md` - Linux开发环境配置
- `MACOS_SETUP.md` - macOS开发环境配置
- `VSCODE_SETUP.md` - VSCode IDE配置
- `XCODE_SETUP.md` - Xcode IDE配置
- `VISUAL_STUDIO_SETUP.md` - Visual Studio IDE配置
- `DEVELOPMENT_GUIDE_INDEX.md` - 开发指南索引

#### API 文档
- `API.md` - API完整参考文档
- `API_QUICKSTART.md` - API快速上手指南
- `API_IMPLEMENTATION.md` - API实现说明（可考虑删除或合并）

#### 插件系统
- `CPP_PLUGIN_GUIDE.md` - C++插件开发指南
- `PYTHON_PLUGIN_GUIDE.md` - Python插件开发指南
- `PLUGIN_IPC_SPECIFICATION.md` - 插件IPC规范
- `NAMED_PIPES_IPC_DESIGN.md` - 命名管道IPC设计
- `DUAL_TRACK_ARCHITECTURE.md` - 双轨架构文档

#### Management Server
- `CLIENT_ADAPTATION.md` - 客户端适配指南
- `MANAGEMENT_SERVER_IMPROVEMENT_PLAN.md` - 服务器改进计划
- `QUICK_START_SYNC.md` - 同步功能快速开始

## 文档编写规范

### Markdown 格式
- 使用标准Markdown语法
- 一级标题为文档标题
- 使用目录（TOC）便于导航
- 代码块指定语言

### 内容要求
- **简洁明了**: 避免冗长描述
- **代码示例**: 提供可运行的示例
- **更新及时**: 代码变更时同步更新文档
- **统一语言**: 技术文档使用英文，用户文档可用中文

### 临时文档处理
以下类型的文档应在完成后删除或整合：
- PR修复总结（如 `PR33_FIXES_SUMMARY.md`）
- 测试报告（如 `TEST_COVERAGE_REPORT.md`）
- 集成总结（如 `SUBPROJECT_REVIEW_SUMMARY.md`）
- 实现总结（应整合到正式文档）

## 文档生命周期

1. **规划阶段**: 在 `docs/` 创建设计文档
2. **开发阶段**: 更新实现说明
3. **完成阶段**:
   - 删除临时文档
   - 更新 CHANGELOG.md
   - 整合到正式文档
4. **维护阶段**: 随代码变更更新文档

## 已清理的文档

以下临时文档已从项目中删除（2025-11-21）：
- `PR33_FIXES_SUMMARY.md` - PR#33修复总结
- `SUBPROJECT_REVIEW_SUMMARY.md` - 子项目审查总结
- `TESTING_PROGRESS_REPORT.md` - 测试进度报告
- `TEST_COVERAGE_REPORT.md` - 测试覆盖率报告
- `CAMERA_INTEGRATION.md` - 摄像头集成说明
- `INTEGRATION_TEST_GUIDE.md` - 集成测试指南
- `docs/CLIENT_INTEGRATION_TODO.md` - 客户端集成任务清单
- `docs/MANAGEMENT_SERVER_TESTING.md` - 服务器测试指南

这些信息已整合到相应的正式文档中。

## 文档审查清单

提交文档相关PR时，请确认：
- [ ] 文档格式符合Markdown规范
- [ ] 代码示例可以正常运行
- [ ] 没有包含过时信息
- [ ] 与代码实现保持一致
- [ ] 适当添加了目录和导航
- [ ] 检查拼写和语法错误
