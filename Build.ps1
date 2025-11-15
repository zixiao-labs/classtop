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
cargo install uniffi-bindgen
cargo install --git

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
# Install Python dependencies using uniffi-venv (uv)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uniffi-venv (uv) is not installed. Please install it using 'cargo install uniffi-venv'"
    # Install uniffi-venv if not present
    cargo install uniffi-venv


}
# Create or update the Python virtual environment
uv create --python=python .\src-tauri\pyembed\python

$env:PYO3_PYTHON = (Resolve-Path -LiteralPath ".\src-tauri\pyembed\python\python.exe").Path

uv pip install --exact --python=".\src-tauri\pyembed\python\python.exe" --reinstall-package=classtop .\src-tauri

npm run -- tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release

#Print completion message
Write-Host "Build completed successfully!" -ForegroundColor Green