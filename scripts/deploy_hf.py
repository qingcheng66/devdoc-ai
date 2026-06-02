import subprocess
import sys
from pathlib import Path


def main():
    print("Deploying to Hugging Face Spaces...")
    print("Ensure you have:")
    print("  1. Created a Space at https://huggingface.co/new-space")
    print("  2. Set DEEPSEEK_API_KEY in Space Settings > Secrets")
    print("  3. Installed huggingface_hub: pip install huggingface-hub")

    project_root = Path(__file__).parent.parent

    try:
        from huggingface_hub import HfApi
        api = HfApi()
        print("Ready to deploy. Use:")
        print("  huggingface-cli upload <your-space-id> . --repo-type=space")
    except ImportError:
        print("Install huggingface-hub first: pip install huggingface-hub")


if __name__ == "__main__":
    main()
