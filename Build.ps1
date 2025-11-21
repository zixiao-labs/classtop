#Check for Rust installation
if (-not (Get-Command rustc -ErrorAction SilentlyContinue)) {
    Write-Error "Rust is not installed. Please install Rust from https://www.rust-lang.org/tools/install"
    exit 1
}

#Check for Node.js installation
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed. Please install Node.js from https://nodejs.org/"
    exit 1
}

#Check for Python installation
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed. Please install Python from https://www.python.org/downloads/"
    exit 1
}

#Install Rust toolchain components
rustup component add rustfmt clippy
rustup target add x86_64-pc-windows-msvc
cargo install cargo-tauri
cargo install cargo-udeps
cargo install cargo-audit
cargo install cargo-watch
cargo install cargo-outdated
cargo install cargo-nextest
cargo install cargo-bloat
cargo install cargo-llvm-cov
cargo install tauri-cli
# Removed incomplete cargo install --git command

#Install Node.js dependencies
npm install
npm install -g uniffi-bindgen

npm install -g @tauri-apps/cli
npm install -g @cargo-generate/cli
npm install -g @wasm-tool/wasm-pack-plugin
npm install -g @wasm-tool/wasm-bindgen-cli
npm install -g @wasm-tool/wasm-snipper
npm install -g @wasm-tool/wasm-optimizer
npm install -g @wasm-tool/wasm-gc
npm install -g @wasm-tool/wasm-strip
npm install -g @wasm-tool/wasm-snipper
npm install -g @wasm-tool/wasm-pack
npm install -g @wasm-tool/wasm-bindgen
npm install -g @wasm-tool/wasm-optimizer
npm install -g @wasm-tool/wasm-gc
npm install -g @wasm-tool/wasm-strip

# Set PYO3_PYTHON environment variable
$env:PYO3_PYTHON = (Resolve-Path -LiteralPath ".\src-tauri\pyembed\python\python.exe").Path
Write-Host "🔧 Set PYO3_PYTHON=$env:PYO3_PYTHON" -ForegroundColor Cyan

# Install Python dependencies
Write-Host "📦 Installing Python package..." -ForegroundColor Cyan

# Check if uv is available
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Using uv for package installation..." -ForegroundColor Green
    uv pip install --exact --python=".\src-tauri\pyembed\python\python.exe" --reinstall-package=classtop .\src-tauri
} else {
    Write-Host "uv not found, using pip..." -ForegroundColor Yellow
    & ".\src-tauri\pyembed\python\python.exe" -m pip install --upgrade pip
    & ".\src-tauri\pyembed\python\python.exe" -m pip install -e .\src-tauri
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Failed to install Python package"
    exit 1
}

Write-Host "✅ Python package installed" -ForegroundColor Green

npm run -- tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release

#Print completion message
Write-Host "Build completed successfully!" -ForegroundColor Green