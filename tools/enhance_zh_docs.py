from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "assets" / "docs"
ZH_ROOT = DOCS_ROOT / "zh"
EN_ROOT = DOCS_ROOT / "en"
INDEX_PATH = ROOT / "assets" / "docs_index.json"
REPORT_PATH = ROOT / "docs_enhance_report.json"

NOTE_BEGIN = "<!-- CMAKE_ZH_CODE_NOTES_BEGIN -->"
NOTE_END = "<!-- CMAKE_ZH_CODE_NOTES_END -->"
SYMBOL_NOTE_BEGIN = "<!-- CMAKE_ZH_SYMBOL_NOTE_BEGIN -->"
SYMBOL_NOTE_END = "<!-- CMAKE_ZH_SYMBOL_NOTE_END -->"

PROTECTED_RE = re.compile(
    r"(<script\b.*?</script>|<style\b.*?</style>|<pre\b[^>]*>.*?</pre>|<code\b[^>]*>.*?</code>|<!--.*?-->|<[^>]+>)",
    re.IGNORECASE | re.DOTALL,
)
GENERATED_NOTE_RE = re.compile(
    rf"\s*{re.escape(NOTE_BEGIN)}.*?{re.escape(NOTE_END)}\s*",
    re.DOTALL,
)
GENERATED_SYMBOL_NOTE_RE = re.compile(
    rf"\s*{re.escape(SYMBOL_NOTE_BEGIN)}.*?{re.escape(SYMBOL_NOTE_END)}\s*",
    re.DOTALL,
)
CODE_BLOCK_RE = re.compile(
    r'(<div class="highlight-([A-Za-z0-9_+\-]+)[^"]*"><div class="highlight"><pre>.*?</pre></div>\s*</div>|<pre class="literal-block"[^>]*>.*?</pre>)',
    re.DOTALL,
)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
BODY_RE = re.compile(r'<div class="body" role="main">(.*?)</div>\s*</div>\s*</div>', re.IGNORECASE | re.DOTALL)
CONTENTS_NAV_RE = re.compile(r"<nav class=\"contents\".*?</nav>", re.IGNORECASE | re.DOTALL)
PARAGRAPH_RE = re.compile(r"<p(?P<attrs>[^>]*)>(?P<body>.*?)</p>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


EXACT_REPLACEMENTS = [
    ("value=\"search\"", "value=\"搜索\""),
    ("title=\"Link to this definition\"", "title=\"跳转到此定义\""),
    ("title=\"Link to this code\"", "title=\"跳转到此代码\""),
    ("title=\"Link to this heading\"", "title=\"跳转到此标题\""),
    ("title=\"Link to this image\"", "title=\"跳转到此图片\""),
    ("title=\"Link to this table\"", "title=\"跳转到此表格\""),
    ("title=\"Link to this equation\"", "title=\"跳转到此公式\""),
    ("Or, select a version from the drop-down menu above.", "或者从上方下拉菜单中选择其他版本。"),
    ("latest release", "最新版本"),
    ("target property", "target property（目标属性）"),
    ("source file property", "source file property（源文件属性）"),
    ("global property", "global property（全局属性）"),
    ("directory property", "directory property（目录属性）"),
    ("test property", "test property（测试属性）"),
    ("installed file property", "installed file property（已安装文件属性）"),
    ("cache property", "cache property（缓存属性）"),
    ("普通库 (Normal Libraries)", "普通库（Normal Libraries）"),
    ("对象库 (Object Libraries)", "对象库（Object Libraries）"),
    ("接口库 (Interface Libraries)", "接口库（Interface Libraries）"),
    ("导入库 (Imported Libraries)", "导入库（Imported Libraries）"),
    ("别名库 (Alias Libraries)", "别名库（Alias Libraries）"),
    ("文件集 (File Sets)", "文件集（File Sets）"),
    ("generator expressions", "generator expressions（生成器表达式）"),
    ("GNU Make", "GNU Make（GNU 构建工具）"),
    ("shell", "shell（命令解释器）"),
    ("depfile", "depfile（依赖描述文件）"),
    ("byproduct", "byproduct（副产品文件）"),
    ("byproducts", "byproducts（副产品文件）"),
    ("job server", "job server（作业服务器）"),
    ("order-only dependencies", "order-only dependencies（仅顺序依赖）"),
    ("recipe line", "recipe line（配方行）"),
    ("ALIAS target", "ALIAS target（别名目标）"),
    ("File Sets", "File Sets（文件集）"),
    ("Makefile（构建脚本）s", "Makefiles（Make 构建脚本）"),
    ("Makefile（构建脚本）", "Makefile（Make 构建脚本）"),
    ("macOS", "macOS（苹果桌面系统）"),
    ("Windows", "Windows（微软桌面系统）"),
    ("DLL", "DLL（动态链接库）"),
    ("dlopen", "dlopen（动态装载接口）"),
    ("OpenGL", "OpenGL（开放图形库）"),
    ("Lua scripting language", "Lua scripting language（Lua 脚本语言）"),
    ("XML library", "XML library（XML 库）"),
    ("HTML-import", "HTML-import（HTML 导入）"),
    ("odt-export", "odt-export（ODT 导出）"),
    ("screenshots", "screenshots（屏幕截图）"),
    ("目标（targets（目标））", "目标（targets）"),
    ("文件集（File Sets（文件集））", "文件集（File Sets）"),
    ("Dashboard Client（仪表板客户端）（仪表板客户端）", "Dashboard Client（仪表板客户端）"),
    ("别名目标 (ALIAS target（别名目标）)", "别名目标（ALIAS target）"),
    ("副产品（byproduct（副产品文件））", "副产品（byproduct）"),
    ("作业服务器（job server（作业服务器））", "作业服务器（job server）"),
    ("配方行（recipe line（配方行））", "配方行（recipe line）"),
    ("依赖文件 (depfile（依赖描述文件）)", "依赖文件（depfile）"),
    ("仅用于顺序的依赖（order-only dependencies（仅顺序依赖））", "仅用于顺序的依赖（order-only dependencies）"),
    ("Dashboard Client", "Dashboard Client（仪表板客户端）"),
    ("Extra Generators", "Extra Generators（扩展生成器）"),
    ("cpack generator", "cpack generator（CPack 生成器）"),
    ("CPack AppImage Generator", "CPack AppImage Generator（AppImage 打包生成器）"),
    ("CPack Archive Generator", "CPack Archive Generator（归档包生成器）"),
    ("CPack Bundle Generator", "CPack Bundle Generator（Bundle 打包生成器）"),
    ("CPack Cygwin Generator", "CPack Cygwin Generator（Cygwin 打包生成器）"),
    ("CPack DEB Generator", "CPack DEB Generator（DEB 打包生成器）"),
    ("CPack DragNDrop Generator", "CPack DragNDrop Generator（DragNDrop 打包生成器）"),
    ("CPack External Generator", "CPack External Generator（外部打包生成器）"),
    ("CPack FreeBSD Generator", "CPack FreeBSD Generator（FreeBSD 打包生成器）"),
    ("CPack IFW Generator", "CPack IFW Generator（IFW 打包生成器）"),
    ("CPack Inno Setup Generator", "CPack Inno Setup Generator（Inno Setup 打包生成器）"),
    ("CPack NSIS Generator", "CPack NSIS Generator（NSIS 打包生成器）"),
    ("CPack NuGet Generator", "CPack NuGet Generator（NuGet 打包生成器）"),
    ("CPack PackageMaker Generator", "CPack PackageMaker Generator（PackageMaker 打包生成器）"),
    ("CPack productbuild Generator", "CPack productbuild Generator（productbuild 打包生成器）"),
    ("CPack RPM Generator", "CPack RPM Generator（RPM 打包生成器）"),
    ("CPack WIX Generator", "CPack WIX Generator（WIX 打包生成器）"),
    ("IDE Integration Guide", "IDE 集成指南"),
    ("Importing and Exporting Guide", "导入和导出指南"),
    ("User Interaction Guide", "用户交互指南"),
    ("Using Dependencies Guide", "使用依赖项指南"),
    ("Step 0: Before You Begin", "第 0 步：开始之前"),
    ("Step 1: A Basic Starting Point", "第 1 步：一个基本的起点"),
    ("Step 1: Getting Started with CMake", "第 1 步：CMake 入门"),
    ("Step 2: Adding a Library", "第 2 步：添加一个库"),
    ("Step 2: CMake Language Fundamentals", "第 2 步：CMake 语言基础"),
    ("Step 3: Adding Usage Requirements for a Library", "第 3 步：为库添加使用要求"),
    ("Step 3: Configuration and Cache Variables", "第 3 步：配置与缓存变量"),
    ("Step 4: Adding Generator Expressions", "第 4 步：添加生成器表达式"),
    ("Step 4: In-Depth CMake Target Commands", "第 4 步：深入了解 CMake 目标命令"),
    ("Step 5: In-Depth CMake Library Concepts", "第 5 步：深入了解 CMake 库概念"),
    ("Step 5: Installing and Testing", "第 5 步：安装和测试"),
    ("Step 6: Adding Support for a Testing Dashboard", "第 6 步：添加测试仪表板支持"),
    ("Step 6: In-Depth System Introspection", "第 6 步：深入系统内省"),
    ("Step 7: Adding System Introspection", "第 7 步：添加系统内省"),
    ("Step 7: Custom Commands and Generated Files", "第 7 步：自定义命令与生成文件"),
    ("Step 8: Adding a Custom Command and Generated File", "第 8 步：添加自定义命令和生成的文件"),
    ("Step 8: Testing and CTest", "第 8 步：测试与 CTest"),
    ("Step 9: Installation Commands and Concepts", "第 9 步：安装命令与概念"),
    ("Step 9: Packaging an Installer", "第 9 步：打包安装程序"),
    ("Step 10: Finding Dependencies", "第 10 步：查找依赖项"),
    ("Step 10: Selecting Static or Shared Libraries", "第 10 步：选择静态库或共享库"),
    ("Step 11: Adding Export Configuration", "第 11 步：添加导出配置"),
    ("Step 11: Miscellaneous Features", "第 11 步：杂项功能"),
    ("Step 12: Packaging Debug and Release", "第 12 步：打包调试版和发布版"),
    ("Dynamic Language Runtime", "Dynamic Language Runtime（动态语言运行时）"),
    ("Python Enhancement Proposals", "Python Enhancement Proposals（Python 增强提案）"),
    ("Qt Installer Framework", "Qt Installer Framework（Qt 安装程序框架）"),
    ("Google Trace Event Format", "Google Trace Event Format（Google 跟踪事件格式）"),
    ("Green Hills Software", "Green Hills Software（Green Hills 软件公司）"),
    ("The Portland Group", "The Portland Group（Portland 编译器供应商）"),
    ("Oracle Developer Studio", "Oracle Developer Studio（Oracle 开发套件）"),
    ("Windows Embedded Compact", "Windows Embedded Compact（Windows 嵌入式精简版）"),
    ("NVIDIA Nsight Tegra Visual Studio Edition", "NVIDIA Nsight Tegra Visual Studio Edition（NVIDIA Tegra 的 Visual Studio 扩展）"),
    ("NVIDIA Nsight Tegra", "NVIDIA Nsight Tegra（NVIDIA Tegra 调试扩展）"),
    ("NVIDIA GPUDirect Storage cuFile", "NVIDIA GPUDirect Storage cuFile（NVIDIA 直通存储接口）"),
    ("NVIDIA Open Computing Language", "NVIDIA Open Computing Language（NVIDIA 开放计算语言）"),
    ("Testing with Xcode", "使用 Xcode 进行测试"),
    ("Link Binaries With Libraries", "链接二进制文件与库"),
    ("Message-Digest Algorithm 5, RFC 1321。", "Message-Digest Algorithm 5（消息摘要算法 5），RFC 1321。"),
    ("US Secure Hash Algorithm 1, RFC 3174。", "US Secure Hash Algorithm 1（美国安全散列算法 1），RFC 3174。"),
    ("US Secure Hash Algorithms, RFC 4634。", "US Secure Hash Algorithms（美国安全散列算法族），RFC 4634。"),
    ("Keccak SHA-3。", "Keccak SHA-3（SHA-3 散列算法）。"),
]

REGEX_REPLACEMENTS = [
    (
        re.compile(r"Ninja(?:（构建工具）)? Multi-Config(?:（Ninja(?:（构建工具）)? 多配置生成器）)*"),
        "Ninja Multi-Config（Ninja 多配置生成器）",
    ),
    (
        re.compile(r"(?<![A-Za-z0-9_])Ninja(?:（构建工具）)+(?![A-Za-z0-9_])"),
        "Ninja（构建工具）",
    ),
    (
        re.compile(r"(?<![A-Za-z0-9_])Ninja(?![A-Za-z0-9_（]| Multi-Config)"),
        "Ninja（构建工具）",
    ),
    (
        re.compile(r"primary module interface unit(?:（主模块接口单元）|（模块接口单元）)+"),
        "primary module interface unit（主模块接口单元）",
    ),
    (
        re.compile(r"primary module interface unit(?!（)"),
        "primary module interface unit（主模块接口单元）",
    ),
    (
        re.compile(r"(?<!primary )module interface unit(?:（模块接口单元）)+"),
        "module interface unit（模块接口单元）",
    ),
    (
        re.compile(r"(?<!primary )module interface unit(?!（)"),
        "module interface unit（模块接口单元）",
    ),
    (
        re.compile(r"internal partition unit(?:（内部分区单元）)+"),
        "internal partition unit（内部分区单元）",
    ),
    (
        re.compile(r"internal partition unit(?!（)"),
        "internal partition unit（内部分区单元）",
    ),
    (
        re.compile(r"strong module ownership(?:（强模块归属）)+"),
        "strong module ownership（强模块归属）",
    ),
    (
        re.compile(r"strong module ownership(?!（)"),
        "strong module ownership（强模块归属）",
    ),
    (
        re.compile(r"Microsoft Visual Studio(?:（微软 Visual Studio(?:（集成开发环境）)?）|（集成开发环境）)+"),
        "Microsoft Visual Studio（微软集成开发环境）",
    ),
    (
        re.compile(r"(?<!Microsoft )Visual Studio(?:（集成开发环境）)+\s+Generators(?:（Visual Studio 生成器）)?"),
        "Visual Studio Generators（Visual Studio 生成器）",
    ),
    (
        re.compile(r"Visual Studio Generators(?!（)"),
        "Visual Studio Generators（Visual Studio 生成器）",
    ),
    (
        re.compile(r"Microsoft Visual Studio(?!（)"),
        "Microsoft Visual Studio（微软集成开发环境）",
    ),
    (
        re.compile(r"(?<!Microsoft )Visual Studio(?:（集成开发环境）)+"),
        "Visual Studio（集成开发环境）",
    ),
    (
        re.compile(r"(?<!Microsoft )Visual Studio(?!（| Generators)"),
        "Visual Studio（集成开发环境）",
    ),
    (re.compile(r"Added in version ([0-9.]+)\."), r"\1 版本新增。"),
    (re.compile(r"Changed in version ([0-9.]+)\."), r"\1 版本更改。"),
    (re.compile(r"Deprecated since version ([0-9.]+)\."), r"自 \1 版本起已弃用。"),
    (re.compile(r"New in version ([0-9.]+)\."), r"\1 版本新增。"),
    (re.compile(r"(?<![A-Za-z0-9_])Makefiles(?![A-Za-z0-9_（])"), "Makefiles（Make 构建脚本）"),
    (re.compile(r"(?<![A-Za-z0-9_])Makefile(?![A-Za-z0-9_（])"), "Makefile（Make 构建脚本）"),
]

CMK_CMD_TEXT = {
    "add_compile_definitions": "为当前目录或目标补充预处理宏定义。",
    "add_compile_options": "为当前目录或目标追加编译选项。",
    "add_custom_command": "定义自定义构建命令及其输入输出关系。",
    "add_custom_target": "定义一个没有直接输出文件的自定义目标。",
    "add_dependencies": "声明目标之间的构建依赖关系。",
    "add_executable": "定义一个可执行目标。",
    "add_library": "定义一个库目标。",
    "add_subdirectory": "把子目录中的 CMakeLists.txt 纳入当前构建。",
    "add_test": "登记一个测试用例。",
    "cmake_minimum_required": "声明工程所需的最低 CMake 版本。",
    "enable_testing": "开启测试支持。",
    "execute_process": "在配置阶段执行外部进程。",
    "file": "执行文件系统相关操作。",
    "find_file": "查找文件路径。",
    "find_library": "查找库文件。",
    "find_package": "查找并加载外部依赖包。",
    "find_path": "查找头文件或目录路径。",
    "find_program": "查找可执行程序。",
    "foreach": "开始遍历列表或范围。",
    "function": "定义一个具有独立作用域的函数。",
    "if": "开始条件判断分支。",
    "include": "加载并执行另一个 CMake 脚本。",
    "install": "声明安装规则。",
    "list": "对列表变量执行追加、删除、查询等操作。",
    "macro": "定义一个与调用方共享作用域的宏。",
    "message": "输出提示、状态或调试信息。",
    "option": "声明一个布尔型配置选项。",
    "project": "定义项目名称及语言等元数据。",
    "return": "从当前函数、宏或脚本提前返回。",
    "set": "设置变量、缓存项或环境变量。",
    "set_property": "设置目标、目录、源文件等对象的属性。",
    "set_target_properties": "批量设置目标属性。",
    "set_source_files_properties": "批量设置源文件属性。",
    "string": "执行字符串处理。",
    "target_compile_definitions": "为目标设置编译宏。",
    "target_compile_features": "为目标声明所需语言特性。",
    "target_compile_options": "为目标设置编译选项。",
    "target_include_directories": "为目标配置头文件搜索目录。",
    "target_link_directories": "为目标配置链接目录。",
    "target_link_libraries": "为目标链接依赖库。",
    "target_link_options": "为目标设置链接器选项。",
    "target_precompile_headers": "为目标配置预编译头。",
    "target_sources": "为目标补充源文件列表。",
    "while": "开始 while 循环。",
}

SHELL_CMD_TEXT = {
    "cmake": "调用 CMake 命令。",
    "ctest": "运行或管理测试。",
    "cpack": "执行打包流程。",
    "ninja": "调用 Ninja 构建工具。",
    "make": "调用 Make 构建工具。",
    "git": "执行 Git 版本控制操作。",
    "cd": "切换当前工作目录。",
    "mkdir": "创建目录。",
    "python": "运行 Python 脚本。",
    "bash": "运行 Bash 命令或脚本。",
    "sh": "运行 shell 命令或脚本。",
}

REFERENCE_MANUAL_DESCRIPTIONS = {
    "cmake.1.html": "CMake 命令行工具：配置、生成、构建和安装项目。",
    "ctest.1.html": "CTest 命令行工具：运行测试并提交测试结果。",
    "cpack.1.html": "CPack 命令行工具：生成安装包和归档包。",
    "cmake-gui.1.html": "CMake 图形界面：交互设置缓存变量并生成构建系统。",
    "ccmake.1.html": "CMake 终端界面：在字符界面中交互配置项目。",
    "cmake-buildsystem.7.html": "CMake 构建系统：目标、属性、传递用法要求及构建规范。",
    "cmake-commands.7.html": "CMake 命令索引：脚本中可调用的全部内置命令。",
    "cmake-compile-features.7.html": "编译特性：声明项目所需的 C、C++ 编译器特性。",
    "cmake-configure-log.7.html": "配置日志：记录配置阶段的系统检查事件。",
    "cmake-cxxmodules.7.html": "C++ 模块：CMake 对 C++20 模块的扫描与构建支持。",
    "cmake-developer.7.html": "开发者手册：编写和维护 CMake 模块及上游代码的规则。",
    "cmake-env-variables.7.html": "环境变量索引：影响 CMake、CTest 和 CPack 行为的环境变量。",
    "cmake-file-api.7.html": "文件 API：供 IDE 和工具读取构建系统语义信息。",
    "cmake-generator-expressions.7.html": "生成器表达式：在生成和构建阶段按上下文计算值。",
    "cmake-generators.7.html": "生成器索引：选择 Ninja、Makefile 或 IDE 构建系统。",
    "cmake-instrumentation.7.html": "插桩接口：采集 CMake 命令执行和构建过程数据。",
    "cmake-language.7.html": "CMake 语言：语法、变量、列表、控制结构和作用域。",
    "cmake-modules.7.html": "CMake 模块索引：查找依赖和提供辅助功能的模块。",
    "cmake-packages.7.html": "软件包：查找、导出和使用 CMake 包配置。",
    "cmake-policies.7.html": "策略索引：管理不同 CMake 版本之间的行为兼容性。",
    "cmake-presets.7.html": "预设：用 JSON 文件保存配置、构建、测试和打包参数。",
    "cmake-properties.7.html": "属性索引：全局、目录、目标、源文件和测试属性。",
    "cmake-qt.7.html": "Qt 支持：自动处理 Qt 工具、资源、界面和元对象代码。",
    "cmake-server.7.html": "旧服务器模式：已移除接口及其迁移说明。",
    "cmake-toolchains.7.html": "工具链：编译器、链接器、交叉编译和平台配置。",
    "cmake-variables.7.html": "变量索引：CMake 提供或识别的全部变量。",
    "cpack-generators.7.html": "CPack 生成器索引：各类安装包和归档格式。",
}

COMMON_VARIABLE_DESCRIPTIONS = {
    "CMAKE_SOURCE_DIR": "顶层源代码目录的绝对路径。",
    "CMAKE_BINARY_DIR": "顶层构建目录的绝对路径。",
    "CMAKE_CURRENT_SOURCE_DIR": "当前正在处理的源代码目录。",
    "CMAKE_CURRENT_BINARY_DIR": "当前源目录所对应的构建目录。",
    "PROJECT_SOURCE_DIR": "最近一次 project() 调用所定义项目的源代码根目录。",
    "PROJECT_BINARY_DIR": "最近一次 project() 调用所定义项目的构建根目录。",
    "PROJECT_NAME": "最近一次 project() 调用设置的项目名称。",
    "CMAKE_PROJECT_NAME": "最顶层 project() 调用设置的项目名称。",
    "CMAKE_BUILD_TYPE": "单配置生成器使用的构建配置，例如 Debug 或 Release。",
    "CMAKE_INSTALL_PREFIX": "install() 默认使用的安装根目录。",
    "CMAKE_MODULE_PATH": "项目额外提供的 CMake 模块搜索目录列表。",
    "CMAKE_PREFIX_PATH": "find_package() 等查找命令使用的安装前缀列表。",
    "CMAKE_GENERATOR": "当前使用的构建系统生成器名称。",
    "CMAKE_TOOLCHAIN_FILE": "配置编译器、平台和交叉编译环境的工具链文件。",
    "CMAKE_C_COMPILER": "当前 C 语言编译器的完整路径。",
    "CMAKE_CXX_COMPILER": "当前 C++ 语言编译器的完整路径。",
    "BUILD_SHARED_LIBS": "未显式指定库类型时，控制 add_library() 默认生成共享库还是静态库。",
    "CMAKE_CURRENT_LIST_DIR": "当前正在执行的 CMake 列表文件所在目录。",
    "CMAKE_CURRENT_LIST_FILE": "当前正在执行的 CMake 列表文件完整路径。",
    "CMAKE_CURRENT_LIST_LINE": "当前正在执行的 CMake 列表文件行号。",
    "CMAKE_VERSION": "当前运行的 CMake 版本号。",
}

VARIABLE_TOKEN_TEXT = {
    "CURRENT": "当前", "SOURCE": "源代码", "BINARY": "构建", "DIR": "目录",
    "DIRECTORY": "目录", "PROJECT": "项目", "NAME": "名称", "VERSION": "版本",
    "BUILD": "构建", "TYPE": "类型", "INSTALL": "安装", "PREFIX": "前缀",
    "COMPILER": "编译器", "LINKER": "链接器", "FLAGS": "选项", "OPTIONS": "选项",
    "LIBRARY": "库", "EXECUTABLE": "可执行文件", "TARGET": "目标", "SYSTEM": "系统",
    "HOST": "宿主机", "PATH": "路径", "FILE": "文件", "OUTPUT": "输出",
    "INPUT": "输入", "CONFIG": "配置", "DEBUG": "调试配置", "RELEASE": "发布配置",
    "LINK": "链接", "INCLUDE": "包含目录", "MODULE": "模块", "TOOLCHAIN": "工具链",
    "GENERATOR": "生成器", "PROGRAM": "程序", "COMMAND": "命令", "TEST": "测试",
}

CMAKE_OPERATOR_DESCRIPTIONS = {
    "NOT": "逻辑非：反转后续条件的真假值", "AND": "逻辑与：两侧条件都为真时结果为真",
    "OR": "逻辑或：任一侧条件为真时结果为真", "COMMAND": "判断给定名称是否为可调用命令",
    "POLICY": "判断给定策略编号是否存在", "TARGET": "判断给定构建目标是否已定义",
    "TEST": "判断给定测试是否已定义", "DEFINED": "判断变量、缓存项或环境变量是否已定义",
    "EXISTS": "判断文件或目录是否存在", "IS_DIRECTORY": "判断路径是否为目录",
    "IS_READABLE": "判断文件或目录是否可读", "IS_WRITABLE": "判断文件或目录是否可写",
    "IS_EXECUTABLE": "判断文件或目录是否可执行", "IS_NEWER_THAN": "比较两个文件的修改时间",
    "IS_SYMLINK": "判断路径是否为符号链接", "IS_ABSOLUTE": "判断路径是否为绝对路径",
    "MATCHES": "用正则表达式匹配字符串", "LESS": "按数值比较左侧是否小于右侧",
    "GREATER": "按数值比较左侧是否大于右侧", "EQUAL": "按数值比较两侧是否相等",
    "LESS_EQUAL": "按数值比较左侧是否小于或等于右侧",
    "GREATER_EQUAL": "按数值比较左侧是否大于或等于右侧",
    "STRLESS": "按字典顺序比较左侧字符串是否更小", "STRGREATER": "按字典顺序比较左侧字符串是否更大",
    "STREQUAL": "比较两侧字符串是否完全相等", "STRLESS_EQUAL": "按字典顺序比较左侧字符串是否小于或等于右侧",
    "STRGREATER_EQUAL": "按字典顺序比较左侧字符串是否大于或等于右侧",
    "VERSION_LESS": "比较左侧版本号是否更低", "VERSION_GREATER": "比较左侧版本号是否更高",
    "VERSION_EQUAL": "比较两个版本号是否相等", "VERSION_LESS_EQUAL": "比较左侧版本号是否更低或相等",
    "VERSION_GREATER_EQUAL": "比较左侧版本号是否更高或相等", "IN_LIST": "判断左侧值是否包含在右侧列表变量中",
    "PATH_EQUAL": "按路径语义比较两侧路径是否相等",
}

SYMBOL_OPERATOR_DESCRIPTIONS = {
    "==": "相等比较", "!=": "不相等比较", "<=": "小于或等于比较", ">=": "大于或等于比较",
    "<": "小于比较", ">": "大于比较",
    "&&": "逻辑与", "||": "逻辑或", "<<": "按位左移", ">>": "按位右移",
    "+": "加法", "-": "减法", "*": "乘法", "/": "除法", "%": "取余",
    "|": "按位或", "&": "按位与", "^": "按位异或", "~": "按位取反",
    "=": "赋值或键值关联",
}

CODE_TEXT_EXPLANATIONS = {
    "Generate a Project Buildsystem": "以下命令用于配置项目并生成原生构建系统。",
    "Build a Project": "以下命令用于构建已经生成的项目。",
    "Install a Project": "以下命令用于执行项目的安装规则。",
    "Open a Project": "以下命令用于用关联的开发工具打开项目。",
    "Run a Script": "以下命令用于以脚本模式执行 CMake 文件。",
    "Run a Command-Line Tool": "以下命令用于调用 CMake 内置的命令行工具。",
    "Run the Find-Package Tool": "以下命令用于从命令行执行依赖包查找。",
    "Run a Workflow Preset": "以下命令用于执行工作流预设。",
    "View Help": "以下命令用于查看帮助主题。",
    "Run Tests": "以下命令用于运行测试。",
    "Build and Test Mode": "以下内容说明先构建再测试的工作模式。",
}

COMMENT_EXPLANATIONS = {
    "...": "此处省略了与当前要点无关的代码。",
    "Ok, relocatable:": "下面给出可重定位的正确写法。",
    "Wrong, not relocatable:": "下面给出不可重定位的错误写法。",
    "feature not yet supported for the other environments": "其他环境目前尚不支持此功能。",
    "Outputs:": "下面列出命令产生的输出。",
    "The constructed linker command line will contain:": "最终生成的链接器命令行将包含以下内容。",
    "or": "下面给出另一种可选写法。",
    "OR": "下面给出另一种可选写法。",
    "specify the C++ standard": "指定项目采用的 C++ 语言标准。",
    "calculate square root": "计算输入值的平方根。",
    "comparison is TRUE": "下面的比较结果为真。",
    "comparison is FALSE": "下面的比较结果为假。",
    "other fields omitted": "其他与当前说明无关的字段已省略。",
    "Check for macro SEEK_SET": "检查 SEEK_SET 宏是否可用。",
    "Save and reset the current state": "保存当前状态，然后将其重置。",
    "Restore the original state": "恢复先前保存的原始状态。",
    "Example paths:": "下面列出示例路径。",
    "GNU C compiler-specific logic.": "下面是仅适用于 GNU C 编译器的逻辑。",
    "GNU C++ compiler-specific logic.": "下面是仅适用于 GNU C++ 编译器的逻辑。",
    "GNU Fortran compiler-specific logic.": "下面是仅适用于 GNU Fortran 编译器的逻辑。",
    "Save original setting so we can restore it later": "保存原始设置，以便稍后恢复。",
    "make cache variables for install destinations": "为各个安装目标目录创建缓存变量。",
    "generate the version file for the config file": "为包配置文件生成对应的版本文件。",
    "warning level 4": "启用警告级别 4。",
    "additional warnings": "启用额外的编译警告。",
    "Get the first string only": "只取列表中的第一个字符串。",
    "Example:": "下面给出示例。",
}

CLI_OPTION_DESCRIPTIONS = {
    "-S": "指定源代码目录", "-B": "指定构建目录", "-D": "定义或覆盖一个 CMake 缓存变量",
    "-G": "选择构建系统生成器", "-A": "选择生成器平台或目标架构", "-T": "选择生成器工具集",
    "-P": "以脚本模式执行指定的 .cmake 文件", "--build": "驱动已经生成的构建目录执行构建",
    "--install": "执行构建目录中生成的安装规则", "--preset": "使用 CMakePresets.json 中定义的预设",
    "--target": "指定要构建的目标", "--config": "为多配置生成器选择构建配置",
}


def clean_text(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = WS_RE.sub(" ", text).strip()
    text = text.replace("¶", "").strip()
    return text


def protect_sections(text: str) -> tuple[str, list[str]]:
    protected: list[str] = []

    def replace(match: re.Match[str]) -> str:
        token = f"__CMAKE_PROTECTED_{len(protected)}__"
        protected.append(match.group(0))
        return token

    return PROTECTED_RE.sub(replace, text), protected


def restore_sections(text: str, protected: list[str]) -> str:
    return re.sub(
        r"__CMAKE_PROTECTED_([0-9]+)__",
        lambda match: protected[int(match.group(1))],
        text,
    )


def apply_text_replacements(text: str) -> str:
    text, protected = protect_sections(text)
    for source, target in EXACT_REPLACEMENTS:
        text = text.replace(source, target)
    for pattern, replacement in REGEX_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    for _ in range(4):
        collapsed = re.sub(r"（([^）]+)）（\1）", r"（\1）", text)
        if collapsed == text:
            break
        text = collapsed
    text = re.sub(r"(?<=[A-Za-z0-9_])Windows（微软桌面系统）", "Windows", text)
    text = re.sub(r"(?<=[A-Za-z0-9_])DLL（动态链接库）(?=[A-Za-z0-9_])", "DLL", text)
    text = re.sub(r"\b([A-Za-z_][A-Za-z0-9_]*targets)（目标）", r"\1", text)
    text = re.sub(
        r"Visual Studio（集成开发环境） ([0-9]+(?:\.[0-9]+)?(?: [0-9]{4}| \.NET 2003)?)",
        r"Visual Studio \1（微软集成开发环境）",
        text,
    )
    return restore_sections(text, protected)


def strip_trailing_whitespace(text: str) -> str:
    has_final_newline = text.endswith(("\n", "\r"))
    normalized = "\n".join(line.rstrip(" \t") for line in text.splitlines())
    return normalized + ("\n" if has_final_newline else "")


def short_summary(text: str, limit: int = 28) -> str:
    text = text.strip()
    if not text:
        return ""
    for sep in ("。", ".", "；", ";", "：", ":"):
        idx = text.find(sep)
        if 0 < idx <= limit + 12:
            return text[:idx].strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def contains_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def describe_variable_name(name: str) -> str:
    name = name.strip()
    if name in COMMON_VARIABLE_DESCRIPTIONS:
        return COMMON_VARIABLE_DESCRIPTIONS[name]
    tokens = [token for token in re.split(r"[_-]+", name.strip("<>")) if token]
    prefix = ""
    if tokens and tokens[0] in {"CMAKE", "CTEST", "CPACK", "PROJECT"}:
        prefix_token = tokens.pop(0)
        prefix = {
            "CMAKE": "CMake ",
            "CTEST": "CTest ",
            "CPACK": "CPack ",
            "PROJECT": "当前项目",
        }[prefix_token]
    translated = [VARIABLE_TOKEN_TEXT[token] for token in tokens if token in VARIABLE_TOKEN_TEXT]
    if translated:
        phrase = "、".join(dict.fromkeys(translated))
        return f"{prefix}{phrase}相关变量，其精确取值和作用域以当前页面或脚本上下文为准。"
    return "当前示例使用的变量，其值由前面的命令、调用参数或运行环境提供。"


def extract_variable_names(line: str) -> list[str]:
    names: list[str] = []
    patterns = (
        r"\$\{([A-Za-z_][A-Za-z0-9_<>-]*)\}",
        r"\$(?:ENV|CACHE)\{([A-Za-z_][A-Za-z0-9_<>-]*)\}",
    )
    for pattern in patterns:
        names.extend(re.findall(pattern, line))
    command_match = re.match(
        r"\s*(?:set|option|foreach|unset)\s*\(\s*([A-Za-z_][A-Za-z0-9_<>-]*)",
        line,
        re.IGNORECASE,
    )
    if command_match:
        names.append(command_match.group(1))
    assignment_match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_<>-]*)\s*=", line)
    if assignment_match:
        names.append(assignment_match.group(1))
    names.extend(re.findall(r"(?:^|\s)-D([A-Za-z_][A-Za-z0-9_<>-]*)(?==|\s|$)", line))
    cache_entry_match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_<>-]*):[A-Za-z_][A-Za-z0-9_]*=", line)
    if cache_entry_match:
        names.append(cache_entry_match.group(1))
    declaration_match = re.search(
        r"\b(?:bool|char|short|int|long|float|double|size_t|auto|string|std::string)\s+(?:const\s+)?([A-Za-z_][A-Za-z0-9_]*)\b",
        line,
    )
    if declaration_match:
        names.append(declaration_match.group(1))
    return list(dict.fromkeys(names))


