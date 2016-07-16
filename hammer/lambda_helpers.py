#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import functools
import logging
import json
import urllib

import boto3

from .util import check_type

mlog = logging.getLogger(__name__)

def fix_s3_event_object_key(orig_func):
    @functools.wraps(orig_func)
    def actual_func(event, context, *pargs, **kwargs):
        event['object']['key'] = urllib.unquote_plus(event['object']['key'])
        return orig_func(event, context, *pargs, **kwargs)
    return actual_func

def unwrap_multi_event(unwrapper_func=lambda record: record):
    def actual_decorator(orig_func):
        @functools.wraps(orig_func)
        def actual_func(event, context, *pargs, **kwargs):
            try:
                records = event['Records']
            except KeyError as err:
                # probably already unwrapped
                mlog.info('No "Records" key found in event: %s', err)
                return orig_func(event, context, *pargs, **kwargs)
            else:
                mlog.info('Found "Records" key with %02d records', len(records))
                if len(records) > 0:
                    if len(records) > 1:
                        # multiple records, resubmit all but the last
                        lambda_client = boto3.client('lambda')
                        try:
                            func_arn = context.invoked_function_arn
                        except AttributeError:
                            func_arn = 'NO-ARN:{}'.format(orig_func.__name__)
                        for record in records[:-1]:
                            try:
                                payload = unwrapper_func(record)
                            except KeyError as err:
                                mlog.error('Failed to get payload from record ( %r ): %s',
                                    record, err)
                                continue
                            else:
                                response = lambda_client.invoke(
                                    FunctionName=func_arn,
                                    InvocationType='Event', # async
                                    Payload=json.dumps(payload),
                                )
                                mlog.info('Re-sumbitted record to %s: %r',
                                    func_arn, response)
                    # return the last/only record
                    try:
                        payload = unwrapper_func(records[-1])
                    except KeyError as err:
                        mlog.error('Failed to get payload from record ( %r ): %s',
                            record, err)
                        raise ValueError(err)
                    return orig_func(payload, context, *pargs, **kwargs)

                else:
                    # no records, nothing to do
                    raise ValueError('No records found in event')
        return actual_func
    return actual_decorator

unwrap_sns_event = unwrap_multi_event(lambda r: r['Sns']['Message'])
unwrap_s3_event = unwrap_multi_event(lambda r: r['s3'])

def add_logger(orig_func):
    @functools.wraps(orig_func)
    def actual_func(event, context, *pargs, **kwargs):
        logger_name = '{arn}={func_name}'.format(
            arn=context.invoked_function_arn,
            func_name=orig_func.__name__)
        flog = logging.getLogger(logger_name)
        return orig_func(event, context, flog, *pargs, **kwargs)
    return actual_func

def verify_types(**params):
    def actual_decorator(orig_func):
        @functools.wraps(orig_func)
        def actual_func(event, context, *pargs, **kwargs):
            if check_type(event, params):
                return orig_func(event, context, *pargs, **kwargs)
            else:
                raise ValueError('Event structure check failed')
        return actual_func
    return actual_decorator

verify_s3_event_types = verify_types(
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

s3_event = lambda f: \
    unwrap_s3_event(
        verify_s3_event_types(
            fix_s3_event_object_key(f)))
