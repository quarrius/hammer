#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os.path
import zipfile
import logging

import boto3
from fs.opener import fsopen, fsopendir
from fs.zipfs import ZipFS
# from nbt.region import RegionFile
# from PIL import Image
# import numpy
# import marble.world

from .lambda_helpers import unwrap_s3_event, add_logger, fix_s3_event_object_key
from .util import safe_path_join
from .toybox import CFG_INIT, DB_INIT, User, World

logging.basicConfig(level=logging.DEBUG)

CFG = CFG_INIT()

DB_OBJ = DB_INIT(CFG.get('config:toybox:DATABASE_URI'))
DB_OBJ.connect()

@unwrap_s3_event
@fix_s3_event_object_key
@add_logger
def extract_world_archive(event, context, flog):
    flog.info('Starting world archive extraction...')

    bucket_name = event['bucket']['name']
    object_key = event['object']['key']

    flog.debug('Event object: %s::%s', bucket_name, object_key)

    # TODO: error handling
    api_key = os.path.splitext(os.path.split(object_key)[1])[0]
    world = World.select().where(World.api_key == api_key).get()
    user = world.user

    flog.info('Extracting for user::world: %s:%s', user.guid, world.guid)

    object_fd = fsopen('s3://{bucket}/{key}'.format(
        bucket=bucket_name,
        key=object_key,
    ))
    archive_fs = ZipFS(object_fd, 'r')
    dest_fs = fsopendir('s3://{bucket}/worlds/{user_guid}/{world_guid}/'.format(
        bucket=bucket_name,
        user_guid=user.guid,
        world_guid=world.guid,
    ))

    for fn in archive_fs.walkfiles(wildcard='level.dat'):
        level_dat_fn = fn
        break
    flog.debug('Found level.dat at: %s', level_dat_fn)

    archive_fs = archive_fs.opendir(os.path.dirname(level_dat_fn))

    flog.info('Extracting level.dat')
    # TODO: make sure these paths are actually safe
    dest_fs.setcontents('level.dat', archive_fs.getcontents('level.dat'))
    for region_fn in archive_fs.walkfiles(wildcard='*.mca'):
        flog.info('Extracting file: %s', region_fn)
        dest_fs.setcontents(region_fn, archive_fs.getcontents(region_fn))

    flog.info('Finished world archive extraction')

@unwrap_s3_event
@fix_s3_event_object_key
@add_logger
def process_level_dat(event, context, flog):
    world_base_dir = os.path.dirname(event['object']['key'])
    vfs = fsopendir('s3://{bucket}/{key}'.format(
        bucket=event['bucket']['name'],
        key=world_base_dir,
    ))

    world = marble.world.MinecraftWorld.load(vfs)

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
    src_region = RegionFile(fileobj=fsopen('s3://{bucket}/{key}'.format(
        bucket=src_bucket, key=src_obj_key), 'rb'))

    img = Image.new('L', (512, 512))

    for chunk in src_region.get_metadata():
        chunk_data = src_region.get_nbt(chunk.x, chunk.z)
        heightmap_data = numpy.array(chunk_data['Level']['HeightMap'],
            dtype=numpy.uint8).reshape((16, 16))
        img.paste(Image.fromarray(heightmap_data),
            box=(chunk.x * 16, chunk.z * 16))

    with dest_vfs.open(dest_image_fn, 'wb') as image_handle:
        img.save(image_handle, format='PNG')
