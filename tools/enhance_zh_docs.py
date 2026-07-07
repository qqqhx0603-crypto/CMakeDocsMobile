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

PROTECTED_RE = re.compile(
    r"(<script\b.*?</script>|<style\b.*?</style>|<pre\b[^>]*>.*?</pre>)",
    re.IGNORECASE | re.DOTALL,
)
GENERATED_NOTE_RE = re.compile(
    rf"\s*{re.escape(NOTE_BEGIN)}.*?{re.escape(NOTE_END)}\s*",
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
    ("Visual Studio", "Visual Studio（集成开发环境）"),
    ("Ninja", "Ninja（构建工具）"),
    ("Makefile", "Makefile（构建脚本）"),
    ("shell", "shell（命令解释器）"),
    ("depfile", "depfile（依赖描述文件）"),
    ("byproduct", "byproduct（副产品文件）"),
    ("byproducts", "byproducts（副产品文件）"),
    ("job server", "job server（作业服务器）"),
    ("order-only dependencies", "order-only dependencies（仅顺序依赖）"),
    ("recipe line", "recipe line（配方行）"),
    ("ALIAS target", "ALIAS target（别名目标）"),
    ("File Sets", "File Sets（文件集）"),
    ("targets", "targets（目标）"),
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
    ("Visual Studio Generators", "Visual Studio Generators（Visual Studio 生成器）"),
    ("Microsoft Visual Studio", "Microsoft Visual Studio（微软 Visual Studio）"),
    ("Dynamic Language Runtime", "Dynamic Language Runtime（动态语言运行时）"),
    ("internal partition unit", "internal partition unit（内部分区单元）"),
    ("module interface unit", "module interface unit（模块接口单元）"),
    ("primary module interface unit", "primary module interface unit（主模块接口单元）"),
    ("strong module ownership", "strong module ownership（强模块归属）"),
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
    (re.compile(r"Added in version ([0-9.]+)\."), r"\1 版本新增。"),
    (re.compile(r"Changed in version ([0-9.]+)\."), r"\1 版本更改。"),
    (re.compile(r"Deprecated since version ([0-9.]+)\."), r"自 \1 版本起已弃用。"),
    (re.compile(r"New in version ([0-9.]+)\."), r"\1 版本新增。"),
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
    for index, original in enumerate(protected):
        text = text.replace(f"__CMAKE_PROTECTED_{index}__", original)
    return text


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
    return restore_sections(text, protected)


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
    scope = CONTENTS_NAV_RE.sub(" ", scope)
    for match in PARAGRAPH_RE.finditer(scope):
        attrs = match.group("attrs") or ""
        if "topic-title" in attrs or "admonition-title" in attrs:
            continue
        text = clean_text(match.group("body"))
        if not text:
            continue
        if text in {"目录", "注意", "提示"}:
            continue
        return text
    return ""


def choose_display_title(lang: str, path: str, title: str, h1: str, summary: str) -> str:
    base = h1 or title or path
    base = base.strip() or path
    if lang != "zh":
        return base
    if contains_chinese(base):
        return base
    desc = short_summary(summary, limit=30)
    if desc and desc != base:
        return f"{base}：{desc}"
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
        return f"这是注释，用来说明：{stripped.lstrip('#').strip() or '当前这段 CMake 逻辑的意图'}。"
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
        return f"这是注释，用来说明：{stripped.lstrip('/* ').strip() or '当前代码的用途'}。"
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
        return f"这是注释，用来说明：{stripped.lstrip('#;').strip() or '当前片段的背景信息'}。"
    if re.match(r"[A-Za-z_][A-Za-z0-9_]*\s*=", stripped):
        return "这一行把某个名称与给定值关联起来，常见于配置或键值示例。"
    return f"这一行给出示例文本或输出，用来说明：{stripped}"


def explain_line(line: str, language: str) -> str:
    if language in {"cmake"}:
        return explain_cmake_line(line)
    if language in {"console", "shell", "sh", "bash", "bat"}:
        return explain_console_line(line)
    if language in {"c", "c++", "cpp", "javascript"}:
        return explain_c_family_line(line)
    if language in {"json", "yaml", "xml"}:
        return explain_data_line(line, language)
    return explain_text_line(line)


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
            f"<span class=\"pre\">{escaped_line}</span></code>：{html.escape(explanation)}</p></li>"
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
    return clean_text(match.group(1).replace("<span></span>", ""))


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
    note_count = 0
    for path in html_files:
        original = path.read_text(encoding="utf-8")
        updated = apply_text_replacements(original)
        updated, notes = enhance_code_blocks(updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1
        note_count += notes

    version_switch_changed = patch_version_switch()
    index_data = rebuild_index()
    report = {
        "changed_html_files": changed_files,
        "code_notes_inserted": note_count,
        "version_switch_changed": version_switch_changed,
        "zh_pages": len(index_data.get("zh", [])),
        "en_pages": len(index_data.get("en", [])),
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
