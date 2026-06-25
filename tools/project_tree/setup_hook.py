"""
================================================================================
Project:       Project Tree Generator
File:          setup_hook.py (o generate_tree.py)
Authors:       Michele Bisignano & Mattia Franchini
Date:          January 2026
License:       Apache License 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
================================================================================
"""

import os
import stat
import sys
from pathlib import Path

def install_hook():
    # 1. Locate the .git folder
    try:
        current_dir = Path(__file__).resolve()
        def find_git_root(start_path: Path) -> Path:
            for parent in [start_path] + list(start_path.parents):
                if (parent / ".git").exists():
                    return parent
            raise RuntimeError(".git folder not found")
        
        repo_root = find_git_root(current_dir)
        hooks_dir = repo_root / ".git" / "hooks"
    except Exception as e:
        print(f"[ERROR] {e}. Make sure you are in a Git repository.")
        return

    # 2. Define the hook file path
    hook_path = hooks_dir / "pre-commit"

    # 3. Content of the bash script
    # We use sys.executable to ensure we use the same Python environment that installed the hook.
    python_path = sys.executable
    
    hook_content = (
        "#!/bin/sh\n"
        "echo '[HOOK] Checking Python environment...'\n\n"
        
        f"PY_CMD='{python_path}'\n\n"
        
        "echo \"[HOOK] Using: $PY_CMD\"\n"
        "echo \"[HOOK] Regenerating project tree...\"\n\n"
        
        "# 1. Run the generator\n"
        "$PY_CMD s/project_tree/generate_tree.py\n\n"
        
        "# 2. Add the generated file to the commit\n"
        "git add docs/project_structure/repository_tree.md\n"
    )

    # 4. Write the file
    try:
        # We use binary write or explicit newline to avoid CRLF issues on some git-bash setups
        with open(hook_path, "w", encoding="utf-8", newline='\n') as f:
            f.write(hook_content)
        
        # 5. Make the file executable
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
        
        print(f"[SUCCESS] Hook installed at: {hook_path}")
        print("The tree will now update automatically on every commit.")
        
    except Exception as e:
        print(f"[ERROR] Could not write the hook: {e}")

if __name__ == "__main__":
    install_hook()
