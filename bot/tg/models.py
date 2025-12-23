from django.db import models

from django.db import models

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    subscribed = models.BooleanField(default=False)
    survey_passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=32)
    hello_message = models.BooleanField(default=False)
    username = models.CharField(max_length=150, default="...")
    inactive = models.BooleanField(default=False)

    def __str__(self):
        return f'id: {self.telegram_id}, username: {self.username}'
    
    def __repr__(self):
        return f'id: {self.telegram_id}, username: {self.username}'


class SurveyAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
