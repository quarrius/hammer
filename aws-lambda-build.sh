#!/bin/bash

set -x

BUILD_VERSION="${1:-0.0.0-devel}"

MARBLE_DIR=~/devel/marble
CHISEL_DIR=~/devel/chisel

NUMPY_URL='https://github.com/Miserlou/lambda-packages/raw/master/lambda_packages/numpy/numpy-1.10.4.tar.gz'
PILLOW_URL='https://github.com/Miserlou/lambda-packages/raw/master/lambda_packages/Pillow/Pillow-3.1.1.tar.gz'

BUILD_DIR="${CHISEL_DIR}/build/chisel-lambdabuild-${BUILD_VERSION}"
DEST_FILE="${CHISEL_DIR}/build/chisel-lambda-${BUILD_VERSION}.zip"
DOWNLOAD_DIR="${CHISEL_DIR}/build"

NUMPY_FILENAME="${DOWNLOAD_DIR}/$(basename ${NUMPY_URL})"
PILLOW_FILENAME="${DOWNLOAD_DIR}/$(basename ${PILLOW_URL})"

mkdir -p "${BUILD_DIR}"

pip install -r "${MARBLE_DIR}/requirements.aws-lambda.txt" -t "${BUILD_DIR}"
pip install -r "${CHISEL_DIR}/requirements.aws-lambda.txt" -t "${BUILD_DIR}"

if [ ! -f "$NUMPY_FILENAME" ]; then
    wget -O "$NUMPY_FILENAME" "$NUMPY_URL"
fi
tar -xzf "$NUMPY_FILENAME" -C "$BUILD_DIR"

if [ ! -f "$PILLOW_FILENAME" ]; then
    wget -O "$PILLOW_FILENAME" "$PILLOW_URL"
fi
tar -xzf "$PILLOW_FILENAME" -C "$BUILD_DIR"

cp -a "${MARBLE_DIR}/marble/" "${BUILD_DIR}/"
cp -a "${CHISEL_DIR}/chisel/" "${BUILD_DIR}/"

pushd "${BUILD_DIR}"
rm -f "${DEST_FILE}"
zip -r "${DEST_FILE}" ./*
