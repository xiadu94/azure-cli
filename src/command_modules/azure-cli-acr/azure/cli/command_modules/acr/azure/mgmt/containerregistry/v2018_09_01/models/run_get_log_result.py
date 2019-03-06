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


class RunGetLogResult(Model):
    """The result of get log link operation.

    :param log_link: The link to logs for a run on a azure container registry.
    :type log_link: str
    """

    _attribute_map = {
        'log_link': {'key': 'logLink', 'type': 'str'},
    }

    def __init__(self, log_link=None):
        super(RunGetLogResult, self).__init__()
        self.log_link = log_link