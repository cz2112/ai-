from app.workers.celery_app import celery_app


def test_process_upload_task_is_registered():
    assert "app.workers.tasks.process_upload" in celery_app.tasks
