#!/bin/sh
# Bundles the ember satin engine and Three.js 0.160.0 into one classic script that sets window.EmberSatin.
# It opens over file:// (the brand guide inlines it), as brand/ember/build.sh does for the v23 engine.
set -e
cd "$(dirname "$0")/../../.."
DEPS="${TMPDIR:-/tmp}/ember-three-0.160.0"
[ -f "$DEPS/node_modules/three/package.json" ] || { mkdir -p "$DEPS"; npm i --no-save --prefix "$DEPS" three@0.160.0 >/dev/null; }
NODE_PATH="$DEPS/node_modules" npx --yes esbuild@0.24.0 brand/ember/satin/engine.js --bundle --format=iife \
  --global-name=EmberSatinBundle --minify --legal-comments=none --outfile=brand/ember/satin/ember-satin.bundle.js
printf 'ember-satin.bundle.js: %s bytes, %s bytes gzipped\n' "$(wc -c < brand/ember/satin/ember-satin.bundle.js | tr -d ' ')" "$(gzip -9c brand/ember/satin/ember-satin.bundle.js | wc -c | tr -d ' ')"
