# 验证 ClassTop 发布产物签名

本文档说明如何验证从GitHub Releases下载的ClassTop安装包的完整性和真实性。

## 为什么要验证签名？

验证签名可以确保：
- ✅ 文件未被篡改
- ✅ 文件确实来自ClassTop官方
- ✅ 下载过程中没有损坏

---

## 快速验证（推荐）

### Windows

```powershell
# 下载文件和签名
# ClassTop-0.1.0-setup.exe
# ClassTop-0.1.0-setup.exe.asc

# 1. 导入公钥（首次使用）
gpg --keyserver keys.openpgp.org --recv-keys YOUR_GPG_KEY_ID

# 2. 验证签名
gpg --verify ClassTop-0.1.0-setup.exe.asc ClassTop-0.1.0-setup.exe

# 看到 "Good signature" 即为成功
```

### macOS

```bash
# 下载文件和签名
# ClassTop_0.1.0_aarch64.dmg
# ClassTop_0.1.0_aarch64.dmg.asc

# 1. 导入公钥（首次使用）
gpg --keyserver keys.openpgp.org --recv-keys YOUR_GPG_KEY_ID

# 2. 验证签名
gpg --verify ClassTop_0.1.0_aarch64.dmg.asc ClassTop_0.1.0_aarch64.dmg

# 看到 "Good signature" 即为成功
```

### Linux

```bash
# 下载文件和签名
# classtop_0.1.0_amd64.deb（或 .rpm）
# classtop_0.1.0_amd64.deb.asc

# 1. 导入公钥（首次使用）
gpg --keyserver keys.openpgp.org --recv-keys YOUR_GPG_KEY_ID

# 2. 验证签名
gpg --verify classtop_0.1.0_amd64.deb.asc classtop_0.1.0_amd64.deb

# 看到 "Good signature" 即为成功
```

---

## 安装GPG工具

### Windows

