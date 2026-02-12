from django.db import models


class ForecastType(models.TextChoices):
    TODAY = "today", "Сегодня"
    TOMORROW = "tomorrow", "Завтра"
    THREE_DAYS = "three_days", "3 дня"


class City(models.Model):
    name = models.CharField(max_length=120, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Channel(models.Model):
    name = models.CharField(max_length=120)
    chat_id = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.chat_id})"


class Schedule(models.Model):
    forecast_type = models.CharField(max_length=20, choices=ForecastType.choices, unique=True)
    publish_time = models.TimeField()
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["publish_time"]

    def __str__(self) -> str:
        return f"{self.get_forecast_type_display()} @ {self.publish_time}"


class BotConfig(models.Model):
    singleton = models.BooleanField(default=True, unique=True)
    service_enabled = models.BooleanField(default=True)
    default_city = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.singleton = True
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(singleton=True)
        return obj

    def __str__(self) -> str:
        return "BotConfig"


class PublicationLog(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    forecast_type = models.CharField(max_length=20, choices=ForecastType.choices)
    target_date = models.DateField()
    message_id = models.CharField(max_length=64, blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "forecast_type", "target_date"],
                name="uniq_channel_forecast_date",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.channel} {self.forecast_type} {self.target_date}"
