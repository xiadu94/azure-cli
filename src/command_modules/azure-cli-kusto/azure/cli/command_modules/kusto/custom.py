# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.log import get_logger
from azure.mgmt.resource import ResourceManagementClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.kusto._validators import round_hot_cache_to_days, round_soft_delete_to_days
from azure.cli.core.util import sdk_no_wait

logger = get_logger(__name__)


def cluster_create(cmd,
                   resource_group_name,
                   cluster_name,
                   sku,
                   location=None,
                   capacity=None,
                   custom_headers=None,
                   raw=False,
                   polling=True,
                   no_wait=False,
                   **kwargs):

    from azure.mgmt.kusto.models import Cluster, AzureSku
    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    if location is None:
        location = _get_resource_group_location(cmd.cli_ctx, resource_group_name)

    _client = cf_cluster(cmd.cli_ctx, None)

    _cluster = Cluster(location=location, sku=AzureSku(name=sku, capacity=capacity))

    return sdk_no_wait(no_wait,
                       _client.create_or_update,
                       resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       parameters=_cluster,
                       custom_headers=custom_headers,
                       raw=raw,
                       polling=polling,
                       operation_config=kwargs)


def _cluster_get(cmd,
                 resource_group_name,
                 cluster_name,
                 custom_headers=None,
                 raw=False,
                 **kwargs):

    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    _client = cf_cluster(cmd.cli_ctx, None)

    return _client.get(resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       custom_headers=custom_headers,
                       raw=raw,
                       operation_config=kwargs)


def cluster_start(cmd,
                  resource_group_name,
                  cluster_name,
                  custom_headers=None,
                  raw=False,
                  polling=True,
                  **kwargs):

    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    _client = cf_cluster(cmd.cli_ctx, None)

    return _client.start(resource_group_name=resource_group_name,
                         cluster_name=cluster_name,
                         custom_headers=custom_headers,
                         raw=raw,
                         polling=polling,
                         operation_config=kwargs)


def cluster_stop(cmd,
                 resource_group_name,
                 cluster_name,
                 custom_headers=None,
                 raw=False,
                 polling=True,
                 **kwargs):

    from azure.cli.command_modules.kusto._client_factory import cf_cluster

    _client = cf_cluster(cmd.cli_ctx, None)

    return _client.stop(resource_group_name=resource_group_name,
                        cluster_name=cluster_name,
                        custom_headers=custom_headers,
                        raw=raw,
                        polling=polling,
                        operation_config=kwargs)


def database_create(cmd,
                    resource_group_name,
                    cluster_name,
                    database_name,
                    soft_delete_period,
                    hot_cache_period=None,
                    custom_headers=None,
                    raw=False,
                    polling=True,
                    no_wait=False,
                    **kwargs):

    from azure.mgmt.kusto.models import Database
    from azure.cli.command_modules.kusto._client_factory import cf_database

    _client = cf_database(cmd.cli_ctx, None)
    _cluster = _cluster_get(cmd, resource_group_name, cluster_name, custom_headers, raw, **kwargs)

    if no_wait:
        location = _cluster.output.location
    else:
        location = _cluster.location

    soft_delete_period_in_days = round_soft_delete_to_days(soft_delete_period)
    hot_cache_period_in_days = round_hot_cache_to_days(hot_cache_period)

    _database = Database(location=location,
                         soft_delete_period_in_days=soft_delete_period_in_days,
                         hot_cache_period_in_days=hot_cache_period_in_days)

    return sdk_no_wait(no_wait,
                       _client.create_or_update,
                       resource_group_name=resource_group_name,
                       cluster_name=cluster_name,
                       database_name=database_name,
                       parameters=_database,
                       custom_headers=custom_headers,
                       raw=raw,
                       polling=polling,
                       operation_config=kwargs)


def update_kusto_cluster(instance, sku=None, capacity=None):

    from azure.mgmt.kusto.models import AzureSku
    if sku is None:
        sku = instance.sku.name
    if capacity is None:
        capacity = instance.sku.capacity
    instance.sku = AzureSku(name=sku, capacity=capacity)
    return instance


def update_kusto_database(instance, soft_delete_period, hot_cache_period=None):

    soft_delete_period_in_days = round_soft_delete_to_days(soft_delete_period)
    hot_cache_period_in_days = round_hot_cache_to_days(hot_cache_period)

    instance.soft_delete_period_in_days = soft_delete_period_in_days
    instance.hot_cache_period_in_days = hot_cache_period_in_days

    return instance


def _get_resource_group_location(cli_ctx, resource_group_name):

    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location