# DataOps Demo App

Ứng dụng demo end-to-end cho [DataOps Control Plane](https://github.com/AndyAnh174/dataops-control-plane): Next.js gọi FastAPI qua Caddy, GitHub Actions self-hosted runner kiểm thử, scan image, publish lên GHCR và triển khai lên VPS.

## Live demo

- Ứng dụng: [https://dataops.andyanh.id.vn](https://dataops.andyanh.id.vn)
- Health check: [https://dataops.andyanh.id.vn/api/health](https://dataops.andyanh.id.vn/api/health)
- Nginx gateway: [`ops/nginx/dataops.andyanh.id.vn.conf`](ops/nginx/dataops.andyanh.id.vn.conf)

## Demo chứng minh điều gì?

```text
git push
  -> self-hosted runner nhận job
  -> DataOps Agent đọc dataops.yaml và gửi RUNNING event
  -> agent chạy test FastAPI + Next.js
  -> agent build, scan và publish Docker images theo commit SHA
  -> agent deploy + health check + rollback nếu lỗi
  -> agent gửi log từng stage và trạng thái SUCCESS / FAILED về Control Plane
```

DataOps Control Plane hiện chứng minh phần **chuẩn hóa và lưu trạng thái pipeline đa provider**, idempotency event và audit theo run. AI Agent/RCA/auto-recovery chưa được triển khai ở giai đoạn này; workflow không giả vờ rằng phần đó đã tồn tại.

Workflow chỉ cần checkout rồi gọi
[`AndyAnh174/dataops-agent@v0`](https://github.com/AndyAnh174/dataops-agent). Toàn bộ
pipeline portable nằm trong [`dataops.yaml`](dataops.yaml); `DATAOPS_TOKEN` được lưu bằng
GitHub Actions secret.

## Chạy local

Backend:

```bash
cd backend
uv sync --group dev
uv run pytest
uv run fastapi dev app/main.py
```

Frontend:

```bash
cd frontend
npm ci
npm test
npm run dev
```

## Kích hoạt demo lỗi có kiểm soát

Vào tab **Actions**, chọn workflow **CI/CD with DataOps telemetry**, chọn **Run workflow**, bật `simulate_failure`. Workflow dừng trước bước publish/deploy và gửi trạng thái `FAILED` vào control plane. Chạy lại với tùy chọn tắt để thấy cùng luồng thành công.

## Network và rollback

- Chỉ Caddy expose TCP `80`.
- FastAPI chỉ nằm trong Docker network nội bộ.
- DataOps API bind `127.0.0.1:18080` trên VPS.
- Mỗi release dùng tag `sha-<full-commit>`.
- Nếu Compose hoặc health check thất bại, `deploy/deploy.sh` tự triển khai lại bộ image trước đó.

## License

[MIT](LICENSE) © 2026 AndyAnh174.
