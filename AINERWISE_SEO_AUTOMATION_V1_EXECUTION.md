# AinerWise SEO Automation V1 Execution

## Principle

AinerWise public SEO is shared by PC, H5, and product storefront pages. Admin can control locale, region, page overrides, keyword policy, and review-first batch optimization. AI may draft SEO copy, but generated metadata must be reviewed before publication.

## Architecture Decision

- `Ainerwise/backend/app/api/v1/endpoints/seo.py` is the SEO policy and batch automation API.
- `Ainerwise/frontend-pc/composables/useAinerwiseSeo.ts` is the shared PC and Store SEO runtime.
- `Ainerwise/frontend-h5/composables/useAinerwiseSeo.ts` is the shared H5 SEO runtime.
- `Ainerwise/frontend-admin/pages/seo/index.vue` is the Marketing/Admin SEO control center.
- Root `CebuProjects` remains read-only and is not part of this implementation.

## Public Entrypoints

- PC official site: `http://localhost:4099`
- H5 official site: `http://localhost:4098`
- Product Store PC: `http://localhost:4096`
- Marketing/Admin SEO center: `http://localhost:4094/seo`
- Admin console alias: `http://localhost:4097/seo`

## SEO Scope

| Area | Status | Evidence |
| --- | --- | --- |
| Backend public SEO config API | READY_FOR_VERIFY | `GET /api/v1/seo/config` returns locales, regions, overrides |
| Backend admin SEO config API | READY_FOR_VERIFY | `GET /api/v1/admin/seo/config` with admin token returns config + static page catalog |
| Backend batch SEO preview | READY_FOR_VERIFY | `POST /api/v1/admin/seo/batch/preview` returns review-first draft items |
| PC official page metadata | READY_FOR_VERIFY | `/cn/solutions` renders localized title, description, canonical, hreflang |
| H5 official page metadata | READY_FOR_VERIFY | `/cn` and `/pl/products` render localized title, description, canonical, hreflang |
| Product Store metadata | READY_FOR_VERIFY | `:4096/cn/products` and `:4096/pl/products` render product catalog SEO |
| PC/H5/Store sitemap | READY_FOR_VERIFY | `sitemap.xml` includes `en`, `zh-CN`, `sr-RS`, `pl-PL`, `x-default` alternates |
| Admin SEO Center UI | READY_FOR_VERIFY | Marketing portal `/seo` route is present and protected by portal access |
| Region-specific copy | READY_FOR_VERIFY | Serbia and Poland defaults supported, region overrides can be managed from admin |
| LLM draft optimization | READY_FOR_VERIFY | API supports `use_ai`, disabled by default, review required |

## Locale And Region Rules

- Enabled locales default to `en`, `zh`, `sr`, `pl`.
- Enabled regions default to `RS`, `PL`.
- Default region is `RS`.
- Frontend respects backend `default_region_code` and user cookie `ainerwise_region_code`.
- Region names and city names are localized for SEO descriptions where supported.
- Admin can override `region_overrides`, including future `localized_names` and `localized_cities`.

## Verification Commands

Run from `/Users/mac/Code_Start/Aislos`.

```bash
python3 -m py_compile Ainerwise/backend/app/api/v1/endpoints/seo.py Ainerwise/backend/app/api/v1/endpoints/localization.py Ainerwise/backend/app/core/portal_registry.py
```

```bash
cd Ainerwise/frontend-pc && npm run build
cd Ainerwise/frontend-h5 && npm run build
cd Ainerwise/frontend-admin && npm run build
```

```bash
cd Ainerwise
docker compose up -d --build backend frontend-pc frontend-h5 frontend-admin nginx
```

```bash
cd Ainerwise
docker compose exec -T backend python - <<'PY'
import urllib.request
for url in ['http://127.0.0.1:8000/health', 'http://127.0.0.1:8000/api/v1/seo/config']:
    with urllib.request.urlopen(url, timeout=8) as r:
        print(url, r.status, r.read(240).decode('utf-8'))
PY
```

```bash
cd Ainerwise
docker compose exec -T backend python - <<'PY'
import json
import urllib.request
base = 'http://127.0.0.1:8000/api/v1'
def req(path, method='GET', token=None, data=None):
    body = None if data is None else json.dumps(data).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    request = urllib.request.Request(base + path, data=body, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read().decode('utf-8')
        return response.status, json.loads(raw) if raw else {}
status, token_payload = req('/auth/login', method='POST', data={'email':'admin@ainerwise.com','password':'admin123456'})
token = token_payload['access_token']
print('login', status, bool(token))
status, config = req('/admin/seo/config', token=token)
print('admin-config', status, config['config']['enabled_locales'], config['config']['enabled_region_codes'], len(config['static_pages']))
status, preview = req('/admin/seo/batch/preview', method='POST', token=token, data={'locales':['zh','pl'], 'region_codes':['RS','PL'], 'page_paths':['/','/products'], 'use_ai':False})
print('preview', status, preview['total'], preview['items'][0]['title'])
PY
```

## Strict Agent Rules

- Do not modify root `CebuProjects`.
- Do not mark any SEO task as `VERIFIED` without an independent verification agent.
- Do not publish AI-generated SEO output automatically.
- Do not replace localized metadata with English-only fallbacks.
- Do not remove Store product SEO because PC `/products` redirects to the Store portal.
- Do not treat a page that merely opens as complete; verify meta title, meta description, canonical, hreflang, sitemap, and auth-gated admin APIs.

## Current Status

`READY_FOR_VERIFY`

