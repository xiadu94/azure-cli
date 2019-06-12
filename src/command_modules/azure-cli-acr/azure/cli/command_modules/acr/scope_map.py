# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError
from ._utils import get_resource_group_name_by_registry_name


def _parse_actions_from_repositories(allow_or_remove_repository):
    actions = []

    allow_or_remove_repository.sort()
    for rule in allow_or_remove_repository:
        splitted = rule.split(';', 1)
        if len(splitted) != 2:
            return False, rule
        repository, repository_actions = splitted[0], splitted[1].split(',')
        for action in repository_actions:
            actions.append("repositories/" + repository + "/" + action)

    return True, actions


def acr_scope_map_create(cmd,
                         client,
                         registry_name,
                         scope_map_name,
                         add_repository,
                         resource_group_name=None,
                         description=None):

    validated, actions = _parse_actions_from_repositories(add_repository)
    if not validated:
        raise CLIError("Rule {} has invalid syntax.".format(actions))

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.create(
        resource_group_name,
        registry_name,
        scope_map_name,
        actions,
        description
    )


def acr_scope_map_delete(cmd,
                         client,
                         registry_name,
                         scope_map_name,
                         yes=None,
                         resource_group_name=None):

    if not yes:
        from knack.prompting import prompt_y_n
        confirmation = prompt_y_n("Deleting the scope map '{}' will remove its permissions with associated tokens. "
                                  "Proceed?".format(scope_map_name))

        if not confirmation:
            return

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.delete(resource_group_name, registry_name, scope_map_name)


def acr_scope_map_update(cmd,
                         client,
                         registry_name,
                         scope_map_name,
                         add_repository=None,
                         remove_repository=None,
                         reset_map=None,
                         resource_group_name=None,
                         description=None):

    if not (add_repository or remove_repository or reset_map or description):
        raise CLIError("At least one of the following parameters must be provided: " +
                       "--add, --remove, --reset, --description.")

    if reset_map:
        current_actions = []
    else:
        current_scope_map = acr_scope_map_show(cmd, client, registry_name, scope_map_name, resource_group_name)
        current_actions = current_scope_map.actions

    if remove_repository:
        validated, removed_actions = _parse_actions_from_repositories(remove_repository)
        if not validated:
            raise CLIError("Rule {} has invalid syntax.".format(removed_actions))
        # We have to treat actions case-insensitively but list them case-sensitively
        lower_current_actions = set([action.lower() for action in current_actions])
        lower_removed_actions = set([action.lower() for action in removed_actions])
        current_actions = [action for action in current_actions
                           if action.lower() in lower_current_actions - lower_removed_actions]

    if add_repository:
        validated, added_actions = _parse_actions_from_repositories(add_repository)
        if not validated:
            raise CLIError("Rule {} has invalid syntax.".format(added_actions))
        # We have to avoid duplicates and give preference to user input casing
        lower_action_to_action = {}
        for action in current_actions:
            lower_action_to_action[action.lower()] = action
        for action in added_actions:
            lower_action_to_action[action.lower()] = action
        current_actions = [lower_action_to_action[action] for action in lower_action_to_action]

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.update(
        resource_group_name,
        registry_name,
        scope_map_name,
        description,
        current_actions
    )


def acr_scope_map_show(cmd,
                       client,
                       registry_name,
                       scope_map_name,
                       resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.get(
        resource_group_name,
        registry_name,
        scope_map_name
    )


def acr_scope_map_list(cmd,
                       client,
                       registry_name,
                       resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)

    return client.list(
        resource_group_name,
        registry_name
    )
