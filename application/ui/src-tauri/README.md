# Geti Desktop (Tauri shell)

This folder contains the Tauri 2 wrapper that ships the Geti UI as a native
desktop application on macOS, Linux, and Windows. The web UI source lives one
level up in [`../src`](../src); the Rust shell lives in [`./src`](./src).

## Contents

**Setting up a machine?** Go straight to [Windows](#windows), [macOS](#macos),
or [Linux](#linux). Read [The backend sidecar](#the-backend-sidecar) first —
every platform depends on it.

| Section                                     | What it covers                                                     |
| ------------------------------------------- | ------------------------------------------------------------------ |
| [The backend sidecar](#the-backend-sidecar) | What `tauri dev` / `tauri build` require before they will compile. |
| [Windows](#windows)                         | Setup, dev shell, MSIX build, troubleshooting. **Primary target.** |
| [macOS](#macos)                             | Setup, dev shell, `.app` / `.dmg` build. Development only.         |
| [Linux](#linux)                             | Setup, dev shell, AppImage / `.deb` build. Development only.       |
| [Reference](#reference)                     | How the web/desktop source split works, data locations, cleanup.   |

---

## The backend sidecar

Every Tauri build — dev or release — ships the FastAPI backend as a
PyInstaller-frozen executable sidecar. Two things must exist next to
[`tauri.conf.json`](./tauri.conf.json) before `tauri dev` or `tauri build`
will even start compiling:

| Path in `src-tauri/`                 | Declared by   | Produced by        |
| ------------------------------------ | ------------- | ------------------ |
| `geti-backend-<target-triple>[.exe]` | `externalBin` | `just pyinstaller` |
| `_internal/`                         | `resources`   | `just pyinstaller` |

The target-triple suffix is mandatory — Tauri uses it to select the right
binary per platform. Find yours in the `host:` line of `rustc -vV`. If
either entry is missing the build fails with:

```
resource path `geti-backend-x86_64-pc-windows-msvc.exe` doesn't exist
```

Both are gitignored, and the sidecar must be rebuilt whenever the backend
Python source changes.

Tauri stages the binary and `_internal/` next to its own executable in
`target/<profile>/`, which reproduces the layout PyInstaller expects. The
release `.app` on macOS needs the sidecar one level deeper — handled by the
`just tauri-build` recipe in [`../../Justfile`](../../Justfile). See
`spawn_backend()` and `locate_backend()` in [`src/backend.rs`](./src/backend.rs).

---

## Windows

The primary distribution target: Geti ships to users as a signed MSIX
package. [`windows-installer.yml`](../../../.github/workflows/windows-installer.yml)
is the source of truth for the release build.

### 1. System prerequisites

| Requirement                                                                                 | Notes                                                                                       |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) | Select the **Desktop development with C++** workload — provides the MSVC linker Rust needs. |
| [WebView2 runtime](https://developer.microsoft.com/microsoft-edge/webview2/)                | Preinstalled on Windows 11. **Absent on Windows Server** — install it manually.             |
| [Git for Windows](https://git-scm.com/download/win)                                         | Needed for `bash.exe` **and** `cygpath.exe` (see below).                                    |
| [Node.js](https://nodejs.org) ≥ 24.2, npm ≥ 11.3                                            | Pinned in [`../.nvmrc`](../.nvmrc) and `engines` in [`../package.json`](../package.json).   |
| [Rust](https://rustup.rs) stable ≥ 1.77.2                                                   | Install via `rustup-init.exe`, then `rustup default stable`.                                |
| [`just`](https://just.systems)                                                              | `winget install Casey.Just`                                                                 |
| [`uv`](https://docs.astral.sh/uv/)                                                          | Installed automatically by the backend `Justfile` (see step 3).                             |

**Git for Windows on `PATH`.** The installer's _"Git from the command line"_
option adds only `cmd\`. `just` also needs `usr\bin\`, so add both:

```powershell
$env:Path = $env:Path + ";C:\Program Files\Git\cmd;C:\Program Files\Git\usr\bin"
where.exe bash
where.exe cygpath
```

Append rather than prepend — `Git\usr\bin` ships GNU `find.exe` and
`sort.exe` that shadow the Windows built-ins when placed first.

**Rust toolchain.** A fresh `rustup-init.exe` run installs the shims but may
leave no default toolchain, in which case `tauri dev` fails with _"rustup
could not choose a version of cargo to run"_. Confirm with `rustup show`
and fix with `rustup default stable`.

### 2. Proxy configuration (corporate networks)

`rustup`, `cargo`, `uv`, and the `curl` calls inside the backend `Justfile`
all read proxy settings from the **environment**. Configuring
`git config http.proxy` or `npm config set proxy` does _not_ cover them —
a common cause of connection timeouts on an otherwise working machine.

```powershell
[Environment]::SetEnvironmentVariable('http_proxy',  'http://<proxy>:911', 'Machine')
[Environment]::SetEnvironmentVariable('https_proxy', 'http://<proxy>:912', 'Machine')
[Environment]::SetEnvironmentVariable('no_proxy',    'localhost,127.0.0.1,::1', 'Machine')
```

Open a **new** shell afterwards, and verify with `$env:https_proxy` in the
same window you run `just` from. Add internal domains to `no_proxy` so they
aren't routed through the proxy.

### 3. Build the backend sidecar

From `application\backend`:

```powershell
just pyinstaller            # CPU
just pyinstaller -a xpu     # Intel GPU
just pyinstaller -a cuda    # NVIDIA GPU
```

On first run the recipe installs `uv` into `%USERPROFILE%\.local\bin`, which
is not added to the running session's `PATH`. If the build then fails with
`uv: command not found`, add it and re-run:

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
```

Output lands in `application\backend\dist\geti-backend\`.

### 4. Stage the sidecar into `src-tauri\`

From `application\ui\src-tauri`. Symlinks avoid copying gigabytes after every
backend rebuild, but need an elevated shell or Developer Mode enabled:

```powershell
New-Item -ItemType SymbolicLink -Path .\geti-backend-x86_64-pc-windows-msvc.exe `
    -Target ..\..\backend\dist\geti-backend\geti-backend.exe
New-Item -ItemType SymbolicLink -Path .\_internal `
    -Target ..\..\backend\dist\geti-backend\_internal
```

If you can't elevate, copy instead — this is what CI does, and it must be
repeated after every `just pyinstaller`:

```powershell
Copy-Item ..\..\backend\dist\geti-backend\geti-backend.exe .\geti-backend-x86_64-pc-windows-msvc.exe
Copy-Item -Recurse -Force ..\..\backend\dist\geti-backend\_internal .\_internal
```

### 5. Run the dev shell

From `application\ui`:

```powershell
npm ci
npm run build:api        # generate API typings from src\api\openapi-spec.json
npm run start:desktop    # tauri dev
```

`start:desktop` runs `tauri dev`, which invokes `npm run start:tauri` (sets
`BUILD_TARGET=tauri` and starts the Rspack dev server) and opens the native
window once the dev server is ready.

Working on the UI only? `npm run start` serves the same app in a browser with
no Rust toolchain and no sidecar required — point it at a backend started with
`just run-server` from `application\backend`.

### 6. Build the MSIX

`bundle.targets` is `["app"]`, so `tauri build` emits a bare executable tree
rather than an installer; the MSIX is packed separately with `makeappx.exe`
from the Windows SDK.

```powershell
cd application\ui
cargo tauri build                       # add --debug for a debug build

$build = "src-tauri\target\release"
$msix  = "$build\bundle\msix"
mkdir -Force $msix
Copy-Item "$build\geti-backend.exe", "$build\geti_ui.exe" $msix
Copy-Item -Recurse -Force "$build\_internal" $msix
Copy-Item -Recurse -Force "src-tauri\msix\*" $msix

& "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\makeappx.exe" `
    pack /d $msix /p "$msix\geti.msix"
```

Release packages are then signed with `signtool.exe`. An unsigned MSIX can
only be installed with Developer Mode enabled.

> The `start:tauri` and `build:tauri` npm scripts set `BUILD_TARGET=tauri`
> using POSIX syntax. npm runs them through the `sh.exe` shipped with Git for
> Windows, so they work from PowerShell. If you invoke Rspack directly, set
> the variable yourself:
>
> ```powershell
> $env:BUILD_TARGET = 'tauri'; npx rsbuild build
> ```

### Troubleshooting

| Symptom                                                    | Cause and fix                                                     |
| ---------------------------------------------------------- | ----------------------------------------------------------------- |
| `error sending request ... (os error 10060)` from `rustup` | Proxy variables not set in the environment. See step 2.           |
| `rustup could not choose a version of cargo to run`        | No default toolchain — run `rustup default stable`.               |
| `link.exe not found`                                       | MSVC build tools missing, or wrong workload selected.             |
| `could not find cygpath executable`                        | `C:\Program Files\Git\usr\bin` not on `PATH`. See step 1.         |
| `uv: command not found` immediately after uv installs      | `%USERPROFILE%\.local\bin` not on `PATH`. See step 3.             |
| `curl: (28) Failed to connect to github.com`               | Proxy variables missing in the shell running `just`.              |
| `resource path geti-backend-...exe doesn't exist`          | Sidecar not built or not staged. See steps 3 and 4.               |
| Blank window on launch                                     | WebView2 runtime not installed.                                   |
| `New-Item ... SymbolicLink` access denied                  | Run elevated, enable Developer Mode, or copy instead. See step 4. |

---

## macOS

Development only — Geti is not distributed as a macOS product.

### 1. System prerequisites

```sh
xcode-select --install
brew install rustup-init just node && rustup-init
```

### 2. Build the backend sidecar

From `application/backend`:

```sh
just pyinstaller            # CPU
just pyinstaller -a xpu     # Intel GPU
just pyinstaller -a cuda    # NVIDIA GPU
```

The recipe first runs `just fix-macho-signatures`, which repairs malformed
Mach-O dylibs shipped by some upstream wheels (notably `openvino`'s
`libhwloc` / `libtbb*`). Without it, ad-hoc codesigning during PyInstaller's
`COLLECT` phase fails with _"internal error in Code Signing subsystem"_. The
script lives at
[`../../backend/pyinstaller/fix_macho_signatures.py`](../../backend/pyinstaller/fix_macho_signatures.py)
and can be run standalone after a manual `uv sync`:

```sh
just fix-macho-signatures
```

### 3. Stage the sidecar into `src-tauri/`

From `application/ui/src-tauri`, using your host triple:

```sh
# Apple silicon (M1/M2/M3/M4)
ln -sf ../../backend/dist/geti-backend/geti-backend geti-backend-aarch64-apple-darwin

# Intel
ln -sf ../../backend/dist/geti-backend/geti-backend geti-backend-x86_64-apple-darwin

ln -sf ../../backend/dist/geti-backend/_internal _internal
```

### 4. Run the dev shell

From `application/ui`:

```sh
npm ci
npm run build:api
npm run start:desktop
```

For UI-only work, `npm run start` serves the same app in a browser with no
Rust toolchain and no sidecar required.

### 5. Build a distributable `.app` / `.dmg`

```sh
just tauri-build   # from application/
```

Use the recipe, not `npx tauri build` directly. It patches the bundle layout
afterwards, moving the sidecar and `_internal/` into `Contents/MacOS/backend/`
so PyInstaller's bootloader doesn't switch into `.app`-bundle mode and look
for `libpython*.dylib` under `Contents/Frameworks/`. A plain `tauri build`
yields a bundle whose backend dies on launch with
`Failed to load Python shared library 'libpython*.dylib'`.

Artifacts land in `application/ui/src-tauri/target/release/bundle/`.

---

## Linux

Development only — Geti is distributed on Linux as a Docker image rather than
a desktop bundle.

### 1. System prerequisites

Debian/Ubuntu package names shown; see the
[Tauri prerequisites page](https://v2.tauri.app/start/prerequisites/) for
Fedora/Arch/openSUSE equivalents.

```sh
sudo apt update
sudo apt install \
    libwebkit2gtk-4.1-dev \
    build-essential \
    curl \
    wget \
    file \
    libxdo-dev \
    libssl-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

Then install [Rust](https://rustup.rs), Node.js ≥ 24.2, and
[`just`](https://just.systems).

### 2. Build and stage the backend sidecar

```sh
cd application/backend && just pyinstaller
cd ../ui/src-tauri
ln -sf ../../backend/dist/geti-backend/geti-backend geti-backend-x86_64-unknown-linux-gnu
ln -sf ../../backend/dist/geti-backend/_internal _internal
```

### 3. Run the dev shell

From `application/ui`:

```sh
npm ci
npm run build:api
npm run start:desktop
```

### 4. Build a distributable AppImage / `.deb`

```sh
just tauri-build   # from application/
```

Artifacts land in `application/ui/src-tauri/target/release/bundle/`.

---

## Reference

### Module resolution architecture

The same TypeScript source tree powers both the browser SPA and the Tauri
desktop build. Per-platform behaviour (downloading files, native menus,
auto-update, OS-specific styles, …) is selected **at build time by the
bundler**, not at runtime.

#### How it works

`rsbuild.config.ts` reads `process.env.BUILD_TARGET`. When it equals `"tauri"`,
the Rspack `resolve.extensions` list is prepended with `.tauri.tsx`,
`.tauri.ts`, `.tauri.jsx`, `.tauri.js`, `.tauri.scss`:

```ts
// application/ui/rsbuild.config.ts
const isTauriBuild = process.env.BUILD_TARGET === 'tauri';
const platformExtensions = isTauriBuild
    ? ['.tauri.tsx', '.tauri.ts', '.tauri.jsx', '.tauri.js', '.tauri.scss']
    : [];

resolve: {
    extensions: [...platformExtensions, '.tsx', '.ts', '.jsx', '.js', '.json'],
}
```

A consumer always imports a plain name:

```ts
import { downloadFile } from './download-file';
```

The bundler resolves that import in extension order:

| Build         | Resolution order                 | File picked                     |
| ------------- | -------------------------------- | ------------------------------- |
| Web (default) | `.tsx`, `.ts`, …                 | `download-file.ts`              |
| Tauri         | `.tauri.tsx`, `.tauri.ts`, `.ts` | `download-file.tauri.ts` (wins) |

The unselected file is **not parsed and never enters the module graph**, so
`@tauri-apps/*` imports cannot leak into the web bundle and the web fallbacks
cannot bloat the desktop bundle.

#### Conventions

```
src/
  platform/
    download-file.ts            ← web (default)
    download-file.tauri.ts      ← tauri override
```

Twins can live anywhere under `src/`; `src/platform/` is just where existing
capability modules are grouped.

Rules of thumb when adding a platform-specific behaviour:

1. **Plain file is the default.** It runs in both web and Tauri _unless_
   shadowed by a `.tauri.*` twin sitting next to it.
2. **`.tauri.*` files may import `@tauri-apps/*`.** Other source files may
   not — this is enforced by the `no-restricted-imports` rule in
   [`../eslint.config.js`](../eslint.config.js).
3. **Tauri-only features:** ship a no-op/null-returning module as the default
   and the real implementation in `.tauri.{ts,tsx}`. Consumers render/call
   unconditionally; the web build tree-shakes the no-op away.
4. **Tauri-only styles:** same trick with `.scss` / `.tauri.scss`. The
   `.tauri.scss` and `.scss` extensions are already in `resolve.extensions`,
   so an extensionless import (`import './foo'`) resolves to `foo.tauri.scss`
   on the desktop build and `foo.scss` on the web build. Drop the extension
   on the import site to opt in to the override.
5. **No `isTauri()` runtime checks anywhere.** Enforced by the
   `no-restricted-syntax` rule in [`../eslint.config.js`](../eslint.config.js).
   If you find yourself reaching for one, add (or split) a capability module
   instead.

The Tauri shell wires `BUILD_TARGET=tauri` for both the dev server and the
production build via `beforeDevCommand` / `beforeBuildCommand` in
[`tauri.conf.json`](./tauri.conf.json), which invoke the `start:tauri` and
`build:tauri` scripts in [`../package.json`](../package.json).

### Verifying the platform split

Quick checks after changing anything under `src/platform/`:

```sh
# Web build should not contain any @tauri-apps references.
npm run build
grep -R "@tauri-apps" dist/ && echo "LEAK" || echo "clean"

# Tauri build must contain them.
npm run build:tauri
grep -R "tauri" dist/ >/dev/null && echo "ok" || echo "missing"
```

### Where is my data?

The desktop shell pins the backend's `DATA_DIR`, `LOG_DIR` and matplotlib
cache to OS-conventional per-user directories (resolved via Tauri's
`app.path()` APIs from the `com.intel.geti` bundle identifier). These live
**outside** the install prefix, so reinstalls and upgrades preserve them
— same convention as Chrome and VSCode.

| Platform | Data                                           | Logs                            | Cache (matplotlib)                           |
| -------- | ---------------------------------------------- | ------------------------------- | -------------------------------------------- |
| macOS    | `~/Library/Application Support/com.intel.geti` | `~/Library/Logs/com.intel.geti` | `~/Library/Caches/com.intel.geti/matplotlib` |
| Windows  | `%APPDATA%\com.intel.geti`                     | `%APPDATA%\com.intel.geti\logs` | `%LOCALAPPDATA%\com.intel.geti\matplotlib`   |
| Linux    | `~/.local/share/com.intel.geti`                | `~/.local/state/com.intel.geti` | `~/.cache/com.intel.geti/matplotlib`         |

Set `DATA_DIR`, `LOG_DIR`, or `MPLCONFIGDIR` in the environment to override
any of them (the Rust shell only fills in what's missing).

### Cleanup / uninstall

The OS uninstaller / drag-to-trash only removes the app itself. To wipe
**everything**, delete the per-user directories listed above plus the local
build outputs.

Windows:

```powershell
Remove-Item -Recurse -Force "$env:APPDATA\com.intel.geti", "$env:LOCALAPPDATA\com.intel.geti"
Remove-Item -Recurse -Force application\backend\dist, application\backend\build
Remove-Item -Recurse -Force application\ui\src-tauri\target, application\ui\dist
```

macOS:

```sh
rm -rf ~/Library/{Application\ Support,Logs,Caches}/com.intel.geti
rm -rf application/backend/dist application/backend/build
rm -rf application/ui/src-tauri/target application/ui/dist
```

Linux:

```sh
rm -rf ~/.local/share/com.intel.geti ~/.local/state/com.intel.geti ~/.cache/com.intel.geti
rm -rf application/backend/dist application/backend/build
rm -rf application/ui/src-tauri/target application/ui/dist
```
