from django.db import models
from django.contrib.auth import get_user_model
from meetings.models import Meeting

User = get_user_model()

class Payment(models.Model):
    GATEWAY_CHOICES = (
        ('jazzcash', 'JazzCash'),
        ('easypaisa', 'EasyPaisa'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    txn_ref = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_successful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.gateway} - {self.amount}"