def explain_comment(comment: str) -> str:
    comment = comment.strip().strip("*/ ").strip()
    if comment in COMMENT_EXPLANATIONS:
        return COMMENT_EXPLANATIONS[comment]
    lowered = comment.lower()
    if lowered.startswith("save "):
        return "保存当前设置或参数，以便后续步骤恢复或复用。"
    if lowered.startswith("restore "):
        return "恢复先前保存的设置或参数。"
    if lowered.startswith("include "):
        return "引入当前步骤所需的文件、模块或依赖。"
    if lowered.startswith("add "):
        return "把注释所指的源文件、目标或配置加入当前构建。"
    if lowered.startswith("define "):
        return "定义后续代码会使用的变量、宏或配置。"
    if lowered.startswith(("check ", "test ", "try ")):
        return "检查注释所指的条件或功能是否可用。"
    if lowered.startswith(("output", "print", "show")):
        return "输出或展示当前步骤产生的结果。"
    if not comment:
        return "这是用于分隔或组织当前代码段的注释。"
    return "这是代码作者保留的说明，描述当前步骤的目的、输入输出或使用限制；英文原文保留在代码中。"


def explain_symbols(line: str, language: str) -> list[str]:
    explanations: list[str] = []
    variables = extract_variable_names(line)
    if variables:
        variable_text = "；".join(
            f"`{name}`：{describe_variable_name(name).rstrip('。')}" for name in variables[:5]
        )
        explanations.append(f"变量说明：{variable_text}")

    generator_ops = list(dict.fromkeys(re.findall(r"\$<([A-Za-z0-9_]+)(?=[:>])", line)))
    if generator_ops:
        explanations.append(
            "生成器表达式："
            + "；".join(
                f"`$<{operator}:...>` 在生成构建系统时按当前目标和配置计算结果"
                for operator in generator_ops[:5]
            )
        )

    stripped = line.strip()
    conditional_context = bool(
        re.match(r"(?:if|elseif|while)\s*\(", stripped, re.IGNORECASE)
        or any(re.match(rf"{operator}\b", stripped) for operator in CMAKE_OPERATOR_DESCRIPTIONS)
    )
    if language == "cmake" and conditional_context:
        operators = [
            operator
            for operator in CMAKE_OPERATOR_DESCRIPTIONS
            if re.search(rf"\b{re.escape(operator)}\b", stripped)
        ]
        if operators:
            explanations.append(
                "条件运算符："
                + "；".join(
                    f"`{operator}` 表示{CMAKE_OPERATOR_DESCRIPTIONS[operator]}"
                    for operator in operators
                )
            )

    operator_scope = re.sub(r"<[^>]*>", "", stripped)
    symbol_operators: list[str] = []
    for operator in SYMBOL_OPERATOR_DESCRIPTIONS:
        escaped = re.escape(operator)
        if operator == "=":
            found = re.search(r"(?<![!<>=])=(?!=)", operator_scope)
        elif operator == "<":
            found = re.search(r"(?<!<)<(?![<=])", operator_scope)
        elif operator == ">":
            found = re.search(r"(?<!>)>(?![>=])", operator_scope)
        elif operator in {"+", "-", "*", "/", "%", "|", "&", "^", "~"}:
            found = re.search(rf"(?:\s|\()({escaped})(?:\s|\))", operator_scope)
        else:
            found = re.search(escaped, operator_scope)
        if found:
            symbol_operators.append(operator)
    if language in {"console", "shell", "sh", "bash", "bat", "text"}:
        symbol_operators = [operator for operator in symbol_operators if operator == "="]
    if symbol_operators:
        rendered_operators: list[str] = []
        for operator in symbol_operators:
            description = SYMBOL_OPERATOR_DESCRIPTIONS[operator]
            if language in {"c++", "cpp"} and operator == "<<" and re.search(r"\b(?:cout|cerr|clog)\b", stripped):
                description = "流插入，把右侧内容写入输出流"
            elif language in {"c++", "cpp"} and operator == ">>" and re.search(r"\bcin\b", stripped):
                description = "流提取，从输入流读取内容"
            rendered_operators.append(f"`{operator}` 表示{description}")
        explanations.append(
            "运算符："
            + "；".join(rendered_operators)
        )

    if language in {"console", "shell", "sh", "bash", "bat", "text"}:
        options = [
            option
            for option in CLI_OPTION_DESCRIPTIONS
            if re.search(rf"(?<!\S){re.escape(option)}(?:\S*|)(?=\s|=|$)", stripped)
        ]
        if options:
            explanations.append(
                "命令行选项："
                + "；".join(
                    f"`{option}` 用于{CLI_OPTION_DESCRIPTIONS[option]}" for option in options
                )
            )
    return explanations


