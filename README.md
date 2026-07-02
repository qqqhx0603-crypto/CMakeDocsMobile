# CMakeDocsMobile

## 简介

CMakeDocsMobile 是一个轻量 Android 离线文档阅读器，内置 CMake 4.3.4 中文版和英文版文档。应用支持中英文同路径切换、目录浏览、搜索、收藏、阅读历史、前进/后退、页面位置恢复、文字缩放、顶部/底部跳转和阅读进度条，适合在手机上快速查阅 CMake 手册。

项目使用原生 Java Activity + WebView 实现，不依赖 Gradle、AndroidX 或第三方 Android 框架。仓库内包含构建 APK 所需的源码、资源、工具脚本和离线文档资产。

## 用法

准备环境：

- Windows PowerShell 5 或更高版本。
- JDK，需能在命令行运行 `java`、`javac` 和 `keytool`。
- Android SDK，至少包含 `platforms/android-35` 和 `build-tools`。
- Python 3，用于打包 APK 内置资产。

设置 Android SDK 路径。如果没有设置，脚本会尝试使用本机默认路径 `D:\env\android-sdk`。

```powershell
$env:ANDROID_HOME = "D:\env\android-sdk"
```

构建 APK：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-apk.ps1
```

构建完成后，APK 会输出到：

```text
dist\cmake-docs-mobile.apk
```

脚本会自动生成本地 `debug.keystore` 用于签名，该文件不会提交到仓库。

## 其他

- `src/`：Android Java 源码。
- `res/`：Android 资源。
- `assets/docs/zh/`：中文 CMake 文档。
- `assets/docs/en/`：英文 CMake 文档。
- `assets/docs_index.json`：应用内目录、搜索和语言切换索引。
- `tools/`：APK 资产打包与路径规范化脚本。

应用源码按 MIT License 开源。仓库内置的 CMake 文档、图标、HTML、CSS、JavaScript 和其他上游文档资产保留其原始版权和许可声明。
