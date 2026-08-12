.PHONY: api-docs api-docs-check backend-i18n-check backend-test acceptance-test docs-check external-path-test frontend-deps frontend-build frontend-test image image-scan sbom pwa-check release-package-check website-check check

CHECK_IMAGE ?= vorrio:check
GRYPE_IMAGE ?= anchore/grype:v0.110.0@sha256:af65fbc0c664691067788fe95ff88760b435543e45595eb2ca6f102fc476fbe1
SYFT_IMAGE ?= anchore/syft:v1.42.3@sha256:5999d209a342e55e9edf70bf8930fb5b86d8f2a783fa401178372c50e21b1d36
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

backend-i18n-check:
	python3 scripts/check_backend_i18n_contract.py

website-check:
	python3 scripts/check_website_contract.py

release-package-check:
	python3 scripts/check_release_package.py

check: backend-test acceptance-test external-path-test frontend-test frontend-build pwa-check docs-check backend-i18n-check website-check release-package-check api-docs-check
