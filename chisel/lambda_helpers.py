#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import functools
import logging

from .util import check_type

mlog = logging.getLogger(__name__)

def unwrap_sns_event(lambda_func):
    @functools.wraps(lambda_func)
    def new_lambda_func(event, *pargs, **kwargs):
        try:
            result = [lambda_func(r['Sns']['Message'], *pargs, **kwargs) \
                for r in event['Records']]
            mlog.debug('Unwrapped SNS message with %d records',
                len(event['Records']))
            return result
        except KeyError as err:
            mlog.debug('No SNS message to unwrap: %s', err)
            return lambda_func(event, *pargs, **kwargs)
    return new_lambda_func

def unwrap_s3_event(lambda_func):
    @functools.wraps(lambda_func)
    def new_lambda_func(event, *pargs, **kwargs):
        try:
            result = [lambda_func(r['s3'], *pargs, **kwargs) \
                for r in event['Records']]
            mlog.debug('Unwrapped S3 message with %d records',
                len(event['Records']))
            return result
        except KeyError as err:
            mlog.debug('No SNS message to unwrap: %s', err)
            return lambda_func(event, *pargs, **kwargs)
    return new_lambda_func

def add_logger(lambda_func):
    @functools.wraps(lambda_func)
    def new_lambda_func(event, context):
        flog = logging.getLogger(lambda_func.__name__)
        flog.setLevel(logging.DEBUG)
        return lambda_func(event, context, flog)
    return new_lambda_func

def event_structure(**params):
    def check_event_structure(lambda_func):
        @functools.wraps(lambda_func)
        def event_checker(event, *pargs, **kwargs):
            if check_type(event, params):
                return lambda_func(event, *pargs, **kwargs)
            else:
                raise ValueError('Event structure check failed')
        return event_checker
    return check_event_structure

s3_event = event_structure(
    s3SchemaVersion=basestring,
    configurationId=basestring,
    bucket=dict(
        name=basestring,
        ownerIdentity=dict(
            principalId=basestring,
        ),
        arn=basestring,
    ),
    object=dict(
        key=basestring,
        size=int,
        eTag=basestring,
        versionId=basestring,
        sequencer=basestring,
    ),
)
