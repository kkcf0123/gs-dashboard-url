# GS Dashboard URL

GS Dashboard 데스크톱 앱이 현재 Cloudflare Quick Tunnel 주소를 찾기 위한 공개 설정 저장소입니다. 이 저장소에는 API 키, Discord 토큰, GitHub 토큰 또는 SSH 자격 증명을 저장하지 않습니다.

## 공개 설정

`dashboard.json` 형식:

```json
{
  "schema_version": 1,
  "url": "https://example.trycloudflare.com",
  "updated_at": "2026-08-16T12:30:00Z",
  "source": "gs-ops-bot"
}
```

데스크톱 앱은 다음 고정 주소에서 파일을 읽을 수 있습니다.

```text
https://raw.githubusercontent.com/kkcf0123/gs-dashboard-url/main/dashboard.json
```

앱은 받은 URL을 바로 적용하지 않고 다음 조건을 확인해야 합니다.

1. `https://*.trycloudflare.com` 루트 주소인지 검증
2. 새 주소의 `/health`가 정상인지 확인
3. 정상일 때만 로컬 주소를 교체
4. 조회 또는 연결 실패 시 마지막 정상 주소 유지

## Raspberry Pi에서 갱신

GitHub fine-grained token은 Raspberry Pi의 `.env`에만 저장합니다. 토큰에는 이 저장소의 **Contents: Read and write** 권한만 부여하세요.

```env
GITHUB_TOKEN=...
GITHUB_REPOSITORY=kkcf0123/gs-dashboard-url
GITHUB_CONFIG_BRANCH=main
```

갱신 명령:

```bash
python3 scripts/update_dashboard_url.py https://example.trycloudflare.com
```

`scripts/update_dashboard_url.py`는 표준 라이브러리만 사용하며 URL 형식을 검증한 뒤 GitHub Contents API로 `dashboard.json`을 갱신합니다. 이미 같은 주소가 게시되어 있으면 불필요한 커밋을 만들지 않습니다. GS Ops 봇은 Quick Tunnel 변경을 감지한 직후 같은 방식으로 이 파일을 자동 갱신합니다.

실제 Raspberry Pi 운영 환경은 개인 계정 토큰 대신 이 저장소 하나에만 쓰기 가능한 SSH Deploy Key를 사용합니다. 개인키는 Pi의 `~/.ssh`에만 보관하고, 봇은 전용 checkout의 `dashboard.json`만 커밋·푸시합니다. 이 방식은 GitHub 계정의 다른 저장소에 대한 권한을 부여하지 않습니다.

## 테스트

```bash
python -m unittest discover -s tests -v
python -m json.tool dashboard.json
```
