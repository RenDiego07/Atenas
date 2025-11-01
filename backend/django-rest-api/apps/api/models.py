from django.db import models
from django.contrib.auth.models import User   # ✅ built-in User model


class Summary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="summaries")
    header = models.TextField(max_length= 50)
    url_link = models.TextField(max_length= 100)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.header
