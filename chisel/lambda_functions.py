#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os.path
import zipfile

import boto3
from fs.opener import fsopen, fsopendir
from fs.zipfs import ZipFS
from nbt.region import RegionFile
from PIL import Image
import numpy

from .lambda_helpers import unwrap_s3_event, add_logger, fix_s3_event_object_key
from .util import safe_path_join

@unwrap_s3_event
@fix_s3_event_object_key
@add_logger
def extract_world_archive(event, context, flog):
    flog.info('Starting world archive extraction...')

    src_bucket = event['bucket']['name']
    src_obj_key = event['object']['key']

    flog.info('Event object: %s::%s', src_bucket, src_obj_key)

    src_dir = os.path.dirname(src_obj_key)
    src_fn = os.path.basename(src_obj_key)
    src_id, _ = os.path.splitext(src_fn)

    flog.info('Source dir : filename : world_id = %s:%s:%s',
        src_dir, src_fn, src_id)

    s3 = fsopendir('s3://{bucket}/'.format(bucket=src_bucket))
    src_fd = s3.open(src_obj_key, 'rb')

    src_zip = ZipFS(src_fd, 'r')

    flog.info('Searching for level.dat ...')

    for fn in src_zip.walkfiles(wildcard='level.dat'):
        level_dat = fn
        break

    flog.info('Found level.dat at: %s', level_dat)

    src_zip = src_zip.opendir(os.path.dirname(level_dat))

    for region_fn in src_zip.walkfiles(wildcard='*.mca'):
        dest_fn = safe_path_join('extracted-worlds', src_id, region_fn)
        flog.info('Extracting: %s -> %s', region_fn, dest_fn)
        s3.setcontents(dest_fn, src_zip.getcontents(region_fn))

@unwrap_s3_event
@fix_s3_event_object_key
@add_logger
def process_level_dat(event, context, flog):
    # parse nbt and stick values into db (dynamodb, rds?)
    pass

@unwrap_s3_event
@fix_s3_event_object_key
@add_logger
def process_client_jar_textures(event, context, flog):
    # turn vanilla textures or texture pack into a format suitable for the
    # rendering process
    pass

@unwrap_s3_event
@fix_s3_event_object_key
@add_logger
def process_region_file(event, context, flog):
    # for each chunk in region file
    #   if chunk.mtime > db_chunk.mtime
    #       render chunk_img
    #       update db_chunk
    #       update db_chunk.img
    pass

@unwrap_s3_event
@fix_s3_event_object_key
@add_logger
def render_region_heightmap(event, context, flog):
    src_bucket = event['bucket']['name']
    src_obj_key = event['object']['key']

    dest_vfs = fsopendir('s3://{bucket}/'.format(bucket='quarry-output'))
    dest_image_fn = os.path.join('heightmaps', *src_obj_key.split('/')[1:]) + '.png'
    src_region = fsopen('s3://{bucket}/{key}'.format(
        bucket=src_bucket, key=src_obj_key), 'rb')

    img = Image.new('L', (512, 512))

    for chunk in region.get_metadata():
        chunk_data = region.get_nbt()
        heightmap_data = numpy.array(chunk_data['Level']['HeightMap'],
            dtype=numpy.uint8).reshape((16, 16))
        img.paste(Image.fromarray(heightmap_data),
            box=(chunk.x * 16, chunk.z * 16))

    with dest_vfs.open(dest_image_fn, 'wb') as image_handle:
        img.save(image_handle, format='PNG')
