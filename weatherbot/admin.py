from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import BotConfig, Channel, City, PublicationLog, Schedule

admin.site.site_header = "Telegram Weather Publisher"
admin.site.site_title = "Telegram Weather Publisher Admin"
admin.site.index_title = "Управление сервисом"


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "chat_id", "active")
    list_filter = ("active",)
    search_fields = ("name", "chat_id")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("forecast_type", "publish_time", "active")
    list_filter = ("active", "forecast_type")


@admin.register(BotConfig)
class BotConfigAdmin(admin.ModelAdmin):
    list_display = ("config_label", "service_enabled", "default_city", "updated_at")
    list_display_links = ("config_label",)

    def config_label(self, _obj):
        return "Открыть настройки"

    config_label.short_description = "Конфиг"

    def has_add_permission(self, request):
        return not BotConfig.objects.exists()

    def changelist_view(self, request, extra_context=None):
        config = BotConfig.get_solo()
        change_url = reverse("admin:weatherbot_botconfig_change", args=[config.pk])
        return redirect(change_url)


@admin.register(PublicationLog)
class PublicationLogAdmin(admin.ModelAdmin):
    list_display = (
        "channel",
        "city",
        "forecast_type",
        "target_date",
        "success",
        "message_id",
        "created_at",
    )
    list_filter = ("success", "forecast_type", "target_date")
    search_fields = ("channel__name", "channel__chat_id", "city__name", "error")
    readonly_fields = (
        "channel",
        "city",
        "forecast_type",
        "target_date",
        "message_id",
        "success",
        "error",
        "created_at",
    )

    def has_add_permission(self, request):
        return False
