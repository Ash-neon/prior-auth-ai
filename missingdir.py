#!/usr/bin/env python3
import os
from pathlib import Path

missing_dirs = [
    # Frontend dirs
    "frontend/components/ui",
    "frontend/components/layout",
    "frontend/components/auth",
    "frontend/components/pa",
    "frontend/components/documents",
    "frontend/components/analytics",
    "frontend/components/common",
    "frontend/pages/pa",
    "frontend/pages/analytics",
    "frontend/pages/admin",
    "frontend/pages/api",
    "frontend/hooks",
    "frontend/lib",
    "frontend/store",
    "frontend/styles",
    "frontend/types",
    "frontend/public/images",
    "frontend/public/icons",
    "frontend/public/fonts",

    # Backend test dirs
    "backend/tests/unit/test_services",
    "backend/tests/unit/test_utils",
    "backend/tests/unit/test_models",
    "backend/tests/integration/test_api",
    "backend/tests/integration/test_workflows",
    "backend/tests/fixtures/sample_documents",
    "backend/tests/fixtures/mock_responses",
]

def ensure_dir(path):
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    keep = p / ".gitkeep"
    keep.write_text("")  # mark empty dirs
    print(f"Created: {p} (+ .gitkeep)")

print("\n📁 Adding missing directories into existing repo...\n")

for d in missing_dirs:
    ensure_dir(d)

print("\n✅ Done! Missing directories added successfully.")
print("👉 Now run:\n")
print("   git add .")
print("   git commit -m 'Add missing folders and .gitkeep files'")
print("   git push")

