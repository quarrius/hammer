#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os.path
import zipfile

from fs.opener import fsopen, fsopendir
from fs.zipfs import ZipFS

from .lambda_helpers import unwrap_sns_event, unwrap_s3_event, add_logger, \
    event_structure, s3_event
from .util import safe_path_join

@add_logger
def extract_world_archive(event, context, flog):
    src_bucket = event['bucket']['name']
    src_obj_key = event['object']['key']

    flog.info('Source bucket: %s', src_bucket)

    src_dir = os.path.dirname(src_obj_key)
    src_fn = os.path.basename(src_obj_key)
    src_id, _ = os.path.splitext(src_fn)

    flog.info('Source dir : filename : id = %s:%s:%s',
        src_dir, src_fn, src_id)

    s3 = fsopendir('s3://{bucket}/'.format(bucket=src_bucket))
    src_fd = s3.open(src_obj_key, 'rb')

    src_zip = ZipFS(src_fd, 'r')

    for fn in src_zip.walkfiles(wildcard='level.dat'):
        level_dat = fn
        break

    src_zip = src_zip.opendir(os.path.dirname(level_dat))

    for region_fn in src_zip.walkfiles(wildcard='*.mca'):
        dest_fn = safe_path_join('extracted-worlds', src_id, region_fn)
        flog.info('Extracting: %s -> %s', region_fn, dest_fn)
        s3.setcontents(dest_fn, src_zip.getcontents(region_fn))

s3_extract_world_archive = unwrap_s3_event(s3_event(extract_world_archive))


@add_logger
def process_world_data(event, context, flog):
    pass

@add_logger
def process_client_jar(event, context, flog):
    pass

@add_logger
def process_region_file(event, context, flog):
    pass
