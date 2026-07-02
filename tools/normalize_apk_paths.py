import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: normalize_apk_paths.py <input.apk> <output.apk>", file=sys.stderr)
        return 2

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(dst, "w") as zout:
        seen = set()
        for info in zin.infolist():
            data = zin.read(info.filename)
            name = info.filename.replace("\\", "/")
            if name in seen:
                raise RuntimeError(f"duplicate zip entry after path normalization: {name}")
            seen.add(name)

            out_info = zipfile.ZipInfo(name)
            out_info.date_time = info.date_time
            out_info.compress_type = info.compress_type
            out_info.comment = info.comment
            out_info.extra = info.extra
            out_info.external_attr = info.external_attr
            zout.writestr(out_info, data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
