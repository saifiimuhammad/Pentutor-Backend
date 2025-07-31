from .models import UserActivity


def log_activity(user, activity):
    UserActivity.objects.create(user=user, activity=activity)


ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/svg"]
MAX_FILE_SIZE_MB = 2


def validate_file(file, field_name):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"{field_name} must be JPEG, JPG, PNG or SVG.")

    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"{field_name} must be under {MAX_FILE_SIZE_MB}MB.")
