# DataOps Demo App

Ứng dụng demo end-to-end cho [DataOps Control Plane](https://github.com/AndyAnh174/dataops-control-plane): Next.js gọi FastAPI qua Caddy, GitHub Actions self-hosted runner kiểm thử, scan image, publish lên GHCR và triển khai lên VPS.

## Demo chứng minh điều gì?

```text
git push
  -> self-hosted runner nhận job
  -> gửi RUNNING event vào DataOps
  -> test FastAPI + Next.js
  -> build và scan Docker images
  -> publish image theo commit SHA
  -> deploy + health check + rollback nếu lỗi
  -> gửi SUCCESS / FAILED / CANCELED event vào DataOps
```

DataOps Control Plane hiện chứng minh phần **chuẩn hóa và lưu trạng thái pipeline đa provider**, idempotency event và audit theo run. AI Agent/RCA/auto-recovery chưa được triển khai ở giai đoạn này; workflow không giả vờ rằng phần đó đã tồn tại.

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
