from celery import shared_task


@shared_task
def send_tracker_form_submit_notification_task(event_id: int, client_id: int) -> None:
    return None
