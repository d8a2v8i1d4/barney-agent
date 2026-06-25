"""Gmail API 包裝：用 OAuth refresh token 寄信／建立草稿。

需要環境變數：
  GMAIL_CLIENT_ID
  GMAIL_CLIENT_SECRET
  GMAIL_REFRESH_TOKEN

一次性流程跑 setup_gmail_oauth.py 取得 refresh token。
gmail.compose 範圍同時涵蓋「建立草稿」與「直接寄送」，所以 send_message
不需要額外授權範圍。
"""

import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def get_credentials():
    client_id = os.environ["GMAIL_CLIENT_ID"]
    client_secret = os.environ["GMAIL_CLIENT_SECRET"]
    refresh_token = os.environ["GMAIL_REFRESH_TOKEN"]
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def _build_raw(to: str, subject: str, html_body: str) -> str:
    message = MIMEText(html_body, "html", "utf-8")
    message["to"] = to
    message["subject"] = subject
    return base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")


def send_message(to: str, subject: str, html_body: str) -> str:
    """直接寄出（進收件匣），回傳 message id。gmail.compose 範圍即可寄送。"""
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    raw = _build_raw(to, subject, html_body)
    sent = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )
    return sent["id"]


def create_draft(to: str, subject: str, html_body: str) -> str:
    """只建草稿（不寄出），回傳 draft id。保留供需要時使用。"""
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    raw = _build_raw(to, subject, html_body)
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return draft["id"]
