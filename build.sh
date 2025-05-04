#!/bin/bash
set -e

# === Configurable ===
IMAGE_NAME="jameswrc/cloudflare-tunnel-manager"
ARCHS=("linux/amd64" "linux/arm64")  # Add/remove as needed

# === Derived values ===
DATE_TAG=$(date +%Y.%m.%d)
FULL_TAG="$IMAGE_NAME:$DATE_TAG"

# === Join ARCHS with comma ===
PLATFORMS=$(IFS=, ; echo "${ARCHS[*]}")

# === Show build info ===
echo "🛠  Building image for: $PLATFORMS"
echo "🏷  Tag: $FULL_TAG"

# === Ensure buildx builder exists ===
docker buildx create --name multiarch-builder --use >/dev/null 2>&1 || docker buildx use multiarch-builder
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
docker buildx inspect --bootstrap

# === Build and push ===
docker buildx build \
  --platform "$PLATFORMS" \
  -t "$FULL_TAG" \
  -t "$IMAGE_NAME:latest" \
  --push .

echo "✅ Image pushed: $FULL_TAG and latest"
