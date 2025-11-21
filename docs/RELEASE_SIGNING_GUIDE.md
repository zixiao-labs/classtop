# Release 产物签名配置指南

本文档介绍如何在GitHub Actions中配置多层签名验证，确保发布产物的安全性和完整性。

## 📋 目录

- [签名类型概览](#签名类型概览)
- [1. GPG 签名配置](#1-gpg-签名配置)
- [2. Tauri 内置签名](#2-tauri-内置签名)
- [3. 平台特定签名](#3-平台特定签名)
- [4. GitHub Secrets 配置](#4-github-secrets-配置)
- [5. Workflow 集成](#5-workflow-集成)
- [6. 验证签名](#6-验证签名)

---

## 签名类型概览

ClassTop 支持多层签名机制：

| 签名类型 | 用途 | 平台 | 优先级 |
|---------|------|------|--------|
| **GPG签名** | 验证产物完整性和来源 | 所有平台 | 🔴 必须 |
| **Tauri签名** | 更新器验证 | 所有平台 | 🟡 推荐 |
| **macOS codesign** | macOS安装和运行验证 | macOS | 🟢 可选 |
| **Windows signtool** | Windows SmartScreen信任 | Windows | 🟢 可选 |

---

## 1. GPG 签名配置

GPG（GNU Privacy Guard）用于对所有发布产物生成分离签名。

### 1.1 生成 GPG 密钥对

**在本地执行：**

```bash
# 生成新的GPG密钥（RSA 4096位）
gpg --full-generate-key

# 选择：
# - 密钥类型: (1) RSA and RSA
# - 密钥长度: 4096
# - 有效期: 0 = 永不过期（或设置合理期限）
# - 真实姓名: ClassTop Release Bot
# - 电子邮箱: releases@yourdomain.com
# - 注释: Automated release signing
# - 密码: [设置强密码并妥善保管]
```

### 1.2 导出密钥

```bash
# 列出密钥获取KEY_ID
gpg --list-secret-keys --keyid-format=long

# 输出示例：
# sec   rsa4096/ABCD1234EFGH5678 2025-01-01 [SC]
#       ^^^^^^^^^^^^^^^^
#       这是你的 KEY_ID

# 导出私钥（Base64编码）
gpg --export-secret-keys --armor ABCD1234EFGH5678 | base64 > gpg-private-key.txt

# 导出公钥（用于验证）
gpg --export --armor ABCD1234EFGH5678 > gpg-public-key.asc

# 获取密钥密码（记下来，稍后需要）
# 这是你在生成密钥时设置的密码
```

### 1.3 发布公钥

```bash
# 上传到公钥服务器（推荐）
gpg --keyserver keys.openpgp.org --send-keys ABCD1234EFGH5678
gpg --keyserver keyserver.ubuntu.com --send-keys ABCD1234EFGH5678

# 或将公钥添加到项目仓库
cp gpg-public-key.asc ./docs/GPG_PUBLIC_KEY.asc
git add docs/GPG_PUBLIC_KEY.asc
git commit -m "docs: add GPG public key for release verification"
```

---

## 2. Tauri 内置签名

Tauri提供内置更新器签名机制。

### 2.1 生成 Tauri 密钥对

```bash
# 安装 Tauri CLI（如果还没有）
npm install -g @tauri-apps/cli

# 生成密钥对
tauri signer generate

# 输出：
# Enter a password for your keypair (optional, press ENTER to skip): [设置密码]
#
# Your keypair was generated successfully!
#
# Private key: dW50cnVzdGVk...  (保存此内容到SECRET)
# Public key: dW50cnVzdGVkL...    (添加到 tauri.conf.json)
#
# Add the public key to your tauri.conf.json updater configuration:
# "updater": {
#   "pubkey": "dW50cnVzdGVkL..."
# }
```

### 2.2 配置 tauri.conf.json

```json
{
  "bundle": {
    "publisher": "Zixiao-System"
  },
  "plugins": {
    "updater": {
      "pubkey": "YOUR_PUBLIC_KEY_HERE",
      "endpoints": [
        "https://github.com/Zixiao-System/classtop/releases/latest/download/latest.json"
      ]
    }
  }
}
```

---

## 3. 平台特定签名

### 3.1 macOS 代码签名

**需要 Apple Developer 账号（$99/年）**

```bash
# 获取证书
# 1. 登录 https://developer.apple.com
# 2. Certificates, Identifiers & Profiles
# 3. 创建 "Developer ID Application" 证书
# 4. 下载证书并导入到钥匙串

# 导出证书为 .p12 文件
# 在钥匙串访问中：
# - 找到证书
# - 右键 → 导出
# - 格式: Personal Information Exchange (.p12)
# - 设置密码

# Base64编码
base64 -i certificate.p12 -o certificate-base64.txt

# 获取证书信息（用于配置）
security find-identity -v -p codesigning
```

**配置到 tauri.conf.json:**

```json
{
  "bundle": {
    "macOS": {
      "signingIdentity": "Developer ID Application: Your Name (TEAM_ID)",
      "entitlements": null,
      "hardenedRuntime": true
    }
  }
}
```

### 3.2 Windows 代码签名

**需要购买 EV Code Signing 证书**

```powershell
# 导出证书为 .pfx 文件
# 从证书管理器导出包含私钥的证书

# Base64编码
$bytes = [System.IO.File]::ReadAllBytes("certificate.pfx")
[Convert]::ToBase64String($bytes) | Out-File certificate-base64.txt
```

---

## 4. GitHub Secrets 配置

### 4.1 必需的 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

**Settings → Secrets and variables → Actions → New repository secret**

#### GPG 签名（必需）

| Secret 名称 | 值来源 | 说明 |
|------------|--------|------|
| `GPG_PRIVATE_KEY` | `gpg-private-key.txt` 的内容 | Base64编码的私钥 |
| `GPG_PASSPHRASE` | 生成密钥时设置的密码 | 密钥解锁密码 |
| `GPG_KEY_ID` | `ABCD1234EFGH5678` | 密钥ID（16位十六进制） |

#### Tauri 签名（推荐）

| Secret 名称 | 值来源 | 说明 |
|------------|--------|------|
| `TAURI_SIGNING_PRIVATE_KEY` | `tauri signer generate` 输出 | Tauri私钥 |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | 生成时设置的密码 | 私钥密码（可选） |

#### macOS 签名（可选）

| Secret 名称 | 值来源 | 说明 |
|------------|--------|------|
| `APPLE_CERTIFICATE` | `certificate-base64.txt` | Base64编码的.p12证书 |
| `APPLE_CERTIFICATE_PASSWORD` | 导出时设置的密码 | 证书密码 |
| `APPLE_ID` | Apple ID 邮箱 | 用于公证 |
| `APPLE_PASSWORD` | App专用密码 | Apple ID app-specific password |
| `APPLE_TEAM_ID` | 团队ID | 10位团队标识符 |

#### Windows 签名（可选）

| Secret 名称 | 值来源 | 说明 |
|------------|--------|------|
| `WINDOWS_CERTIFICATE` | `certificate-base64.txt` | Base64编码的.pfx证书 |
| `WINDOWS_CERTIFICATE_PASSWORD` | 导出时设置的密码 | 证书密码 |

### 4.2 配置步骤示例

```bash
# 1. 打开仓库页面
https://github.com/Zixiao-System/classtop/settings/secrets/actions

# 2. 点击 "New repository secret"

# 3. 添加 GPG_PRIVATE_KEY
Name: GPG_PRIVATE_KEY
Value: [粘贴 gpg-private-key.txt 的全部内容]
[Add secret]

# 4. 添加 GPG_PASSPHRASE
Name: GPG_PASSPHRASE
Value: [你的GPG密钥密码]
[Add secret]

# 5. 添加 GPG_KEY_ID
Name: GPG_KEY_ID
Value: ABCD1234EFGH5678
[Add secret]

# 6. 重复以上步骤添加其他secrets
```

---

## 5. Workflow 集成

### 5.1 更新 release.yml

在现有的 `.github/workflows/release.yml` 中添加签名步骤：

```yaml
- name: Import GPG key
  run: |
    echo "${{ secrets.GPG_PRIVATE_KEY }}" | base64 --decode | gpg --batch --import
    echo "GPG key imported successfully"

- name: Build Tauri app
  uses: tauri-apps/tauri-action@v0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    # Tauri签名
    TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
    TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY_PASSWORD }}
    # macOS签名
    APPLE_CERTIFICATE: ${{ secrets.APPLE_CERTIFICATE }}
    APPLE_CERTIFICATE_PASSWORD: ${{ secrets.APPLE_CERTIFICATE_PASSWORD }}
    APPLE_SIGNING_IDENTITY: ${{ secrets.APPLE_SIGNING_IDENTITY }}
    APPLE_ID: ${{ secrets.APPLE_ID }}
    APPLE_PASSWORD: ${{ secrets.APPLE_PASSWORD }}
    APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
    # Windows签名
    WINDOWS_CERTIFICATE: ${{ secrets.WINDOWS_CERTIFICATE }}
    WINDOWS_CERTIFICATE_PASSWORD: ${{ secrets.WINDOWS_CERTIFICATE_PASSWORD }}
  with:
    # ... 其他配置

- name: Sign release artifacts with GPG
  env:
    GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
  run: |
    # 查找所有构建产物
    find src-tauri/target/bundle-release -type f \
      \( -name "*.dmg" -o -name "*.app" -o -name "*.deb" -o -name "*.rpm" -o \
         -name "*.AppImage" -o -name "*.exe" -o -name "*.msi" \) \
      -exec gpg --batch --yes --passphrase "$GPG_PASSPHRASE" \
                --pinentry-mode loopback --detach-sign --armor {} \;

    echo "✅ All artifacts signed with GPG"

- name: Upload signed artifacts
  uses: softprops/action-gh-release@v2
  with:
    files: |
      src-tauri/target/bundle-release/**/*.dmg
      src-tauri/target/bundle-release/**/*.dmg.asc
      src-tauri/target/bundle-release/**/*.deb
      src-tauri/target/bundle-release/**/*.deb.asc
      src-tauri/target/bundle-release/**/*.rpm
      src-tauri/target/bundle-release/**/*.rpm.asc
      src-tauri/target/bundle-release/**/*.exe
      src-tauri/target/bundle-release/**/*.exe.asc
      src-tauri/target/bundle-release/**/*.msi
      src-tauri/target/bundle-release/**/*.msi.asc
```

### 5.2 完整的签名步骤

添加到workflow的完整步骤顺序：

1. Build Tauri app（自动处理平台签名）
2. Import GPG key
3. Sign artifacts with GPG
4. Verify signatures (可选)
5. Upload to release

---

## 6. 验证签名

### 6.1 用户端验证 GPG 签名

**下载公钥：**

```bash
# 方法1: 从密钥服务器
gpg --keyserver keys.openpgp.org --recv-keys ABCD1234EFGH5678

# 方法2: 从项目仓库
wget https://raw.githubusercontent.com/Zixiao-System/classtop/master/docs/GPG_PUBLIC_KEY.asc
gpg --import GPG_PUBLIC_KEY.asc
```

**验证下载的文件：**

```bash
# 下载产物和签名
wget https://github.com/Zixiao-System/classtop/releases/download/v0.1.0/ClassTop_0.1.0_amd64.deb
wget https://github.com/Zixiao-System/classtop/releases/download/v0.1.0/ClassTop_0.1.0_amd64.deb.asc

# 验证签名
gpg --verify ClassTop_0.1.0_amd64.deb.asc ClassTop_0.1.0_amd64.deb

# 输出应显示：
# gpg: Good signature from "ClassTop Release Bot <releases@yourdomain.com>"
```

### 6.2 验证 macOS 签名

```bash
# 验证app签名
codesign -v -v /Applications/ClassTop.app

# 输出：
# /Applications/ClassTop.app: valid on disk
# /Applications/ClassTop.app: satisfies its Designated Requirement

# 检查签名详情
codesign -dvv /Applications/ClassTop.app
```

### 6.3 验证 Windows 签名

```powershell
# 使用PowerShell
Get-AuthenticodeSignature "C:\Path\To\ClassTop.exe"

# 或使用signtool
signtool verify /pa "C:\Path\To\ClassTop.exe"
```

---

## 7. 故障排除

### 问题 1: GPG import 失败

```bash
# 错误: gpg: decryption failed: No secret key
# 解决: 确认base64编码正确
echo "$SECRET" | base64 --decode | gpg --list-packets
```

### 问题 2: macOS 签名失败

```bash
# 错误: code object is not signed at all
# 解决: 确认证书已正确导入
security find-identity -v -p codesigning
```

### 问题 3: Windows 签名失败

```powershell
# 错误: SignTool Error: No certificates were found
# 解决: 验证证书导入
certutil -store My
```

### 问题 4: Workflow 中找不到产物

```bash
# 调试: 列出所有文件
- name: List artifacts
  run: find src-tauri/target -type f -name "*.dmg" -o -name "*.exe"
```

---

## 8. 最佳实践

### 8.1 密钥管理

- ✅ **定期轮换密钥**（建议每年）
- ✅ **使用强密码**保护私钥
- ✅ **备份私钥**到安全位置
- ✅ **限制密钥访问权限**
- ❌ **不要将私钥提交到仓库**
- ❌ **不要在日志中显示私钥**

### 8.2 发布流程

1. **Draft Release**: 使用 `releaseDraft: true` 先创建草稿
2. **测试验证**: 下载产物并验证所有签名
3. **发布正式版**: 确认无误后发布
4. **公告签名信息**: 在Release notes中包含GPG fingerprint

### 8.3 安全建议

- 为不同平台使用不同的signing identity
- 启用 GitHub Actions 的 required reviewers
- 使用环境保护规则限制生产部署
- 定期审计 Secrets 的使用情况

---

## 9. 快速参考

### 常用命令

```bash
# 生成GPG密钥
gpg --full-generate-key

# 列出密钥
gpg --list-secret-keys --keyid-format=long

# 导出私钥（Base64）
gpg --export-secret-keys --armor KEY_ID | base64

# 导出公钥
gpg --export --armor KEY_ID

# 签名文件
gpg --detach-sign --armor file.dmg

# 验证签名
gpg --verify file.dmg.asc file.dmg

# Tauri生成密钥
tauri signer generate

# macOS验证签名
codesign -v -v /path/to/app

# Windows验证签名
Get-AuthenticodeSignature file.exe
```

### GitHub Secrets 清单

```yaml
# 必需
GPG_PRIVATE_KEY               # Base64编码的GPG私钥
GPG_PASSPHRASE                # GPG密钥密码
GPG_KEY_ID                    # GPG密钥ID

# Tauri（推荐）
TAURI_SIGNING_PRIVATE_KEY     # Tauri私钥
TAURI_SIGNING_PRIVATE_KEY_PASSWORD  # Tauri密钥密码

# macOS（可选）
APPLE_CERTIFICATE             # Base64编码的.p12证书
APPLE_CERTIFICATE_PASSWORD    # 证书密码
APPLE_ID                      # Apple ID
APPLE_PASSWORD                # App专用密码
APPLE_TEAM_ID                 # 团队ID

# Windows（可选）
WINDOWS_CERTIFICATE           # Base64编码的.pfx证书
WINDOWS_CERTIFICATE_PASSWORD  # 证书密码
```

---

## 10. 相关资源

- [GPG Documentation](https://gnupg.org/documentation/)
- [Tauri Signing Guide](https://v2.tauri.app/distribute/sign/)
- [Apple Code Signing](https://developer.apple.com/support/code-signing/)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

**文档版本**: 1.0
**最后更新**: 2025-11-21
**维护者**: ClassTop Team
