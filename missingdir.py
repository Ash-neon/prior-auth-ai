#!/usr/bin/env python3
"""
Prior Auth AI - Missing File/Directory Fixer
------------------------------------------------
This script FIXES an existing repository by:

✔ Adding missing directories
✔ Adding missing files
✔ Adding .gitkeep only to TRULY empty dirs
✔ NEVER overwriting existing files
✔ NEVER creating a nested repo

This is the correct version for updating an already-generated Git repo.
"""

import os
from pathlib import Path

BASE = Path(".")  # Use current repo directory


# ---------------------------------------------------------
# 1. FULL REPO STRUCTURE (directories + expected files)
# ---------------------------------------------------------
structure = {
    "backend/tests": ["__init__.py", "conftest.py"],
    "backend/tests/unit/test_services": [],
    "backend/tests/unit/test_utils": [],
    "backend/tests/unit/test_models": [],
    "backend/tests/integration/test_api": [],
    "backend/tests/integration/test_workflows": [],
    "backend/tests/fixtures/sample_documents": [],
    "backend/tests/fixtures/mock_responses": [],

    "frontend/components/ui": ["button.tsx", "input.tsx", "card.tsx", "table.tsx", "dialog.tsx"],
    "frontend/components/layout": ["Header.tsx", "Sidebar.tsx", "Footer.tsx", "Layout.tsx"],
    "frontend/components/auth": ["LoginForm.tsx", "ProtectedRoute.tsx", "AuthProvider.tsx"],
    "frontend/components/pa": ["PAList.tsx", "PADetail.tsx", "CreatePAForm.tsx", "PAStatusBadge.tsx", "PATimeline.tsx"],
    "frontend/components/documents": ["DocumentUpload.tsx", "DocumentViewer.tsx", "DocumentList.tsx", "ExtractionResults.tsx"],
    "frontend/components/analytics": ["Dashboard.tsx", "MetricsCard.tsx", "ApprovalChart.tsx", "TurnaroundChart.tsx"],
    "frontend/components/common": ["LoadingSpinner.tsx", "ErrorBoundary.tsx", "Pagination.tsx", "SearchBar.tsx"],

    "frontend/pages": ["_app.tsx", "_document.tsx", "index.tsx", "login.tsx"],
    "frontend/pages/pa": ["index.tsx", "[id].tsx", "create.tsx"],
    "frontend/pages/analytics": ["index.tsx"],
    "frontend/pages/admin": ["users.tsx", "settings.tsx"],
    "frontend/pages/api": ["health.ts"],

    "frontend/hooks": ["useAuth.ts", "usePA.ts", "useDocuments.ts", "useWebSocket.ts", "useAnalytics.ts"],
    "frontend/lib": ["api.ts", "websocket.ts", "auth.ts", "utils.ts"],
    "frontend/store": ["authStore.ts", "paStore.ts", "uiStore.ts"],
    "frontend/styles": ["globals.css"],
    "frontend/types": ["api.ts", "pa.ts", "document.ts", "user.ts"],

    "frontend/public/images": [],
    "frontend/public/icons": [],
    "frontend/public/fonts": [],
}


# ---------------------------------------------------------
# 2. Get default content for new files
# ---------------------------------------------------------
def placeholder(file):
    ext = Path(file).suffix
    if ext == ".py":
        return "# TODO: Implement\n"
    if ext in [".tsx", ".ts"]:
        return "// TODO: Implement\n"
    if ext == ".css":
        return "/* TODO */\n"
    if ext == ".md":
        return "# TODO\n"
    if ext == ".txt":
        return "TODO\n"
    return ""


# ---------------------------------------------------------
# 3. Main creation logic
# ---------------------------------------------------------
created_dirs = 0
created_files = 0

for dir_path, files in structure.items():
    full_dir = BASE / dir_path

    # Create directory if missing
    if not full_dir.exists():
        full_dir.mkdir(parents=True, exist_ok=True)
        created_dirs += 1
        print(f"📁 Created directory: {dir_path}")

    # Add missing files
    if files:
        for file in files:
            fp = full_dir / file
            if not fp.exists():
                fp.write_text(placeholder(file))
                created_files += 1
                print(f"   📄 Added missing file: {dir_path}/{file}")
    else:
        # If truly empty → add .gitkeep
        if not any(full_dir.iterdir()):
            gitkeep = full_dir / ".gitkeep"
            gitkeep.write_text("")
            created_files += 1
            print(f"   📌 Added .gitkeep in empty dir: {dir_path}")


print("\n--------------------------------------------------")
print("✅ FIX COMPLETE")
print(f"📁 Directories created: {created_dirs}")
print(f"📄 Files added:        {created_files}")
print("--------------------------------------------------")
print("You can now run:\n")
print("   git add .")
print("   git commit -m 'Add missing repo files and directories'")
print("   git push")

