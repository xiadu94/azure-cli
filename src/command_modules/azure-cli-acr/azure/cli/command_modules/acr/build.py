# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#from azure.cli.core._util import CLIError
#from ._factory import get_acr_service_client
import json
from base64 import b64encode
import requests
from requests.utils import to_native_string
from ._utils import get_registry_by_name
from .credential import acr_credential_show
from azure.cli.core.prompting import prompt
from azure.cli.core._util import CLIError
import azure.cli.core.azlogging as azlogging


logger = azlogging.get_az_logger(__name__)

endpoint = "http://localhost:8080/api/build/definition/"
# endpoint =  "http://acrbuilder.azurewebsites.net/api/build/definition"


def _basic_auth_str(username, password):
    return 'Basic ' + to_native_string(
        b64encode(('%s:%s' % (username, password)).encode('latin1')).strip()
    )


def acr_build_definition_create(build_definition_name, registry_name, resource_group_name):
    '''Manage builds definitions.
    :param str registry_name: The name of container registry
    '''
    logger.warning(
        "Please install https://github.com/integration/azure-container-registry-preview")
    registry, _ = get_registry_by_name(registry_name, resource_group_name)
    cred = acr_credential_show(registry_name)
    username = cred.username  # pylint: disable=no-member
    password = cred.password  # pylint: disable=no-member
    headers = headers = {'Authorization': _basic_auth_str(username, password)}
    buildResourceId = registry.id + "/buildDefinitions/" + build_definition_name  # pylint: disable=no-member
    dockerfile = prompt('Dockerfile path [Dockerfile] : ') or 'Dockerfile'
    branch = prompt('Branch [master] : ') or 'master'
    platform = prompt('Platform (linux/windows) [default=linux] : ') or 'linux'
    image = prompt('Image [' + build_definition_name + '] : ') or build_definition_name
    tag = prompt('Tag [latest] : ') or 'latest'
    repository = prompt('GitHub Respository  : ')
    if not repository:
        raise CLIError('Respository not specified.')

    payload = {
        "location": registry.location,  # pylint: disable=no-member
        "resourceId": buildResourceId,
        "repository": {
            "type": "github",
            "location": repository
        },
        "platform": platform,
        "dockerfiles":
        [
            {
                "branch": branch,
                "path": dockerfile,
                "image": image,
                "tag": tag
            }
        ]
    }
    response = requests.put(
        endpoint,
        headers=headers,
        json=payload
    )
    return json.loads(response.content.decode('utf-8'))


def acr_build_definition_delete(build_definition_name, registry_name, resource_group_name):
    registry, _ = get_registry_by_name(registry_name, resource_group_name)
    cred = acr_credential_show(registry_name)
    username = cred.username  # pylint: disable=no-member
    password = cred.password  # pylint: disable=no-member
    headers = headers = {'Authorization': _basic_auth_str(username, password)}
    buildResourceId = registry.id + "/buildDefinitions/" + build_definition_name  # pylint: disable=no-member
    payload = {
        "resourceId": buildResourceId
    }
    response = requests.delete(
        endpoint,
        headers=headers,
        json=payload
    )
    return json.loads(response.content.decode('utf-8'))


def acr_build_definition_show(build_definition_name, registry_name, resource_group_name):
    registry, _ = get_registry_by_name(registry_name, resource_group_name)
    cred = acr_credential_show(registry_name)
    username = cred.username  # pylint: disable=no-member
    password = cred.password  # pylint: disable=no-member
    headers = headers = {'Authorization': _basic_auth_str(username, password)}
    buildResourceId = registry.id + "/buildDefinitions/" + build_definition_name  # pylint: disable=no-member
    payload = {
        "resourceId": buildResourceId
    }
    response = requests.get(
        endpoint,
        headers=headers,
        json=payload
    )

    # content = response.content
    # print(type(content))
    return json.loads(response.content.decode('utf-8'))


def acr_build_trigger(build_definition_name, registry_name, resource_group_name):
    '''Triggers a build for a build definition.
    :param str registry_name: The name of container registry
    '''

    registry, _ = get_registry_by_name(registry_name, resource_group_name)
    cred = acr_credential_show(registry_name)
    username = cred.username  # pylint: disable=no-member
    password = cred.password  # pylint: disable=no-member
    headers = headers = {'Authorization': _basic_auth_str(username, password)}
    buildResourceId = registry.id + "/buildDefinitions/" + build_definition_name  # pylint: disable=no-member
    payload = {
        "resourceId": buildResourceId
    }

    response = requests.post(
        endpoint + "trigger",
        headers=headers,
        json=payload
    )
    return json.loads(response.content.decode('utf-8'))