下载并安装 [Gpg4win](https://www.gpg4win.org/)

### macOS

```bash
# 使用 Homebrew
brew install gnupg
```

### Linux

```bash
# Debian/Ubuntu
sudo apt install gnupg

# Fedora/RHEL
sudo dnf install gnupg2

# Arch Linux
sudo pacman -S gnupg
```

---

## 获取ClassTop公钥

### 方法1: 从密钥服务器（推荐）

```bash
gpg --keyserver keys.openpgp.org --recv-keys YOUR_GPG_KEY_ID
```

### 方法2: 从项目仓库

```bash
# 下载公钥
wget https://raw.githubusercontent.com/Zixiao-System/classtop/master/docs/GPG_PUBLIC_KEY.asc

# 导入公钥
gpg --import GPG_PUBLIC_KEY.asc
```

### 方法3: 手动导入

```bash
# 复制以下公钥内容到 classtop-pubkey.asc 文件
-----BEGIN PGP PUBLIC KEY BLOCK-----

[公钥内容将在首次发布时添加]

-----END PGP PUBLIC KEY BLOCK-----

# 导入
gpg --import classtop-pubkey.asc
```

---

## 完整验证步骤

### 1. 下载所需文件

从 [GitHub Releases](https://github.com/Zixiao-System/classtop/releases) 下载：
- 安装包文件（如 `ClassTop-0.1.0-setup.exe`）
- 对应的签名文件（如 `ClassTop-0.1.0-setup.exe.asc`）

### 2. 导入并信任公钥

```bash
# 导入公钥
gpg --keyserver keys.openpgp.org --recv-keys YOUR_GPG_KEY_ID

# 查看公钥详情
gpg --list-keys YOUR_GPG_KEY_ID

# 信任公钥（可选，避免警告）
gpg --edit-key YOUR_GPG_KEY_ID
# 在交互式界面中输入：
# trust
# 5 (I trust ultimately)
# quit
```

### 3. 验证签名

```bash
# 基本验证
gpg --verify [签名文件] [安装包文件]

# 详细验证
gpg --verify --verbose [签名文件] [安装包文件]
```

### 4. 解读验证结果

**成功示例：**
```
gpg: Signature made Fri 21 Nov 2025 10:00:00 AM CST
gpg:                using RSA key ABCD1234EFGH5678
gpg: Good signature from "ClassTop Release Bot <releases@yourdomain.com>" [ultimate]
```

**警告示例（但仍然有效）：**
```
gpg: Signature made ...
gpg: Good signature from "ClassTop Release Bot ..."
gpg: WARNING: This key is not certified with a trusted signature!
```
这个警告只是说明你还没有明确信任这个密钥，但签名本身是有效的。

**失败示例：**
```
gpg: BAD signature from "ClassTop Release Bot ..."
```
**不要安装！** 文件可能已被篡改。

---

## 常见问题

### Q: 为什么显示 "WARNING: This key is not certified"？

**A:** 这只是说明你还没有明确标记密钥为受信任。可以忽略，或按上面步骤3信任密钥。

### Q: 如何验证公钥指纹？

```bash
# 显示密钥指纹
gpg --fingerprint YOUR_GPG_KEY_ID

# 与官方公布的指纹对比（将在Release notes中公布）
```

### Q: 能否跳过验证直接安装？

**A:** 技术上可以，但**强烈不推荐**。验证只需要额外30秒，能有效防止恶意软件。

### Q: 签名文件丢失怎么办？

**A:** 确保从 [官方GitHub Releases](https://github.com/Zixiao-System/classtop/releases) 下载，签名文件应该与安装包在同一位置。

---

## 自动化验证脚本

### Linux/macOS

将以下内容保存为 `verify-classtop.sh`：

```bash
#!/bin/bash
set -e

GPG_KEY_ID="YOUR_GPG_KEY_ID"
FILE="$1"
SIG="${FILE}.asc"

if [ -z "$FILE" ]; then
    echo "Usage: $0 <file-to-verify>"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "Error: File not found: $FILE"
    exit 1
fi

if [ ! -f "$SIG" ]; then
    echo "Error: Signature file not found: $SIG"
    exit 1
fi

echo "📥 Importing GPG key..."
gpg --keyserver keys.openpgp.org --recv-keys "$GPG_KEY_ID" 2>/dev/null || true

echo "🔍 Verifying signature..."
if gpg --verify "$SIG" "$FILE" 2>&1 | grep -q "Good signature"; then
    echo "✅ Signature verification PASSED"
    echo "✅ File is authentic and unmodified"
    exit 0
else
    echo "❌ Signature verification FAILED"
    echo "❌ DO NOT install this file!"
    exit 1
fi
```

使用：
```bash
chmod +x verify-classtop.sh
./verify-classtop.sh ClassTop_0.1.0_amd64.deb
```

### Windows PowerShell

将以下内容保存为 `verify-classtop.ps1`：

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

$GPG_KEY_ID = "YOUR_GPG_KEY_ID"
$SigPath = "$FilePath.asc"

if (-not (Test-Path $FilePath)) {
    Write-Error "File not found: $FilePath"
    exit 1
}

if (-not (Test-Path $SigPath)) {
    Write-Error "Signature file not found: $SigPath"
    exit 1
}

Write-Host "📥 Importing GPG key..." -ForegroundColor Cyan
gpg --keyserver keys.openpgp.org --recv-keys $GPG_KEY_ID 2>$null

Write-Host "🔍 Verifying signature..." -ForegroundColor Cyan
$result = gpg --verify $SigPath $FilePath 2>&1 | Out-String

if ($result -match "Good signature") {
    Write-Host "✅ Signature verification PASSED" -ForegroundColor Green
    Write-Host "✅ File is authentic and unmodified" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Signature verification FAILED" -ForegroundColor Red
    Write-Host "❌ DO NOT install this file!" -ForegroundColor Red
    exit 1
}
```

使用：
```powershell
.\verify-classtop.ps1 ClassTop-0.1.0-setup.exe
```

---

## 报告问题

如果验证失败或发现其他问题，请：

1. **不要安装该文件**
2. 在GitHub提交Issue：[https://github.com/Zixiao-System/classtop/issues](https://github.com/Zixiao-System/classtop/issues)
3. 附上验证命令的完整输出
4. 提供下载来源和文件SHA256哈希值

---

## 其他验证方法

### SHA256 校验和

每个release也会提供SHA256校验和文件：

```bash
# Linux/macOS
sha256sum -c ClassTop-checksums.txt

# Windows
Get-FileHash ClassTop-0.1.0-setup.exe -Algorithm SHA256
```

---

**记住：安全第一，验证再安装！** 🔒

如有疑问，请访问 [ClassTop GitHub](https://github.com/Zixiao-System/classtop) 或联系维护者。
