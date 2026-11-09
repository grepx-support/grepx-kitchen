#!/usr/bin/env bash
# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

# Prepare the Flutter app (first time: generates the android/ and ios/ shells, then fetches packages).
#   ./setup.sh
#   flutter run --dart-define=API_BASE=http://10.0.2.2:8861                    (Android emulator, local server)
#   flutter build apk --release --dart-define=API_BASE=https://kitchen.example.com
set -euo pipefail
cd "$(dirname "$0")"

say() { printf '%s %-5s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "mobile" "$2"; }
die() { say ERROR "$1"; exit 1; }

command -v flutter >/dev/null 2>&1 || die "Flutter is not installed - see https://docs.flutter.dev/get-started/install"
if [ ! -d android ]; then
  say INFO "generating the android/ and ios/ shells (first time)"
  flutter create --org sg.grepx --project-name kitchen_mobile --platforms=android,ios . >/dev/null || die "flutter create failed"
fi
say INFO "fetching packages"
flutter pub get >/dev/null || die "flutter pub get failed"
say OK "mobile ready - run: flutter run --dart-define=API_BASE=<your site, e.g. https://kitchen.example.com>"
