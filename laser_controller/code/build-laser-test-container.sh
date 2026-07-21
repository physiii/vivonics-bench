#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(cd "$project_dir/../.." && pwd)"
idf_image="docker.io/espressif/idf@sha256:b9f2d6ea1c19e0c9f7959bdb74a9e3c775642f9d0f3b841937c5fa3363db892b"

mount_root="$workspace_root"
while superproject_root="$(git -C "$mount_root" rev-parse --show-superproject-working-tree 2>/dev/null)" \
    && [[ -n "$superproject_root" ]]; do
  mount_root="$superproject_root"
done
project_relative="$(realpath --relative-to="$mount_root" "$project_dir")"
project_workdir="/workspace/$project_relative"

docker run --rm \
  --volume "$mount_root:/workspace" \
  --workdir "$project_workdir" \
  "$idf_image" \
  bash -lc 'git config --global --add safe.directory "*" && idf.py -B build-laser-test -D SDKCONFIG=sdkconfig.laser-test -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.validation.defaults;sdkconfig.laser-test.defaults" set-target esp32s3 build'
