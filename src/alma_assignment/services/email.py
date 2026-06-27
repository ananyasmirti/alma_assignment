import logging

import resend

from alma_assignment.core.config import settings

logger = logging.getLogger(__name__)


def _init_resend() -> None:
    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key


_init_resend()


async def send_prospect_confirmation(first_name: str, prospect_email: str) -> None:
    if not settings.resend_api_key:
        logger.info("No RESEND_API_KEY set — skipping prospect email to %s", prospect_email)
        return

    params: resend.Emails.SendParams = {
        "from": settings.email_from,
        "to": [prospect_email],
        "subject": "We received your application — Alma",
        "html": f"""
        <p>Hi {first_name},</p>
        <p>Thank you for your interest in working with Alma. We've received your application
        and our team will review it shortly.</p>
        <p>We'll be in touch soon.</p>
        <p>— The Alma Team</p>
        """,
    }
    try:
        resend.Emails.send(params)
    except Exception:
        logger.exception("Failed to send prospect confirmation to %s", prospect_email)


async def send_attorney_notification(
    first_name: str,
    last_name: str,
    prospect_email: str,
    lead_id: str,
    submitted_at: str,
) -> None:
    if not settings.resend_api_key:
        logger.info(
            "No RESEND_API_KEY set — skipping attorney notification for lead %s", lead_id
        )
        return

    dashboard_link = f"http://localhost:3000/dashboard?lead={lead_id}"

    params: resend.Emails.SendParams = {
        "from": settings.email_from,
        "to": [settings.attorney_email],
        "subject": f"New Lead: {first_name} {last_name}",
        "html": f"""
        <p>A new prospect has submitted their information.</p>
        <table>
          <tr><td><strong>Name</strong></td><td>{first_name} {last_name}</td></tr>
          <tr><td><strong>Email</strong></td><td>{prospect_email}</td></tr>
          <tr><td><strong>Submitted</strong></td><td>{submitted_at}</td></tr>
        </table>
        <p><a href="{dashboard_link}">View in dashboard</a></p>
        """,
    }
    try:
        resend.Emails.send(params)
    except Exception:
        logger.exception("Failed to send attorney notification for lead %s", lead_id)
