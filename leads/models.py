from django.db import models


class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("won", "Won"),
        ("lost", "Lost"),
        ("closed", "Closed"),
    ]

    CONVERSION_RATING_CHOICES = [
        ("not_contacted", "Not contacted"),
        ("A", "A - Highly likely to convert"),
        ("B", "B - Some interest"),
        ("C", "C - Low interest"),
        ("D", "D - Not interested / dead lead"),
    ]

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    url = models.URLField(max_length=500, blank=True)
    rating_count = models.IntegerField(null=True, blank=True)
    star_count = models.FloatField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    zip = models.CharField(max_length=20, blank=True)
    facebook_link = models.URLField(max_length=500, blank=True)
    instagram_link = models.URLField(max_length=500, blank=True)
    twitter_link = models.URLField(max_length=500, blank=True)
    whatsapp_link = models.URLField(max_length=500, blank=True)
    tiktok_link = models.URLField(max_length=500, blank=True)
    linkedin_link = models.URLField(max_length=500, blank=True)
    youtube_link = models.URLField(max_length=500, blank=True)
    primary_category_name = models.CharField(max_length=255, blank=True)
    category_name = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    conversion_rating = models.CharField(
        max_length=20, choices=CONVERSION_RATING_CHOICES, default="not_contacted"
    )
    notes = models.TextField(blank=True)
    contact_date = models.DateField(null=True, blank=True)
    followup_date = models.DateField(null=True, blank=True)

    monday_hours = models.CharField(max_length=100, blank=True)
    tuesday_hours = models.CharField(max_length=100, blank=True)
    wednesday_hours = models.CharField(max_length=100, blank=True)
    thursday_hours = models.CharField(max_length=100, blank=True)
    friday_hours = models.CharField(max_length=100, blank=True)
    saturday_hours = models.CharField(max_length=100, blank=True)
    sunday_hours = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
