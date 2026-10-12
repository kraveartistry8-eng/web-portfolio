#!/bin/sh
# Bundles the ember engine and Three.js 0.160.0 into one classic script that sets window.EmberEngine.
# It opens over file:// (the brand guide inlines it) and loads as a Shopify asset.
set -e
cd "$(dirname "$0")/../.."
DEPS="${TMPDIR:-/tmp}/ember-three-0.160.0"
[ -f "$DEPS/node_modules/three/package.json" ] || { mkdir -p "$DEPS"; npm i --no-save --prefix "$DEPS" three@0.160.0 >/dev/null; }
NODE_PATH="$DEPS/node_modules" npx --yes esbuild@0.24.0 brand/ember/ember-engine.js --bundle --format=iife \
  --global-name=EmberBundle --minify --legal-comments=none --outfile=brand/ember/ember.bundle.js
printf 'ember.bundle.js: %s bytes, %s bytes gzipped\n' "$(wc -c < brand/ember/ember.bundle.js | tr -d ' ')" "$(gzip -9c brand/ember/ember.bundle.js | wc -c | tr -d ' ')"
