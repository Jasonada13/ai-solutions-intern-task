import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


FILES = (
    "README.md", "DATA.md", "NOTES.md", "LICENSE",
    "solution.py", "analysis.sql", "run.py", "package_submission.py",
    "tests/test_scaffold.py", "tests/test_candidate.py",
    "data/orders.csv", "data/refunds.csv", "output/summary.csv",
)


def build_archive(root: Path) -> Path:
    archive = root / "submission.zip"
    archive.unlink(missing_ok=True)
    for name in FILES:
        path = root / name
        if not path.is_file():
            raise ValueError(f"Missing {name}. Complete the task and run python3 run.py before packaging.")
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"{name} must be a regular file inside the task folder.")
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as submission:
        for name in FILES:
            submission.write(root / name, arcname=name)
    return archive


def main() -> int:
    try:
        archive = build_archive(Path(__file__).resolve().parent)
    except (OSError, ValueError) as error:
        print(f"Unable to package submission: {error}", file=sys.stderr)
        return 1
    print(f"Created {archive.name}. Email it through your recruiter invitation or reply channel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