def format_explanation_html(text: str) -> str:
    parts = re.split(r"(`[^`]+`)", text)
    rendered: list[str] = []
    for part in parts:
        if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
            rendered.append(
                "<code class=\"docutils literal notranslate\"><span class=\"pre\">"
                + html.escape(part[1:-1])
                + "</span></code>"
            )
        else:
            rendered.append(html.escape(part))
    return "".join(rendered)


def extract_title(html_text: str) -> str:
    match = TITLE_RE.search(html_text)
    if not match:
        return ""
    title = clean_text(match.group(1))
    if "—" in title:
        title = title.split("—", 1)[0].strip()
    return title


def extract_h1(html_text: str) -> str:
    match = H1_RE.search(html_text)
    return clean_text(match.group(1)) if match else ""


def extract_first_summary(html_text: str) -> str:
    main = BODY_RE.search(html_text)
    scope = main.group(1) if main else html_text
    scope = GENERATED_SYMBOL_NOTE_RE.sub(" ", scope)
    scope = CONTENTS_NAV_RE.sub(" ", scope)
    for match in PARAGRAPH_RE.finditer(scope):
        attrs = match.group("attrs") or ""
        if "topic-title" in attrs or "admonition-title" in attrs or "versionmodified" in attrs:
            continue
        text = clean_text(match.group("body"))
        if not text:
            continue
        if text in {"目录", "注意", "提示"}:
            continue
        if re.fullmatch(r"(?:版本\s*)?[0-9.]+\s*(?:版本)?(?:新增|更改|已弃用).*", text):
            continue
        return text
    return ""


