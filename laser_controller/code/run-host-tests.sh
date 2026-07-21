#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
test_binary="$(mktemp /tmp/vivonics-laser-controller-tests.XXXXXX)"
trap 'rm -f "$test_binary"' EXIT

cc \
  -std=c11 \
  -Wall \
  -Wextra \
  -Werror \
  -Wpedantic \
  -fsanitize=address,undefined \
  -I"$project_dir/main" \
  "$project_dir/main/ad7606_decode.c" \
  "$project_dir/main/laser_safety.c" \
  "$project_dir/main/laser_test_protocol.c" \
  "$project_dir/tests/test_ad7606_and_safety.c" \
  -lm \
  -o "$test_binary"

ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 "$test_binary"
