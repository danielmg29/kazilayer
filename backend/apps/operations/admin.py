from django.contrib import admin

from .models import (
    AuditEvent,
    Comment,
    ExportJob,
    FileAsset,
    ImportJob,
    Mention,
    Notification,
    NotificationPreference,
    NotificationTemplate,
    SearchDocument,
    ServiceRequest,
    UserFeedback,
    WorkOrder,
    WorkTransition,
)

for model in (
    UserFeedback,
    ServiceRequest,
    Comment,
    Mention,
    FileAsset,
    SearchDocument,
    ImportJob,
    ExportJob,
    AuditEvent,
    WorkOrder,
    WorkTransition,
    NotificationPreference,
    NotificationTemplate,
    Notification,
):
    admin.site.register(model)