def build_symbol_note(title: str, symbol: str, description: str) -> str:
    return (
        f"\n{SYMBOL_NOTE_BEGIN}\n"
        "<div class=\"admonition note cmake-symbol-note\">"
        f"<p class=\"admonition-title\">{html.escape(title)}</p>"
        "<p><code class=\"docutils literal notranslate\"><span class=\"pre\">"
        f"{html.escape(symbol)}</span></code>：{html.escape(description)}</p>"
        "</div>\n"
        f"{SYMBOL_NOTE_END}\n"
    )


def enhance_symbol_notes(path: Path, html_text: str) -> tuple[str, int]:
    html_text = GENERATED_SYMBOL_NOTE_RE.sub("\n", html_text)
    relative = path.relative_to(ZH_ROOT).as_posix()
    note_title = ""
    symbol = ""
    description = ""

    if relative.startswith("variable/"):
        symbol = extract_h1(html_text)
        description = extract_first_summary(html_text) or describe_variable_name(symbol)
        note_title = "变量说明"
    elif relative.startswith("manual/") and path.name in REFERENCE_MANUAL_DESCRIPTIONS:
        symbol = extract_h1(html_text)
        description = REFERENCE_MANUAL_DESCRIPTIONS[path.name]
        note_title = "手册说明"

    count = 0
    if note_title and symbol and description:
        match = H1_RE.search(html_text)
        if match:
            note = build_symbol_note(note_title, symbol, description)
            html_text = html_text[: match.end()] + note + html_text[match.end() :]
            count = 1

    if relative == "index.html":
        for filename, manual_description in REFERENCE_MANUAL_DESCRIPTIONS.items():
            pattern = re.compile(
                rf'(<a class="reference internal" href="manual/{re.escape(filename)}">)(.*?)(</a>)'
            )

            def replace_manual_link(match: re.Match[str]) -> str:
                original_label = clean_text(match.group(2)).split("：", 1)[0]
                return f"{match.group(1)}{html.escape(original_label)}：{html.escape(manual_description)}{match.group(3)}"

            html_text, replacements = pattern.subn(replace_manual_link, html_text)
            count += replacements
    return html_text, count


