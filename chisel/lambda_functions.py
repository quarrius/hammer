#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from .lambda_helpers import unwrap_sns_event, unwrap_s3_event, add_logger, event_structure

@add_logger
def extract_world_archive(event, context, logger):
    pass

@add_logger
def process_world_data(event, context, logger):
    pass

@add_logger
def process_client_jar(event, context, logger):
    pass

@add_logger
def process_region_file(event, context, logger):
    pass
