from django.urls import path

from . import api

urlpatterns = [
    path("organizations/<slug:slug>/convergence/contracts/", api.contracts),
    path(
        "organizations/<slug:slug>/convergence/contracts/<uuid:contract_id>/publish/",
        api.publish_contract,
    ),
    path(
        "organizations/<slug:slug>/convergence/dynamic-forms/<slug:contract_key>/",
        api.dynamic_form,
    ),
    path("organizations/<slug:slug>/convergence/view-recipes/", api.view_recipes),
    path("organizations/<slug:slug>/convergence/dashboards/", api.dashboards),
    path("organizations/<slug:slug>/convergence/webhooks/", api.webhooks),
    path(
        "organizations/<slug:slug>/convergence/webhooks/<uuid:endpoint_id>/rotate/",
        api.rotate_webhook,
    ),
    path("organizations/<slug:slug>/convergence/realtime/", api.realtime),
    path("organizations/<slug:slug>/convergence/bulk-operations/", api.bulk_operations),
    path(
        "organizations/<slug:slug>/convergence/bulk-operations/<uuid:operation_id>/confirm/",
        api.confirm_bulk_operation,
    ),
]
