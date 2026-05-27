    .PHONY: demo-up demo-down demo-logs demo-health demo-test

    demo-up:
	docker compose up -d --build

    demo-down:
	docker compose down

    demo-logs:
	docker compose logs -f

    demo-health:
	bash deploy/scripts/healthcheck.sh

    demo-test:
	PYTHONPATH=reference/python pytest tests/conformance/test_demo_api.py -q
