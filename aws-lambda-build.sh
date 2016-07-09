#!/bin/bash

set -x

BUILD_DIR=~/tmp/quarry-lambda-build
DEST_FILE=~/tmp/chisel-lambda-build.zip

rm -rf "${BUILD_DIR}" "${DEST_FILE}"
mkdir "${BUILD_DIR}"

pip install -r ~/devel/marble/requirements.aws-lambda.txt -t "${BUILD_DIR}"
pip install -r ~/devel/chisel/requirements.aws-lambda.txt -t "${BUILD_DIR}"

tar -xzf ~/tmp/numpy-1.10.4.tar.gz -C "${BUILD_DIR}"
tar -xzf ~/tmp/Pillow-3.1.1.tar.gz -C "${BUILD_DIR}"

cp -r ~/devel/marble/marble/ "${BUILD_DIR}/"
cp -r ~/devel/chisel/chisel/ "${BUILD_DIR}/"

pushd "${BUILD_DIR}"

zip -r ~/tmp/chisel-lambda-build.zip ./*
