from django.urls import path

from . import api

urlpatterns = [
    path("organizations/<slug:slug>/operations/feedback/", api.feedback),
    path("organizations/<slug:slug>/operations/requests/", api.service_requests),
    path("organizations/<slug:slug>/operations/comments/", api.comments),
    path("organizations/<slug:slug>/operations/files/", api.files),
    path("organizations/<slug:slug>/operations/search/", api.search),
    path("organizations/<slug:slug>/operations/data-jobs/", api.data_jobs),
    path("organizations/<slug:slug>/operations/audit/", api.audit),
    path("organizations/<slug:slug>/operations/work-orders/", api.work_orders),
    path(
        "organizations/<slug:slug>/operations/work-orders/<uuid:work_order_id>/transition/",
        api.transition_work_order,
    ),
    path("organizations/<slug:slug>/operations/notifications/", api.notifications),
    path(
        "organizations/<slug:slug>/operations/notification-preferences/",
        api.notification_preferences,
    ),
    path("organizations/<slug:slug>/operations/sla-policies/", api.sla_policies),
    path(
        "organizations/<slug:slug>/operations/work-orders/<uuid:work_order_id>/apply-sla/",
        api.apply_sla,
    ),
    path("organizations/<slug:slug>/operations/dispatch/", api.dispatch_board),
]
