import hashlib
from datetime import timedelta
from django.utils import timezone
from .models import Payment
from jobboard.models import TutorPayment


def generate_secure_hash(data: dict, integrity_salt: str) -> str:
    sorted_keys = sorted(data.keys())
    string_to_hash = (
        integrity_salt + "&" + "&".join([str(data[k]) for k in sorted_keys])
    )
    return hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest()


def activate_tutor_plan(user, payment: Payment, plan_type: str):
    duration = {"BASIC": 30, "PREMIUM": 90}.get(plan_type, 0)

    end_date = timezone.now() + timedelta(days=duration)

    TutorPayment.objects.update_or_create(
        tutor=user,
        defaults={
            "plan": plan_type,
            "is_active": True,
            "start_date": timezone.now(),
            "end_date": end_date,
            "amount_paid": payment.amount,
            "last_payment": payment,
        },
    )
