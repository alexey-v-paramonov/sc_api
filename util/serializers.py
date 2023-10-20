# -*- coding: utf-8 -*-
import time
import datetime

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator


class CustomErrorMessagesModelSerializer(serializers.ModelSerializer):

    '''
    Replace validators error messages with error codes
    '''

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # All object validators (non_field_errors)
        for v in self.validators:
            if isinstance(v, UniqueTogetherValidator):
                v.message = u"unique_{0}".format(u"_".join(v.fields))

        # Filed validator error massages
        for k, f in self.fields.items():
            for v in f.validators:
                v.message = v.__class__.__name__.lower().replace(
                    'validator', ''
                )

            f.error_messages.update(
                (k, k) for k, v in f.error_messages.items()
            )


class CustomErrorMessagesSerializer(serializers.Serializer):

    '''
    Replace validators error messages with error codes
    '''

    def __init__(self, *args, **kwargs):

        super(
            CustomErrorMessagesSerializer,
            self
        ).__init__(*args, **kwargs)

        # Failed validator error massages
        for k, f in self.fields.items():
            for v in f.validators:
                v.message = v.__class__.__name__.lower().replace(
                    'validator', ''
                )

            f.error_messages.update(
                (k, k) for k, v in f.error_messages.items()
            )


class UnixEpochDateField(serializers.DateTimeField):
    def to_representation(self, value):
        """ Return epoch time for a datetime object or ``None``"""
        try:
            return int(time.mktime(value.timetuple())) * 1000
        except (AttributeError, TypeError):
            return None

    def to_internal_value(self, value):
        return datetime.datetime.fromtimestamp(int(value))
