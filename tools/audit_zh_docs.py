from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "assets" / "docs"
ZH_ROOT = DOCS_ROOT / "zh"
EN_ROOT = DOCS_ROOT / "en"
REPORT_PATH = ROOT / "docs_quality_report.json"

NOTE_BEGIN = "<!-- CMAKE_ZH_CODE_NOTES_BEGIN -->"
NOTE_END = "<!-- CMAKE_ZH_CODE_NOTES_END -->"

CODE_BLOCK_RE = re.compile(
    r'(<div class="highlight-([A-Za-z0-9_+\-]+)[^"]*"><div class="highlight"><pre>.*?</pre></div>\s*</div>|<pre class="literal-block"[^>]*>.*?</pre>)',
    re.DOTALL,
)
PRE_RE = re.compile(r"<pre\b[^>]*>.*?</pre>", re.IGNORECASE | re.DOTALL)
CODE_RE = re.compile(r"<code\b[^>]*>.*?</code>", re.IGNORECASE | re.DOTALL)
SCRIPT_STYLE_RE = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>)", re.IGNORECASE | re.DOTALL)
NOTE_RE = re.compile(
    rf"{re.escape(NOTE_BEGIN)}.*?{re.escape(NOTE_END)}",
    re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
TEXT_RE = re.compile(r">([^<]+)<")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+\-./]*")

WHITELIST = {
    "cmake",
    "kitware",
    "sphinx",
    "html",
    "json",
    "xml",
    "yaml",
    "utf",
    "api",
    "cli",
    "ui",
    "id",
    "cmakelists.txt",
    "todo",
    "index.html",
    "search.html",
    "genindex.html",
    "cmake.org",
    "cmake.com.cn",
}


def clean_text(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def iter_html_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.html") if path.is_file())


def extract_code_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    for match in CODE_BLOCK_RE.finditer(text):
        pre_match = re.search(r"<pre\b[^>]*>(.*?)</pre>", match.group(1), re.DOTALL | re.IGNORECASE)
        if not pre_match:
            continue
        blocks.append(clean_text(pre_match.group(1).replace("<span></span>", "")))
    return blocks


def strip_for_residual_scan(text: str) -> str:
    text = NOTE_RE.sub(" ", text)
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = PRE_RE.sub(" ", text)
    text = CODE_RE.sub(" ", text)
    return text


def is_actionable_text(text: str) -> bool:
    if text.endswith("文档 - CMake 构建系统"):
        return False
    if text.startswith("© 版权所有"):
        return False
    if "title=" in text or text.endswith("\">¶"):
        return False
    words = ENGLISH_WORD_RE.findall(text)
    if not words:
        return False
    lower_words = [word.lower() for word in words]
    if all(word in WHITELIST for word in lower_words):
        return False
    has_chinese = any("\u4e00" <= ch <= "\u9fff" for ch in text)
    if has_chinese and re.fullmatch(r"[^A-Za-z]*[\u4e00-\u9fff0-9 ()（）:：,，./+-]*（[^）]*[A-Za-z][^）]*）[^A-Za-z]*", text):
        return False
    if not has_chinese:
        if re.fullmatch(r"[A-Za-z0-9_:+<>()./\"' -]+", text):
            return False
        if len(lower_words) < 5:
            return False
    alpha_words = [word for word in words if re.search(r"[A-Za-z]{2,}", word)]
    if not alpha_words:
        return False
    letters_only = "".join(alpha_words)
    if letters_only.upper() == letters_only and "_" in letters_only:
        return False
    if len(alpha_words) == 1 and len(alpha_words[0]) <= 4:
        return False
    return True


def collect_residual_samples(root: Path, limit: int = 120) -> tuple[int, list[dict[str, str]], Counter]:
    count = 0
    samples: list[dict[str, str]] = []
    top_words: Counter = Counter()
    for path in iter_html_files(root):
        rel = path.relative_to(root).as_posix()
        text = strip_for_residual_scan(path.read_text(encoding="utf-8"))
        seen_local: set[str] = set()
        for match in TEXT_RE.finditer(text):
            candidate = clean_text(match.group(1))
            if not candidate or candidate in seen_local:
                continue
            if is_actionable_text(candidate):
                count += 1
                seen_local.add(candidate)
                for word in ENGLISH_WORD_RE.findall(candidate):
                    if len(word) >= 4:
                        top_words[word.lower()] += 1
                if len(samples) < limit:
                    samples.append({"path": rel, "text": candidate})
    return count, samples, top_words


def compare_pairwise_code() -> dict[str, object]:
    zh_files = {path.relative_to(ZH_ROOT).as_posix(): path for path in iter_html_files(ZH_ROOT)}
    en_files = {path.relative_to(EN_ROOT).as_posix(): path for path in iter_html_files(EN_ROOT)}
    only_zh = sorted(set(zh_files) - set(en_files))
    only_en = sorted(set(en_files) - set(zh_files))
    code_mismatch_pages: list[dict[str, object]] = []
    total_blocks = 0
    total_notes = 0
    total_mismatch_blocks = 0
    for rel in sorted(set(zh_files) & set(en_files)):
        zh_text = zh_files[rel].read_text(encoding="utf-8")
        en_text = en_files[rel].read_text(encoding="utf-8")
        zh_blocks = extract_code_blocks(zh_text)
        en_blocks = extract_code_blocks(en_text)
        total_blocks += len(zh_blocks)
        total_notes += zh_text.count(NOTE_BEGIN)
        mismatches: list[int] = []
        for index, (zh_block, en_block) in enumerate(zip(zh_blocks, en_blocks), start=1):
            if zh_block != en_block:
                mismatches.append(index)
        total_mismatch_blocks += len(mismatches)
        if mismatches or len(zh_blocks) != len(en_blocks):
            code_mismatch_pages.append(
                {
                    "path": rel,
                    "zh_blocks": len(zh_blocks),
                    "en_blocks": len(en_blocks),
                    "mismatch_block_indexes": mismatches[:20],
                }
            )
    return {
        "zh_only_paths": only_zh,
        "en_only_paths": only_en,
        "code_blocks": total_blocks,
        "code_notes": total_notes,
        "code_mismatch_blocks": total_mismatch_blocks,
        "code_mismatch_pages": code_mismatch_pages[:120],
    }


def main() -> None:
    pair_report = compare_pairwise_code()
    residual_count, samples, top_words = collect_residual_samples(ZH_ROOT)
    report = {
        "zh_html_pages": len(iter_html_files(ZH_ROOT)),
        "en_html_pages": len(iter_html_files(EN_ROOT)),
        "paired_path_differences": {
            "zh_only": len(pair_report["zh_only_paths"]),
            "en_only": len(pair_report["en_only_paths"]),
        },
        "code_blocks": pair_report["code_blocks"],
        "code_notes": pair_report["code_notes"],
        "code_mismatch_blocks": pair_report["code_mismatch_blocks"],
        "residual_english_segments": residual_count,
        "top_residual_words": top_words.most_common(80),
        "samples": samples,
        "code_mismatch_pages": pair_report["code_mismatch_pages"],
        "zh_only_paths": pair_report["zh_only_paths"][:80],
        "en_only_paths": pair_report["en_only_paths"][:80],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    REPORT_PATH.write_text(rendered, encoding="utf-8")
    sys.stdout.buffer.write((rendered + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
