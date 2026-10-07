from django.contrib import admin

from .models import (
    BulkOperation,
    ContractField,
    ContractVersion,
    Dashboard,
    DashboardWidget,
    MetricDefinition,
    RealtimeEvent,
    ViewRecipe,
    WebhookDelivery,
    WebhookEndpoint,
)

for model in (
    ContractVersion,
    ContractField,
    ViewRecipe,
    MetricDefinition,
    Dashboard,
    DashboardWidget,
    WebhookEndpoint,
    WebhookDelivery,
    RealtimeEvent,
    BulkOperation,
):
    admin.site.register(model)
