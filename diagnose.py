"""Diagnostic and quick-fix helper for the Long-Form Memory project."""

import importlib.util
import sys
from pathlib import Path


REQUIRED_PACKAGES = {
    "flask": "Flask",
    "sqlalchemy": "SQLAlchemy",
}

OPTIONAL_PACKAGES = {
    "faiss": "FAISS (for vector search)",
    "sentence_transformers": "Sentence Transformers (for embeddings)",
}

CORE_MODULES = [
    ("memory_extraction", "Memory extraction module"),
    ("memory_storage", "Memory storage module"),
    ("memory_retrieval", "Memory retrieval module"),
    ("conversation_agent", "Conversation agent module"),
]


def _is_installed(module_name: str) -> bool:
    """Check package presence without importing module side effects."""
    return importlib.util.find_spec(module_name) is not None


def _python_version_ok() -> bool:
    version = sys.version_info
    return version.major > 3 or (version.major == 3 and version.minor >= 9)


def _print_header() -> None:
    print("=" * 70)
    print("  DIAGNOSTIC SCRIPT - Long-Form Memory System")
    print("=" * 70)
    print()


def _check_python() -> None:
    print("1. Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    if _python_version_ok():
        print("   ✓ Python version OK")
    else:
        print("   ⚠ WARNING: Python 3.9+ recommended")

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        print("   ✓ Virtual environment active")
    else:
        print("   ⚠ WARNING: Virtual environment not detected")
    print()


def _check_packages() -> tuple[list[str], list[str]]:
    print("2. Checking required packages...")
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for package, display_name in REQUIRED_PACKAGES.items():
        if _is_installed(package):
            print(f"   ✓ {display_name}")
        else:
            print(f"   ✗ {display_name} - MISSING (REQUIRED)")
            missing_required.append(package)

    for package, display_name in OPTIONAL_PACKAGES.items():
        if _is_installed(package):
            print(f"   ✓ {display_name}")
        else:
            print(f"   ⚠ {display_name} - MISSING (Optional - will use fallback)")
            missing_optional.append(package)

    print()
    return missing_required, missing_optional


def _check_data_dirs(project_root: Path) -> bool:
    print("3. Checking data directory...")
    data_dir = project_root / "data"
    embeddings_dir = data_dir / "embeddings"

    try:
        data_dir.mkdir(exist_ok=True)
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ Data directory ready: {data_dir}")
        print(f"   ✓ Embeddings directory ready: {embeddings_dir}")
        print()
        return True
    except OSError as exc:
        print(f"   ✗ Failed to prepare data directories: {exc}")
        print()
        return False


def _check_core_modules(project_root: Path) -> list[str]:
    print("4. Testing core modules...")
    src_dir = project_root / "src"
    import_errors: list[str] = []

    if not src_dir.exists():
        message = f"src directory not found at {src_dir}"
        print(f"   ✗ {message}")
        print()
        return [message]

    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    for module_name, display_name in CORE_MODULES:
        module_file = src_dir / f"{module_name}.py"
        if not module_file.exists():
            error_message = f"missing file: {module_file}"
            print(f"   ✗ {display_name}: {error_message}")
            import_errors.append(error_message)
            continue

        try:
            __import__(module_name)
            print(f"   ✓ {display_name}")
        except Exception as exc:
            error_message = f"{module_name}: {exc}"
            print(f"   ✗ {display_name}: {exc}")
            import_errors.append(error_message)

    print()
    return import_errors


def _print_install_hints(missing_required: list[str], missing_optional: list[str]) -> None:
    python_cmd = f'"{sys.executable}" -m pip install'

    if missing_required:
        print("⚠ REQUIRED PACKAGES MISSING")
        print("Run this command to install missing required packages:")
        print(f"   {python_cmd} {' '.join(missing_required)}")
        print()

    if missing_optional:
        print("ℹ Optional packages missing (system works without them)")
        print("To enable full semantic retrieval features, run:")
        print(f"   {python_cmd} {' '.join(missing_optional)}")
        print("Note: Without FAISS and sentence-transformers, text fallback retrieval is used.")
        print()


def run_diagnostics() -> int:
    project_root = Path(__file__).resolve().parent

    _print_header()
    _check_python()
    missing_required, missing_optional = _check_packages()
    dirs_ok = _check_data_dirs(project_root)
    import_errors = _check_core_modules(project_root)
    _print_install_hints(missing_required, missing_optional)

    print("=" * 70)
    print("  DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print()

    if missing_required:
        print("⚠ ACTION REQUIRED: Install missing required packages")
        print(f"   \"{sys.executable}\" -m pip install {' '.join(missing_required)}")
    elif import_errors or not dirs_ok:
        print("⚠ ACTION REQUIRED: Resolve the module/data issues listed above")
    else:
        print("✓ Core checks passed")
        print("You can now run:")
        print(f"   \"{sys.executable}\" src/demo.py")

    if missing_optional:
        print()
        print("TIP: Install optional dependencies for best retrieval quality")
        print(f"   \"{sys.executable}\" -m pip install {' '.join(missing_optional)}")

    if missing_required or import_errors or not dirs_ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_diagnostics())