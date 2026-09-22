from django.utils import timezone


def shell(request):
    today = timezone.localdate()
    start = today.year if today.month >= 7 else today.year - 1
    return {"nomination_cycle": f"{start}–{str(start + 1)[-2:]}", "today": today}
