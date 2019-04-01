# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

from knack.util import CLIError
from knack.log import get_logger

from ._utils import user_confirmation
from ._docker_utils import request_data_from_registry, get_access_credentials, RegistryException

logger = get_logger(__name__)


UNTAG_NOT_SUPPORTED = 'Untag is only supported for managed registries.'
DELETE_NOT_SUPPORTED = 'Delete is only supported for managed registries.'
SHOW_MANIFESTS_NOT_SUPPORTED = 'Show manifests is only supported for managed registries.'
ATTRIBUTES_NOT_SUPPORTED = 'Attributes are only supported for managed registries.'
METADATA_NOT_SUPPORTED = 'Metadata is only supported for managed registries.'

ORDERBY_PARAMS = {
    'time_asc': 'timeasc',
    'time_desc': 'timedesc'
}
DEFAULT_PAGINATION = 100
MANIFEST_V2_HEADER = {
    'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
}


def _get_repository_path(repository=None):
    """Return the path for a repository, or list of repositories if repository is empty.
    """
    if repository:
        return '/acr/v1/{}'.format(repository)
    return '/acr/v1/_catalog'


def _get_tag_path(repository, tag=None):
    """Return the path for a tag, or list of tags if tag is empty.
    """
    if tag:
        return '/acr/v1/{}/_tags/{}'.format(repository, tag)
    return '/acr/v1/{}/_tags'.format(repository)


def _get_manifest_path(repository, manifest=None):
    """Return the path for a manifest, or list of manifests if manifest is empty.
    """
    if manifest:
        return '/acr/v1/{}/_manifests/{}'.format(repository, manifest)
    return '/acr/v1/{}/_manifests'.format(repository)


def _get_manifest_digest(login_server, repository, tag, username, password):
    response = request_data_from_registry(
        http_method='get',
        login_server=login_server,
        path=_get_tag_path(repository, tag),
        username=username,
        password=password,
        result_index='tag')[0]

    if 'digest' in response and response['digest']:
        return response['digest']

    raise CLIError("Could not get the manifest digest for image '{}:{}'.".format(repository, tag))


def _obtain_data_from_registry(login_server,
                               path,
                               username,
                               password,
                               result_index,
                               top=None,
                               orderby=None):
    result_list = []
    execute_next_http_call = True

    params = {
        'n': DEFAULT_PAGINATION,
        'orderby': ORDERBY_PARAMS[orderby] if orderby else None
    }

    while execute_next_http_call:
        execute_next_http_call = False

        # Override the default page size if top is provided
        if top is not None:
            params['n'] = DEFAULT_PAGINATION if top > DEFAULT_PAGINATION else top
            top -= params['n']

        result, next_link = request_data_from_registry(
            http_method='get',
            login_server=login_server,
            path=path,
            username=username,
            password=password,
            result_index=result_index,
            params=params)

        if result:
            result_list += result

        if top is not None and top <= 0:
            break

        if next_link:
            # The registry is telling us there's more items in the list,
            # and another call is needed. The link header looks something
            # like `Link: </v2/_catalog?last=hello-world&n=1>; rel="next"`
            # we should follow the next path indicated in the link header
            next_link_path = next_link[(next_link.index('<') + 1):next_link.index('>')]
            tokens = next_link_path.split('?', 2)
            params = {y[0]: unquote(y[1]) for y in (x.split('=', 2) for x in tokens[1].split('&'))}
            execute_next_http_call = True

    return result_list


def acr_repository_list(cmd,
                        registry_name,
                        top=None,
                        resource_group_name=None,  # pylint: disable=unused-argument
                        tenant_suffix=None,
                        username=None,
                        password=None):
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)

    return _obtain_data_from_registry(
        login_server=login_server,
        path='/v2/_catalog',
        username=username,
        password=password,
        result_index='repositories',
        top=top)


