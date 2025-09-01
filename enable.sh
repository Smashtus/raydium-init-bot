#!/usr/bin/env bash
set -euo pipefail

# ===== Config (override via env) =====
: "${REPO:=raydium-init-bot}"
: "${GITHUB_USER:?export GITHUB_USER to your GitHub login}"
: "${DEFAULT_BRANCH:=main}"
: "${PAT_FILE:=.pat}"   # path to the PAT file (gitignored)

# ===== Read PAT safely =====
if [[ ! -f "$PAT_FILE" ]]; then
  echo "PAT file '$PAT_FILE' not found. Create it and chmod 600." >&2
  exit 1
fi

# Ensure the file isn’t world/group readable
if [[ $(stat -c "%a" "$PAT_FILE" 2>/dev/null || stat -f "%Lp" "$PAT_FILE") -gt 600 ]]; then
  echo "PAT file permissions too open. Run: chmod 600 $PAT_FILE" >&2
  exit 1
fi

PAT=$(tr -d '\r\n' < "$PAT_FILE")
if [[ -z "$PAT" ]]; then
  echo "PAT file is empty." >&2
  exit 1
fi

# ===== Basic git setup =====
git init
git add .
git commit -m "init" || true
git branch -M "$DEFAULT_BRANCH"

# Never persist creds in plaintext helpers
git config --global --unset credential.helper || true

# ===== Ensure remote repo exists (idempotent) =====
api="https://api.github.com"
repo_api="$api/repos/${GITHUB_USER}/${REPO}"

# Check if repo exists
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token ${PAT}" "$repo_api")

if [[ "$HTTP_CODE" == "404" ]]; then
  # Create public repo (flip to true for private)
  curl -s -H "Authorization: token ${PAT}" \
       -H "Accept: application/vnd.github+json" \
       -d "{\"name\":\"${REPO}\",\"private\":false}" \
       "$api/user/repos" >/dev/null
elif [[ "$HTTP_CODE" != "200" ]]; then
  echo "GitHub API returned HTTP $HTTP_CODE when checking/creating repo." >&2
  exit 1
fi

# ===== Configure remote =====
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/${GITHUB_USER}/${REPO}.git"

# ===== Push without saving credentials =====
# Inline token in the URL so nothing is saved to ~/.git-credentials
git push -u "https://${GITHUB_USER}:${PAT}@github.com/${GITHUB_USER}/${REPO}.git" "$DEFAULT_BRANCH"
echo "✅ Pushed ${DEFAULT_BRANCH} to https://github.com/${GITHUB_USER}/${REPO}"

