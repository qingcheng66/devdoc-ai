import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    print("Starting DevDoc AI in development mode...")
    subprocess.run(
        [sys.executable, "-m", "gradio", str(project_root / "app.py")],
        cwd=str(project_root),
    )


if __name__ == "__main__":
    main()
