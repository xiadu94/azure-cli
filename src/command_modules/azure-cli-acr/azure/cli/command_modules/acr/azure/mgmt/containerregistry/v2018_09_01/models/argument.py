# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class Argument(Model):
    """The properties of a run argument.

    :param name: The name of the argument.
    :type name: str
    :param value: The value of the argument.
    :type value: str
    :param is_secret: Flag to indicate whether the argument represents a
     secret and want to be removed from build logs. Default value: False .
    :type is_secret: bool
    """

    _validation = {
        'name': {'required': True},
        'value': {'required': True},
    }

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'},
        'is_secret': {'key': 'isSecret', 'type': 'bool'},
    }

    def __init__(self, name, value, is_secret=False):
        super(Argument, self).__init__()
        self.name = name
        self.value = value
        self.is_secret = is_secret