import os
from contextlib import contextmanager

import json

from django.core import serializers
from django.conf import settings
if not hasattr(settings, 'SERIALIZATION_MODULES'):
    settings.SERIALIZATION_MODULES = {}
if 'django_snailtracker.serializer' not in settings.SERIALIZATION_MODULES:
    settings.SERIALIZATION_MODULES['django_snailtracker.serializer'] = 'django_snailtracker.serializer'

SNAILTRACKER_TMP_PATH = getattr(settings, 'SNAILTRACKER_TMP_PATH', '/tmp/')


def snailtracker_enabled():
    return getattr(settings, 'SNAILTRACKER_ENABLED', False)


def make_model_snapshot(instance):
    object_as_dict = json.loads(
            serializers.serialize(
                'django_snailtracker.serializer', [instance]))[0]
    if hasattr(instance, 'snailtracker_exclude_fields'):
        for field in instance.snailtracker_exclude_fields:
            try:
                del object_as_dict['fields'][field]
            except KeyError:
                pass
    return object_as_dict


def dict_diff(d1, d2):
    c_list = list()
    for k, v in d1.iteritems():
        if unicode(d2[k]) != unicode(v):
            c_list.append(k)
    return c_list


def dict_diff_with_values(dict1, dict2):
    the_diff = {}
    for k, v in dict1.iteritems():
        if unicode(dict2[k]) != unicode(v):
            the_diff[k] = {'old': dict1[k], 'new': dict2[k]}
    return the_diff


def diff_from_action(action, values=True):
    if action.post_init_snapshot and action.post_save_snapshot:
        if not values:
            return dict_diff(
                    action.init_snapshot_to_python()['fields'],
                    action.save_snapshot_to_python()['fields'])
        else:
            return dict_diff_with_values(
                    action.init_snapshot_to_python()['fields'],
                    action.save_snapshot_to_python()['fields'])


@contextmanager
def mutex_lock(key):
    mutex_key = '%ssnailtracker.%s.lock' % (SNAILTRACKER_TMP_PATH, key)
    if os.path.exists(mutex_key):
        raise SnailtrackerMutexLockedError("'%s' is already locked" % (key,))
    else:
        open(mutex_key, 'a').close()
    try:
        yield True
    finally:
        os.remove(mutex_key)


class SnailtrackerMutexLockedError(Exception):
    pass
