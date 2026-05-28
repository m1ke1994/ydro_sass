# -*- coding: utf-8 -*-
import logging

from celery import states
from celery import shared_task
from django.utils import timezone

from seo_audit.models import SiteSEOAudit
from seo_audit.services.crawler import AuditCancelledError, crawl_site_audit
from seo_audit.services.scoring import recalculate_audit_score

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="seo_audit.run_site_audit")
def run_site_audit_task(self, audit_id: int) -> None:
    audit = SiteSEOAudit.objects.filter(id=audit_id).first()
    if not audit:
        logger.warning("seo_audit.task аудит не найден audit_id=%s", audit_id)
        return

    task_id = str(getattr(self.request, "id", "") or "")
    logger.info(
        "seo_audit.task запуск audit_id=%s client_id=%s domain=%s task_id=%s",
        audit.id,
        audit.client_id,
        audit.domain,
        task_id,
    )

    audit.celery_task_id = task_id or audit.celery_task_id
    if audit.is_cancelled:
        audit.status = SiteSEOAudit.Status.STOPPED
        audit.finished_at = timezone.now()
        audit.save(update_fields=["celery_task_id", "status", "finished_at"])
        logger.info(
            "seo_audit.task остановлен до старта audit_id=%s client_id=%s domain=%s task_id=%s",
            audit.id,
            audit.client_id,
            audit.domain,
            task_id,
        )
        self.update_state(state=states.REVOKED)
        return

    audit.status = SiteSEOAudit.Status.RUNNING
    audit.finished_at = None
    audit.save(update_fields=["celery_task_id", "status", "finished_at"])

    def _stop_requested() -> bool:
        audit.refresh_from_db(fields=["is_cancelled"])
        return bool(audit.is_cancelled)

    try:
        crawl_site_audit(audit, stop_check=_stop_requested)
        try:
            recalculate_audit_score(audit)
        except Exception:
            logger.exception("seo_audit.task не удалось пересчитать итоговый score audit_id=%s", audit.id)
    except AuditCancelledError:
        try:
            recalculate_audit_score(audit)
        except Exception:
            logger.exception("seo_audit.task не удалось пересчитать частичный score audit_id=%s", audit.id)
        audit.status = SiteSEOAudit.Status.STOPPED
        audit.finished_at = timezone.now()
        audit.save(update_fields=["status", "finished_at"])
        logger.info(
            "seo_audit.task остановлен audit_id=%s client_id=%s domain=%s task_id=%s score=%s pages_count=%s",
            audit.id,
            audit.client_id,
            audit.domain,
            task_id,
            audit.seo_score,
            audit.pages_count,
        )
        self.update_state(state=states.REVOKED)
        return
    except Exception:
        logger.exception("seo_audit.task ошибка audit_id=%s domain=%s task_id=%s", audit.id, audit.domain, task_id)
        audit.status = SiteSEOAudit.Status.ERROR
        audit.finished_at = timezone.now()
        audit.save(update_fields=["status", "finished_at"])
        return

    audit.refresh_from_db(fields=["is_cancelled", "seo_score", "pages_count"])
    if audit.is_cancelled:
        audit.status = SiteSEOAudit.Status.STOPPED
        audit.finished_at = timezone.now()
        audit.save(update_fields=["status", "finished_at"])
        logger.info(
            "seo_audit.task остановлен после обхода audit_id=%s client_id=%s domain=%s task_id=%s",
            audit.id,
            audit.client_id,
            audit.domain,
            task_id,
        )
        self.update_state(state=states.REVOKED)
        return

    audit.status = SiteSEOAudit.Status.DONE
    audit.finished_at = timezone.now()
    audit.save(update_fields=["status", "finished_at"])
    logger.info(
        "seo_audit.task завершён audit_id=%s client_id=%s domain=%s task_id=%s score=%s pages_count=%s",
        audit.id,
        audit.client_id,
        audit.domain,
        task_id,
        audit.seo_score,
        audit.pages_count,
    )