def acr_repository_show_tags(cmd,
                             registry_name,
                             repository,
                             top=None,
                             orderby=None,
                             resource_group_name=None,  # pylint: disable=unused-argument
                             tenant_suffix=None,
                             username=None,
                             password=None,
                             detail=False):
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission='pull')

    try:
        raw_result = _obtain_data_from_registry(
            login_server=login_server,
            path=_get_tag_path(repository),
            username=username,
            password=password,
            result_index='tags',
            top=top,
            orderby=orderby)
    except RegistryException as e:
        # Check for Classic registry
        if e.status_code == 405:
            if detail:
                logger.warning("The specified --detail is ignored as it is only supported for managed registries.")
            if top:
                logger.warning("The specified --top is ignored as it is only supported for managed registries.")
            if orderby:
                logger.warning("The specified --orderby is ignored as it is only supported for managed registries.")
            return _obtain_data_from_registry(
                login_server=login_server,
                path='/v2/{}/tags/list'.format(repository),
                username=username,
                password=password,
                result_index='tags')
        raise

    # For backward compatibility, convert the results to the old schema
    if not detail:
        return [item['name'] for item in raw_result]

    return raw_result


def acr_repository_show_manifests(cmd,
                                  registry_name,
                                  repository,
                                  top=None,
                                  orderby=None,
                                  resource_group_name=None,  # pylint: disable=unused-argument
                                  tenant_suffix=None,
                                  username=None,
                                  password=None,
                                  detail=False):
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission='pull')

    try:
        raw_result = _obtain_data_from_registry(
            login_server=login_server,
            path=_get_manifest_path(repository),
            username=username,
            password=password,
            result_index='manifests',
            top=top,
            orderby=orderby)
    except RegistryException as e:
        # Check for Classic registry
        if e.status_code == 405:
            raise CLIError(SHOW_MANIFESTS_NOT_SUPPORTED)
        raise

    # For backward compatibility, convert the results to the old schema
    if not detail:
        return [{
            'digest': item['digest'] if 'digest' in item else '',
            'tags': item['tags'] if 'tags' in item else [],
            'timestamp': item['lastUpdateTime'] if 'lastUpdateTime' in item else ''
        } for item in raw_result]

    return raw_result


def acr_repository_show(cmd,
                        registry_name,
                        repository=None,
                        image=None,
                        resource_group_name=None,  # pylint: disable=unused-argument
                        tenant_suffix=None,
                        username=None,
                        password=None):
    return _acr_repository_attributes_helper(
        cmd=cmd,
        registry_name=registry_name,
        http_method='get',
        json_payload=None,
        permission='pull',
        repository=repository,
        image=image,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)


def acr_repository_update(cmd,
                          registry_name,
                          repository=None,
                          image=None,
                          resource_group_name=None,  # pylint: disable=unused-argument
                          tenant_suffix=None,
                          username=None,
                          password=None,
                          delete_enabled=None,
                          list_enabled=None,
                          read_enabled=None,
                          write_enabled=None):
    json_payload = {}

    if delete_enabled is not None:
        json_payload.update({
            'deleteEnabled': delete_enabled
        })
    if list_enabled is not None:
        json_payload.update({
            'listEnabled': list_enabled
        })
    if read_enabled is not None:
        json_payload.update({
            'readEnabled': read_enabled
        })
    if write_enabled is not None:
        json_payload.update({
            'writeEnabled': write_enabled
        })

    return _acr_repository_attributes_helper(
        cmd=cmd,
        registry_name=registry_name,
        http_method='patch' if json_payload else 'get',
        json_payload=json_payload,
        permission='*',
        repository=repository,
        image=image,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)