def choose_display_title(lang: str, path: str, title: str, h1: str, summary: str) -> str:
    base = h1 or title or path
    base = base.strip() or path
    if lang != "zh":
        return base
    if path.startswith("manual/"):
        manual_description = REFERENCE_MANUAL_DESCRIPTIONS.get(Path(path).name)
        if manual_description:
            return f"{base}：{manual_description}"
    if contains_chinese(base):
        return base
    return base


def build_keywords(title: str, h1: str, summary: str, path: str) -> str:
    parts = [title, h1, summary, path]
    seen: list[str] = []
    for part in parts:
        part = WS_RE.sub(" ", part).strip()
        if part and part not in seen:
            seen.append(part)
    return " ".join(seen)


def detect_literal_language(code: str) -> str:
    stripped = code.strip()
    if not stripped:
        return "text"
    if stripped.startswith("<") and stripped.endswith(">"):
        return "xml"
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    if "\n" in stripped:
        first = stripped.splitlines()[0].strip()
        if first.endswith(":") and not first.startswith("$"):
            return "yaml"
    if re.search(r"^[A-Za-z_][A-Za-z0-9_]*\s*\(", stripped, re.MULTILINE):
        return "cmake"
    if re.search(r"^\s*#include\b", stripped, re.MULTILINE):
        return "c"
    if re.search(r"^\s*(\$ |> )", stripped, re.MULTILINE):
        return "console"
    return "text"


