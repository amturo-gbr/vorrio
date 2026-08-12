.PHONY: api-docs api-docs-check backend-test acceptance-test docs-check external-path-test frontend-build frontend-test image pwa-check release-package-check check

CHECK_IMAGE ?= vorrio:check

image:
	docker build -t $(CHECK_IMAGE) .

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

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test

pwa-check:
	python3 scripts/check_pwa_contract.py

docs-check:
	python3 scripts/check_docs_links.py

release-package-check:
	python3 scripts/check_release_package.py

check: backend-test acceptance-test external-path-test frontend-test frontend-build pwa-check docs-check release-package-check api-docs-check
