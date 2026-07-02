import os
import sys
import zipfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: package_apk_assets.py <input.apk> <assets_dir> <output.apk>", file=sys.stderr)
        return 2

    input_apk = Path(sys.argv[1])
    assets_dir = Path(sys.argv[2])
    output_apk = Path(sys.argv[3])

    if not input_apk.is_file():
        print(f"input APK not found: {input_apk}", file=sys.stderr)
        return 1
    if not assets_dir.is_dir():
        print(f"assets directory not found: {assets_dir}", file=sys.stderr)
        return 1

    output_apk.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_apk, "r") as zin, zipfile.ZipFile(
        output_apk, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True
    ) as zout:
        for info in zin.infolist():
            name = info.filename.replace("\\", "/")
            if name.startswith("META-INF/") or name.startswith("assets/"):
                continue
            data = zin.read(info.filename)
            info.filename = name
            zout.writestr(info, data)

        for path in sorted(assets_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(assets_dir).as_posix()
            archive_name = "assets/" + rel
            zip_info = zipfile.ZipInfo(archive_name)
            zip_info.date_time = (1980, 1, 1, 0, 0, 0)
            zip_info.compress_type = zipfile.ZIP_DEFLATED
            with path.open("rb") as f:
                zout.writestr(zip_info, f.read())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