def explain_cmake_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith("#"):
        return "这是 CMake 注释。" + explain_comment(stripped.lstrip("#"))
    if stripped in {"else()", "elseif()", "endif()", "endforeach()", "endfunction()", "endmacro()", "endwhile()", "endblock()"}:
        return "这一行结束或切换上一段控制结构的分支。"
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*$", stripped)
    if not match:
        if stripped in {"{", "}", "};"}:
            return "这一行用于界定当前代码块的开始或结束。"
        return "这一行继续补充当前命令或表达式的内容。"
    cmd = match.group(1)
    args = match.group(2).strip()
    if cmd == "set":
        arg_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s+(.+)", args)
        if arg_match:
            return f"调用 `set()` 命令，把变量 `{arg_match.group(1)}` 设为给定的值。"
    if cmd == "message":
        return "调用 `message()` 输出提示信息，方便观察脚本执行结果。"
    if cmd == "foreach":
        return "开始一个 `foreach()` 循环，后续语句会按列表元素依次执行。"
    if cmd == "if":
        return "开始一个 `if()` 条件判断，根据条件结果选择是否执行后续语句。"
    if cmd == "function":
        return "定义一个函数，并为其后的语句建立独立作用域。"
    if cmd == "macro":
        return "定义一个宏，后续语句会在调用方作用域内展开执行。"
    if cmd == "add_library" and "TARGET_OBJECTS" in stripped:
        return "定义库目标，并把对象库中的编译结果并入当前库。"
    if cmd == "add_executable" and "TARGET_OBJECTS" in stripped:
        return "定义可执行目标，并把对象库中的编译结果并入当前程序。"
    desc = CMK_CMD_TEXT.get(cmd)
    if desc:
        return f"调用 `{cmd}()` 命令，{desc}"
    return f"调用 `{cmd}()` 命令，具体行为由这一行传入的参数决定。"


