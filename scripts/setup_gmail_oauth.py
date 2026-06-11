"""一次性 OAuth 流程：在本機跑一次，拿到 GMAIL_REFRESH_TOKEN。

用法：
  1. 到 Google Cloud Console 建立 OAuth Client ID（Desktop app 類型）
  2. 下載 client_secret.json，放到本目錄
  3. python3 scripts/setup_gmail_oauth.py
  4. 瀏覽器會自動開，登入並同意授權
  5. 終端會印出 refresh_token，複製到 GitHub Secrets
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def main():
    client_secret_file = Path(__file__).parent / "client_secret.json"
    if not client_secret_file.exists():
        print(
            f"找不到 {client_secret_file}\n"
            "請到 Google Cloud Console 下載 OAuth Client ID JSON 後放到此路徑。",
            file=sys.stderr,
        )
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    secret = json.loads(client_secret_file.read_text())
    installed = secret.get("installed") or secret.get("web") or {}

    print("\n===== 拿到了！把下面三個值放進 GitHub Secrets =====\n")
    print(f"GMAIL_CLIENT_ID     = {installed.get('client_id')}")
    print(f"GMAIL_CLIENT_SECRET = {installed.get('client_secret')}")
    print(f"GMAIL_REFRESH_TOKEN = {creds.refresh_token}")
    print(
        "\n設定路徑：GitHub repo → Settings → Secrets and variables → Actions → New repository secret"
    )


if __name__ == "__main__":
    main()