def _acr_repository_attributes_helper(cmd,
                                      registry_name,
                                      http_method,
                                      json_payload,
                                      permission,
                                      repository=None,
                                      image=None,
                                      tenant_suffix=None,
                                      username=None,
                                      password=None):
    _validate_parameters(repository, image)

    if image:
        # If --image is specified, repository must be empty.
        repository, tag, manifest = _parse_image_name(image, allow_digest=True)
    else:
        # This is a request on repository
        tag, manifest = None, None

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission=permission)

    if tag:
        path = _get_tag_path(repository, tag)
        result_index = 'tag'
    elif manifest:
        path = _get_manifest_path(repository, manifest)
        result_index = 'manifest'
    else:
        path = _get_repository_path(repository)
        result_index = None

    # Non-GET request doesn't return the entity so there is always a GET reqeust
    if http_method != 'get':
        try:
            request_data_from_registry(
                http_method=http_method,
                login_server=login_server,
                path=path,
                username=username,
                password=password,
                result_index=result_index,
                json_payload=json_payload)
        except RegistryException as e:
            # Check for Classic registry
            if e.status_code == 405:
                raise CLIError(ATTRIBUTES_NOT_SUPPORTED)
            raise

    try:
        return request_data_from_registry(
            http_method='get',
            login_server=login_server,
            path=path,
            username=username,
            password=password,
            result_index=result_index)[0]
    except RegistryException as e:
        # Check for Classic registry
        if e.status_code == 405:
            raise CLIError(ATTRIBUTES_NOT_SUPPORTED)
        raise


def acr_repository_untag(cmd,
                         registry_name,
                         image,
                         resource_group_name=None,  # pylint: disable=unused-argument
                         tenant_suffix=None,
                         username=None,
                         password=None):
    repository, tag, _ = _parse_image_name(image)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission='*')

    try:
        return request_data_from_registry(
            http_method='delete',
            login_server=login_server,
            path=_get_tag_path(repository, tag),
            username=username,
            password=password)[0]
    except RegistryException as e:
        # Check for Classic registry
        if e.status_code == 405:
            raise CLIError(UNTAG_NOT_SUPPORTED)
        raise


def acr_repository_delete(cmd,
                          registry_name,
                          repository=None,
                          image=None,
                          resource_group_name=None,  # pylint: disable=unused-argument
                          tenant_suffix=None,
                          username=None,
                          password=None,
                          yes=False):
    _validate_parameters(repository, image)

    if image:
        # If --image is specified, repository must be empty.
        repository, tag, manifest = _parse_image_name(image, allow_digest=True)
    else:
        # This is a request on repository
        tag, manifest = None, None

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password,
        repository=repository,
        permission='*')

    if tag or manifest:
        manifest = _delete_manifest_confirmation(
            login_server=login_server,
            username=username,
            password=password,
            repository=repository,
            tag=tag,
            manifest=manifest,
            yes=yes)
        path = '/v2/{}/manifests/{}'.format(repository, manifest)
    else:
        user_confirmation("Are you sure you want to delete the repository '{}' "
                          "and all images under it?".format(repository), yes)
        path = _get_repository_path(repository)

    try:
        return request_data_from_registry(
            http_method='delete',
            login_server=login_server,
            path=path,
            username=username,
            password=password)[0]
    except RegistryException as e:
        # Check for Classic registry
        if e.status_code == 405:
            raise CLIError(DELETE_NOT_SUPPORTED)
        raise


def _validate_parameters(repository, image):
    if bool(repository) == bool(image):
        raise CLIError('Usage error: --image IMAGE | --repository REPOSITORY')


def _parse_image_name(image, allow_digest=False):
    if allow_digest and '@' in image:
        # This is probably an image name by manifest digest
        tokens = image.split('@')
        if len(tokens) == 2:
            return tokens[0], None, tokens[1]

    if ':' in image:
        # This is probably an image name by tag
        tokens = image.split(':')
        if len(tokens) == 2:
            return tokens[0], tokens[1], None
    else:
        # This is probably an image with implicit latest tag
        return image, 'latest', None

    if allow_digest:
        raise CLIError("The name of the image to delete may include a tag in the"
                       " format 'name:tag' or digest in the format 'name@digest'.")
    else:
        raise CLIError("The name of the image may include a tag in the format 'name:tag'.")


