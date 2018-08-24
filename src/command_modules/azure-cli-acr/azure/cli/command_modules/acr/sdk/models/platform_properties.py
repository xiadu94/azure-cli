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


class PlatformProperties(Model):
    """The platform properties against which the run has to happen.

    :param os: The operating system type required for the run. Possible values
     include: 'Windows', 'Linux'
    :type os: str or ~azure.mgmt.containerregistry.v2018_09_01.models.OS
    :param architecture: The OS architecture. Possible values include:
     'amd64', 'x86', 'arm'
    :type architecture: str or
     ~azure.mgmt.containerregistry.v2018_09_01.models.Architecture
    :param variant: Variant of the CPU. Possible values include: 'v6', 'v7',
     'v8'
    :type variant: str or
     ~azure.mgmt.containerregistry.v2018_09_01.models.Variant
    """

    _validation = {
        'os': {'required': True},
        'architecture': {'required': True},
    }

    _attribute_map = {
        'os': {'key': 'os', 'type': 'str'},
        'architecture': {'key': 'architecture', 'type': 'str'},
        'variant': {'key': 'variant', 'type': 'str'},
    }

    def __init__(self, os, architecture, variant=None):
        super(PlatformProperties, self).__init__()
        self.os = os
        self.architecture = architecture
        self.variant = variant
