from django.contrib import admin

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
    list_display = ("service_enabled", "default_city", "updated_at")

    def has_add_permission(self, request):
        return not BotConfig.objects.exists()


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
