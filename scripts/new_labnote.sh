#!/usr/bin/env bash
# Create a new lab notebook entry.
#
# Usage:
#   pixi run note                     -> labnotebook/YYYY-MM-DD.md
#   pixi run note some slug words     -> labnotebook/YYYY-MM-DD__some-slug-words.md
#
# The editable template is the heredoc at the bottom of this file.

set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
dir="$root/labnotebook"
mkdir -p "$dir"

date_iso="$(date +%F)"
timestamp="$(date +%Y-%m-%dT%H:%M:%S%z)"

if [ "$#" -gt 0 ]; then
  slug="$(printf '%s' "$*" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g' \
    | sed -E 's/^-+//; s/-+$//')"
  if [ -z "$slug" ]; then
    echo "error: slug is empty after cleanup" >&2
    exit 1
  fi
  path="$dir/${date_iso}__${slug}.md"
  title="$(printf '%s' "$slug" | tr '-' ' ')"
else
  path="$dir/${date_iso}.md"
  title="$date_iso"
fi

if [ -e "$path" ]; then
  echo "error: ${path##*/} already exists" >&2
  exit 1
fi

{
  printf '%s\n' '---'
  printf '%s\n' "date: $date_iso"
  printf '%s\n' "created: $timestamp"
  printf '%s\n' 'tags: []'
  printf '%s\n' '---'
  printf '%s\n' ''
  printf '%s\n' "# $title"
  printf '%s\n' ''
} > "$path"

echo "${path#"$root"/}"