def explain_console_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    prompt = ""
    content = stripped
    if stripped.startswith("$ "):
        prompt = "$ "
        content = stripped[2:].strip()
    elif stripped.startswith("> "):
        prompt = "> "
        content = stripped[2:].strip()
    token = content.split()[0] if content else ""
    if token in SHELL_CMD_TEXT:
        if token == "cmake" and " -P " in f" {content} ":
            return "这是一条 `cmake -P` 命令，用脚本模式直接执行指定的 CMake 脚本文件。"
        return f"这是一条命令行输入，{SHELL_CMD_TEXT[token]}"
    if prompt:
        return "这是一条命令行输入，用来演示终端中实际执行的命令。"
    return f"这是命令执行后的输出结果，内容为：{content}"


def explain_c_family_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
        return "这是代码注释。" + explain_comment(stripped.lstrip("/* "))
    if stripped.startswith("#include"):
        return "这一行引入头文件，使当前源文件可以使用其中声明的类型、函数或宏。"
    if stripped.startswith("#define"):
        return "这一行定义预处理宏，供后续代码在编译前展开使用。"
    if stripped.startswith("#if") or stripped.startswith("#ifdef") or stripped.startswith("#ifndef"):
        return "这一行开始预处理条件分支，按宏条件决定后续代码是否参与编译。"
    if stripped.startswith("#elif") or stripped.startswith("#else") or stripped.startswith("#endif"):
        return "这一行切换或结束预处理条件分支。"
    if stripped in {"{", "}", "};"}:
        return "这一行用于界定当前代码块、结构体或函数体的开始或结束。"
    if re.match(r"(return)\b", stripped):
        return "这一行从当前函数返回结果，或者直接结束当前函数执行。"
    if re.match(r"(if|for|while|switch)\s*\(", stripped):
        return "这一行开始控制流程语句，用于分支判断或循环。"
    if re.match(r"(else|case|default)\b", stripped):
        return "这一行切换到另一条分支逻辑。"
    if re.search(r"\)\s*\{?$", stripped) and "(" in stripped:
        return "这一行定义或调用一个函数/方法，具体行为取决于参数和上下文。"
    if "=" in stripped and stripped.endswith(";"):
        return "这一行完成赋值或初始化，把右侧结果写入左侧变量。"
    return "这一行补充当前 C/C++ 代码逻辑，具体作用取决于其上下文。"


