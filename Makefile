.PHONY: api-docs api-docs-check backend-i18n-check backend-test acceptance-test docs-check docs-site-deps docs-site-check external-path-test frontend-deps frontend-build frontend-test image image-scan language-pack-check sbom pwa-check release-package-check secret-scan stripe-support-check stripe-support-integration-check website-check check

CHECK_IMAGE ?= vorrio:check
GRYPE_IMAGE ?= anchore/grype:v0.110.0@sha256:af65fbc0c664691067788fe95ff88760b435543e45595eb2ca6f102fc476fbe1
SYFT_IMAGE ?= anchore/syft:v1.42.3@sha256:5999d209a342e55e9edf70bf8930fb5b86d8f2a783fa401178372c50e21b1d36
GITLEAKS_IMAGE ?= zricethezav/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f
SBOM_FILE ?= vorrio-sbom.cdx.json

image:
	docker build -t $(CHECK_IMAGE) .

image-scan:
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$(CURDIR):/workspace:ro" \
		$(GRYPE_IMAGE) $(CHECK_IMAGE) \
		--fail-on high --only-fixed \
		--vex /workspace/security/vex.openvex.json \
		--output table

sbom:
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v "$(CURDIR):/output" \
		$(SYFT_IMAGE) $(CHECK_IMAGE) \
		--output cyclonedx-json=/output/$(SBOM_FILE)

api-docs: image
	docker run --rm --entrypoint python \
		-e PYTHONPATH=/workspace/backend \
		-v "$(CURDIR)/backend:/workspace/backend:ro" \
		-v "$(CURDIR)/scripts:/workspace/scripts:ro" \
		-v "$(CURDIR)/docs:/workspace/docs" \
		-w /workspace $(CHECK_IMAGE) scripts/sync_api_docs.py

api-docs-check: image
	docker run --rm --entrypoint python \
		-e PYTHONPATH=/workspace/backend \
		-v "$(CURDIR)/backend:/workspace/backend:ro" \
		-v "$(CURDIR)/scripts:/workspace/scripts:ro" \
		-v "$(CURDIR)/docs:/workspace/docs:ro" \
		-w /workspace $(CHECK_IMAGE) scripts/sync_api_docs.py --check

backend-test: image
	docker run --rm --entrypoint python \
		-e PYTHONPATH=/workspace/backend \
		-v "$(CURDIR)/backend:/workspace/backend:ro" \
		-w /workspace $(CHECK_IMAGE) -m unittest discover -s backend/tests -v

acceptance-test: image
	docker run --rm --entrypoint python \
		-e PYTHONPATH=/workspace/backend \
		-v "$(CURDIR)/backend:/workspace/backend:ro" \
		-v "$(CURDIR)/scripts:/workspace/scripts:ro" \
		-w /workspace $(CHECK_IMAGE) scripts/release_smoke.py
	docker run --rm --entrypoint python \
		-e PYTHONPATH=/workspace/backend \
		-v "$(CURDIR)/backend:/workspace/backend:ro" \
		-v "$(CURDIR)/scripts:/workspace/scripts:ro" \
		-w /workspace $(CHECK_IMAGE) scripts/family_security_smoke.py

external-path-test: image
	docker run --rm --entrypoint python \
		-e PYTHONPATH=/app \
		-e DATA_DIR=/tmp/vorrio-external-path-smoke \
		-e APP_SECRET_KEY=synthetic-external-path-secret-0123456789abcdef \
		-e DEPLOYMENT_PROFILE=public_https \
		-e PUBLIC_URL=https://vorrio.example.test \
		-e TRUSTED_HOSTS=vorrio.example.test \
		-e ALLOWED_ORIGINS=https://vorrio.example.test \
		-e FORWARDED_ALLOW_IPS=127.0.0.1 \
		-e SESSION_HTTPS_ONLY=true \
		-e PUBLIC_EXPOSURE_ACKNOWLEDGED=true \
		$(CHECK_IMAGE) /app/scripts/external_path_smoke.py

frontend-deps:
	cd frontend && npm ci

frontend-build: frontend-deps
	cd frontend && npm run build

frontend-test: frontend-deps
	cd frontend && npm test

pwa-check:
	python3 scripts/check_pwa_contract.py

docs-check:
	python3 scripts/check_docs_links.py

docs-site-deps:
	cd docs && npm ci

docs-site-check: docs-site-deps
	cd docs && npm run build
	python3 scripts/check_docs_site.py

backend-i18n-check:
	python3 scripts/check_backend_i18n_contract.py

language-pack-check:
	python3 scripts/validate_language_pack.py
	python3 -m unittest scripts.test_language_pack scripts.test_create_language_pack -v
	python3 scripts/check_translation_community.py

website-check:
	python3 scripts/check_website_contract.py

stripe-support-check:
	node --test scripts/test_stripe_support.mjs

stripe-support-integration-check:
	node scripts/check_stripe_test_support.mjs

release-package-check:
	python3 scripts/check_release_package.py
	python3 -m unittest scripts.test_release_package -v

secret-scan:
	docker run --rm \
		-v "$(CURDIR):/repository:ro" \
		-w /repository \
		$(GITLEAKS_IMAGE) git . --redact=100 --no-banner

check: secret-scan backend-test acceptance-test external-path-test frontend-test frontend-build pwa-check docs-check docs-site-check backend-i18n-check language-pack-check website-check stripe-support-check release-package-check api-docs-check
