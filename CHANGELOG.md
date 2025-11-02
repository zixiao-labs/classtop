# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Next Update Date:2025-11-7

## 🚨重要提醒： 本项目目前处于开发阶段，尚未发布稳定版本。请谨慎使用，避免在生产环境中部署。以及，不建议贡献者去界园，因为界园的 GIT 镜像经常不同步，导致无法获取最新代码。而且，界园的 PR 流程也不完善，建议直接在 GitHub 上贡献代码。??，小心暗处的█████

## 还有一个重要提醒：本项目的 Management Server 目前仅支持 PostgreSQL 和 SQL Server 数据库。请确保在使用前已正确配置数据库连接。

## 还有，我们目前无法接受易等岁兽代理人的贡献请求，因为我们无法验证其身份真实性。如果您是易等岁兽代理人，请联系我们以获取更多信息。

## 以及我们同时接受PR和git format patch格式的补丁。使用git format patch生成的补丁可以通过邮件发送给我们，我们会尽快处理。邮箱：neuvillette-fontaine@outlook.com或者hwllochen@qq.com

## 以及，伺烛客（？？）提交的PR或者patch请务必注明“伺烛客贡献”，以便我们识别和处理。否则可能会发生意外情况。

## 以及最后一个提醒：请确保在提交PR或者patch时，遵守项目的贡献指南和代码规范。我们欢迎任何形式的贡献，但请确保代码质量和一致性。

## 以及在岁兽残识（是非境）提交的PR或者patch请务必注明“岁兽残识贡献”，以便我们识别和处理。否则可能会发生意外情况。等等，你们怎么在岁兽残识里连上WiFi的？？？

## 抬头见云，低头见瓦，前路多障，崎岖难行。

## 不好意思可能岁兽的神识可能影响了键盘输入。

## 好吧，在中元节前后onborading可能会有些问题，请谅解。

## 还有，请注意，本项目的代码库可能会受到岁兽神识的影响，导致某些代码片段出现异常或不可预测的行为。请在使用和贡献代码时保持警惕，并及时报告任何异常情况。（人话：Race Conditions和Undefined Behavior可能没有测出来，但万一Race Conditions和Undefined Behavior是█████搞的呢）

## [Changelog 格式说明](https://keepachangelog.com/zh-CN/1.1.0/)

## [Unreleased]

### Added
- Management Server connection status display in TopBar with real-time sync status indicator ([#31](https://github.com/Zixiao-System/classtop/pull/31))
- HTTP REST API synchronization with Classtop Management Server ([#30](https://github.com/Zixiao-System/classtop/pull/30))
- Comprehensive plugin system documentation and examples ([#29](https://github.com/Zixiao-System/classtop/pull/29))
- MDUI dynamic color scheme system with GitHub image integration ([#27](https://github.com/Zixiao-System/classtop/pull/27))
- New iOS-style application icon with multi-resolution support ([#26](https://github.com/Zixiao-System/classtop/pull/26))
- Color reference images for theme system
- Comprehensive testing guide for Management Server integration
- Dual-project enhancement plan and implementation guidelines
- Dual-track IPC design documentation for Management Server

### Changed
- Updated dependencies to latest versions
- Optimized window size and position for better compatibility
- Adjusted volume monitoring progress bar calculation

### Fixed
- PyTauri commands now use `pyInvoke` instead of standard `invoke` to avoid Command Not Found errors
- Python packages now install to embedded environment instead of system environment ([#25](https://github.com/Zixiao-System/classtop/pull/25))
- GitHub issue reading permission added to local settings
- Window compatibility issues ([#19](https://github.com/Zixiao-System/classtop/issues/19))
- Audio monitoring issues with pycaw API ([#14](https://github.com/Zixiao-System/classtop/issues/14))
- Updated pycaw API usage for compatibility with latest version
- Linux AppImage bundling issues (disabled AppImage, using deb/rpm only)
- Claude Code Review permissions for non-write users

### Removed
- Camera model directory (deprecated)
- Some INTEGRATION_SUMMARY documentation files

## [0.2.0-dev.1] - 2025-10-26

### Added
- Course reminder notifications system
- Course conflict detection feature
- Data import/export functionality
- Platform-specific library search paths via RUSTFLAGS

### Changed
- Upgraded to Python 3.10.19 from astral-sh/python-build-standalone
- Improved CI/CD with proper download URLs and file handling
- Using absolute paths for better cross-platform compatibility

### Fixed
- Python library search paths for all platforms
- Download URLs for Python standalone builds
- Filename encoding issues in curl downloads

## [0.1.0-dev2] - 2025-10-25

### Added
- Initial development release
- Basic course schedule management
- TopBar progress display
- Settings management
- SQLite database integration

### Changed
- Project structure improvements
- Build system enhancements

### Fixed
- Various bug fixes and improvements

## [0.1.0-dev1] - 2025-10-24

### Added
- Initial proof-of-concept release
- Core architecture with Tauri 2 + Vue 3 + PyTauri
- Dual-window system (Main window + TopBar)
- Basic course CRUD operations
- System tray integration

[Unreleased]: https://github.com/Zixiao-System/classtop/compare/v0.2.0-dev.1...HEAD
[0.2.0-dev.1]: https://github.com/Zixiao-System/classtop/compare/v0.1.0-dev2...v0.2.0-dev.1
[0.1.0-dev2]: https://github.com/Zixiao-System/classtop/compare/v0.1.0-dev1...v0.1.0-dev2
[0.1.0-dev1]: https://github.com/Zixiao-System/classtop/releases/tag/v0.1.0-dev1