def explain_data_line(line: str, language: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped in {"{", "}", "[", "]", "],", "},"}:
        return "这一行用于界定当前数据结构的层级范围。"
    if language == "json" and ":" in stripped:
        key = stripped.split(":", 1)[0].strip().strip("\"")
        return f"这一行给键 `{key}` 指定对应的值。"
    if language == "yaml" and ":" in stripped:
        key = stripped.split(":", 1)[0].strip()
        return f"这一行声明字段 `{key}` 及其取值。"
    if language == "xml":
        return "这一行给出一个 XML 标签或其内容，用于描述结构化节点。"
    return "这一行给出数据项或文本内容，用于补充当前示例。"


def explain_text_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith("#") or stripped.startswith(";"):
        return "这是配置或脚本注释。" + explain_comment(stripped.lstrip("#;"))
    if stripped in CODE_TEXT_EXPLANATIONS:
        return CODE_TEXT_EXPLANATIONS[stripped]
    if re.match(r"[A-Za-z_][A-Za-z0-9_]*\s*=", stripped):
        return "这一行把某个名称与给定值关联起来，常见于配置或键值示例。"
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9 /+().:'_-]+", stripped):
        return "这是示例中的英文标题或状态文本，用于说明紧随其后的命令、阶段或输出。"
    return f"这一行给出示例文本或输出，用来说明：{stripped}"


def explain_line(line: str, language: str) -> str:
    if language in {"cmake"}:
        base = explain_cmake_line(line)
    elif language in {"console", "shell", "sh", "bash", "bat"}:
        base = explain_console_line(line)
    elif language in {"c", "c++", "cpp", "javascript"}:
        base = explain_c_family_line(line)
    elif language in {"json", "yaml", "xml"}:
        base = explain_data_line(line, language)
    else:
        base = explain_text_line(line)
    symbol_notes = explain_symbols(line, language)
    if not symbol_notes:
        return base
    return base.rstrip("。") + "；" + "；".join(symbol_notes) + "。"


def build_note_html(code: str, language: str) -> str:
    rows: list[str] = []
    for raw_line in code.splitlines():
        display = raw_line.rstrip()
        if not display.strip():
            continue
        explanation = explain_line(display, language)
        if not explanation:
            continue
        escaped_line = html.escape(display)
        rows.append(
            "<li><p><code class=\"docutils literal notranslate\">"
            f"<span class=\"pre\">{escaped_line}</span></code>：{format_explanation_html(explanation)}</p></li>"
        )
    if not rows:
        return ""
    return (
        f"\n{NOTE_BEGIN}\n"
        "<div class=\"admonition note cmake-code-notes\">"
        "<p class=\"admonition-title\">代码说明</p>"
        "<ul class=\"simple\">"
        + "".join(rows)
        + "</ul></div>\n"
        f"{NOTE_END}\n"
    )


def extract_code(block_html: str) -> str:
    match = re.search(r"<pre\b[^>]*>(.*?)</pre>", block_html, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""
    code = match.group(1).replace("<span></span>", "")
    code = TAG_RE.sub("", code)
    code = html.unescape(code).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in code.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def enhance_code_blocks(html_text: str) -> tuple[str, int]:
    count = 0
    html_text = GENERATED_NOTE_RE.sub("\n", html_text)

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        block = match.group(1)
        language = match.group(2).lower() if match.group(2) else detect_literal_language(extract_code(block))
        code = extract_code(block)
        note = build_note_html(code, language)
        if note:
            count += 1
        return block + note

    html_text = CODE_BLOCK_RE.sub(replace, html_text)
    return html_text, count


def patch_version_switch() -> bool:
    path = ZH_ROOT / "version_switch.js"
    original = path.read_text(encoding="utf-8")
    updated = original.replace(
        "// check beforehand if url exists, else redirect to version's start page",
        "// 先检查目标页面是否存在；如果不存在，则跳转到该版本的首页",
    )
    updated = updated.replace("latest release", "最新版本")
    updated = updated.replace(
        "Or, select a version from the drop-down menu above.",
        "或者从上方下拉菜单中选择其他版本。",
    )
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def iter_html_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.html") if path.is_file())


def rebuild_index() -> dict[str, list[dict[str, str]]]:
    root_data: dict[str, list[dict[str, str]]] = {}
    for lang, base in (("zh", ZH_ROOT), ("en", EN_ROOT)):
        entries: list[dict[str, str]] = []
        html_files = iter_html_files(base)
        html_files.sort(key=lambda p: (
            { "genindex.html": 0, "index.html": 1, "search.html": 2 }.get(p.relative_to(base).as_posix(), 3),
            p.relative_to(base).as_posix(),
        ))
        for path in html_files:
            rel = path.relative_to(base).as_posix()
            text = path.read_text(encoding="utf-8")
            title = extract_title(text)
            h1 = extract_h1(text)
            summary = extract_first_summary(text)
            display_title = choose_display_title(lang, rel, title, h1, summary)
            entry = {
                "path": rel,
                "title": display_title,
                "keywords": build_keywords(title, h1, summary, rel),
            }
            if summary:
                entry["summary"] = short_summary(summary, limit=60)
            entries.append(entry)
        root_data[lang] = entries
    INDEX_PATH.write_text(json.dumps(root_data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return root_data


def main() -> None:
    html_files = iter_html_files(ZH_ROOT)
    changed_files = 0
    changed_paths: list[str] = []
    note_count = 0
    symbol_note_count = 0
    for path in html_files:
        original = path.read_text(encoding="utf-8")
        updated = apply_text_replacements(original)
        updated, symbol_notes = enhance_symbol_notes(path, updated)
        updated, notes = enhance_code_blocks(updated)
        updated = strip_trailing_whitespace(updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1
            changed_paths.append(path.relative_to(ZH_ROOT).as_posix())
        note_count += notes
        symbol_note_count += symbol_notes

    version_switch_changed = patch_version_switch()
    index_data = rebuild_index()
    report = {
        "changed_html_files": changed_files,
        "changed_paths": changed_paths,
        "code_notes_inserted": note_count,
        "symbol_notes_inserted": symbol_note_count,
        "version_switch_changed": version_switch_changed,
        "zh_pages": len(index_data.get("zh", [])),
        "en_pages": len(index_data.get("en", [])),
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
