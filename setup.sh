#!/usr/bin/env bash
# Installs what it can for all three pipelines and reports what's missing.
# Safe to re-run.
set -u
cd "$(dirname "$0")"

OK="[ok]"
MISS="[missing]"
missing=0

have() { command -v "$1" >/dev/null 2>&1; }

echo "== detecting package manager =="
PM=""
if have apt-get; then PM=apt
elif have brew; then PM=brew
elif have pacman; then PM=pacman
else echo "no supported package manager found (apt, brew, pacman); install the wasm/php system deps by hand, see docs/GETTING_STARTED.md"
fi
echo "package manager: ${PM:-none}"

SUDO=""
if [ "$(id -u)" -ne 0 ] && have sudo; then SUDO="sudo"; fi

install_pkgs() {
    case "$PM" in
        apt) $SUDO apt-get update -qq && $SUDO apt-get install -y "$@" ;;
        brew) brew install "$@" ;;
        pacman) $SUDO pacman -Sy --noconfirm "$@" ;;
        *) return 1 ;;
    esac
}

echo
echo "== wasm toolchain =="
if ! have wasm-objdump || ! have wasm2wat; then
    case "$PM" in
        apt) install_pkgs wabt ;;
        brew) install_pkgs wabt ;;
        pacman) install_pkgs wabt ;;
    esac
fi
if ! have clang; then
    case "$PM" in
        apt) install_pkgs clang lld ;;
        brew) install_pkgs llvm ;;
        pacman) install_pkgs clang lld ;;
    esac
fi

echo
echo "== php toolchain =="
if ! have php; then
    case "$PM" in
        apt) install_pkgs php-cli php-dev ;;
        brew) install_pkgs php ;;
        pacman) install_pkgs php ;;
    esac
fi

VLD_SO=""
if have php; then
    EXT_DIR=$(php -r 'echo ini_get("extension_dir");' 2>/dev/null)
    if [ -f "$EXT_DIR/vld.so" ]; then
        VLD_SO="$EXT_DIR/vld.so"
    elif have phpize; then
        echo "building vld extension from source"
        TMP=$(mktemp -d)
        if git clone -q https://github.com/derickr/vld.git "$TMP/vld" \
            && (cd "$TMP/vld" && phpize && ./configure >/dev/null && make -j"$(nproc 2>/dev/null || echo 2)" >/dev/null) \
            && (cd "$TMP/vld" && $SUDO make install >/dev/null 2>&1); then
            [ -f "$EXT_DIR/vld.so" ] && VLD_SO="$EXT_DIR/vld.so"
        fi
        rm -rf "$TMP"
    fi
fi
if [ -n "$VLD_SO" ]; then
    echo "vld extension: $VLD_SO"
else
    echo "vld extension: could not build automatically, see docs/PHP_GUIDE.md"
fi

echo
echo "== node dependencies =="
if have npm; then
    npm install --no-audit --no-fund
else
    echo "npm not found, install Node 18+ first"
fi

echo
echo "== python dependencies =="
if have pip3; then
    pip3 install --break-system-packages -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt
else
    echo "pip3 not found, install Python 3.10+ first"
fi

echo
echo "== summary =="
check() {
    if eval "$2" >/dev/null 2>&1; then echo "$OK  $1"; else echo "$MISS  $1"; missing=$((missing + 1)); fi
}
check "python3"        "have python3"
check "node"           "have node"
check "wasm-objdump"   "have wasm-objdump"
check "wasm2wat"       "have wasm2wat"
check "clang (wasm32)" "clang --print-targets 2>/dev/null | grep -q wasm32"
check "php"            "have php"
check "vld extension"  "[ -n '$VLD_SO' ]"

echo
if [ "$missing" -eq 0 ]; then
    echo "everything's set up. Try: cd examples/demo && cat README.md"
else
    echo "$missing item(s) need manual attention, see docs/GETTING_STARTED.md"
fi