def _delete_manifest_confirmation(login_server,
                                  username,
                                  password,
                                  repository,
                                  tag,
                                  manifest,
                                  yes):
    # Always query manifest if it is empty
    try:
        manifest = manifest or _get_manifest_digest(
            login_server=login_server,
            repository=repository,
            tag=tag,
            username=username,
            password=password)
    except RegistryException as e:
        # Check for Classic registry
        if e.status_code == 405:
            raise CLIError(DELETE_NOT_SUPPORTED)
        raise

    if yes:
        return manifest

    try:
        tags = _obtain_data_from_registry(
            login_server=login_server,
            path=_get_tag_path(repository),
            username=username,
            password=password,
            result_index='tags'
        )
    except RegistryException as e:
        # Check for Classic registry
        if e.status_code == 405:
            raise CLIError(DELETE_NOT_SUPPORTED)
        raise

    filter_by_manifest = [x['name'] for x in tags if manifest == x['digest']]
    message = "This operation will delete the manifest '{}'".format(manifest)
    if filter_by_manifest:
        images = ", ".join(["'{}:{}'".format(repository, str(x)) for x in filter_by_manifest])
        message += " and all the following images: {}".format(images)
    user_confirmation("{}.\nAre you sure you want to continue?".format(message))

    return manifest


def get_image_digest(cmd, registry_name, image):
    repository, tag, manifest = _parse_image_name(image, allow_digest=True)

    if manifest:
        return repository, tag, manifest

    # If we don't have manifest yet, try to get it from tag.
    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        repository=repository,
        permission='pull')

    manifest = _get_manifest_digest(
        login_server=login_server,
        repository=repository,
        tag=tag,
        username=username,
        password=password)

    return repository, tag, manifest


def _get_manifest(login_server, repository, tag, username, password, retry_times=3, retry_interval=5):
    import requests, time
    from azure.cli.core.util import should_disable_connection_verify
    from ._docker_utils import get_authorization_header, log_registry_response, parse_error_message
    url = 'https://{}/v2/{}/manifests/{}'.format(login_server, repository, tag)
    headers = get_authorization_header(username, password)
    headers.update(MANIFEST_V2_HEADER)
    for i in range(0, retry_times):
        errorMessage = None
        try:
            response = requests.get(
                url=url,
                headers=headers,
                verify=(not should_disable_connection_verify())
            )
            log_registry_response(response)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise CLIError(parse_error_message('Authentication required.', response))
            elif response.status_code == 404:
                raise CLIError(parse_error_message('The manifest does not exist.', response))
            else:
                raise Exception(parse_error_message('Could not get manifest digest.', response))
        except CLIError:
            raise
        except Exception as e:  # pylint: disable=broad-except
            errorMessage = str(e)
            logger.debug('Retrying %s with exception %s', i + 1, errorMessage)
            time.sleep(retry_interval)
    raise CLIError(errorMessage)


def acr_teleport(cmd,
                 registry_name,
                 image,
                 username=None,
                 password=None):
    repository, tag, manifest = _parse_image_name(image, allow_digest=True)

    login_server, username, password = get_access_credentials(
        cmd=cmd,
        registry_name=registry_name,
        username=username,
        password=password,
        repository=repository,
        permission='pull')

    manifest_content = _get_manifest(
        login_server=login_server,
        repository=repository,
        tag=manifest or tag,
        username=username,
        password=password)

    mount_command = None
    base_mnt = '/mnt/{}'.format(login_server)

    for layer in manifest_content['layers']:
        digest = layer['digest']
        mount = request_data_from_registry(
            http_method='get',
            login_server=login_server,
            path='/acr/v1/{}/_mounts/{}'.format(repository, digest),
            username=username,
            password=password)[0]
        layer['mount'] = mount
        source = mount['source']
        u = mount['credential']['username']
        p = mount['credential']['password']
        f = mount['file']
        if not mount_command:
            mount_command = 'sudo mount -t cifs {} {} -o vers=3.0,username={},password={},dir_mode=0777,file_mode=0777,sec=ntlmssp'.format(
                source, base_mnt, u, p
            )
            _mkdir(base_mnt)
            logger.warning(mount_command)
        source_file = '{}/{}'.format(source, f)
        target_folder = '/mnt/{}'.format(digest.split(':')[1])
        _mkdir(target_folder)
        _mount(source_file, target_folder)

    return manifest_content


def _mkdir(path):
    logger.warning('mkdir -p {}'.format(path))


def _mount(source, target):
    logger.warning('mount {} {}'.format(source, target))
