# CA Automation App

Minimal runnable skeleton for CA Practice Automation. This repo contains:
- A small Express backend (backend/index.js) with health + sample API.
- A tiny static frontend (frontend/index.html) that calls the backend.
- Dockerfile + docker-compose to run the backend container.
- CI workflow to run tests.
- A selftest runnable via `npm test`.

Quickstart (local)
1. Clone repo
2. npm install
3. In terminal A: npm start            # starts backend on PORT (default 4000)
4. In terminal B: npm run start:frontend   # serves frontend at http://localhost:3000
5. Open http://localhost:3000

Docker (single backend container)
1. docker build -t ca-automation-app .
2. docker run -p 4000:4000 ca-automation-app

CI
- A GitHub Actions workflow will run `npm install` and `npm test` on push/PR.

Verification checklist
- [ ] Backend responds to GET /api/health
- [ ] Backend responds to GET /api/tasks with sample items
- [ ] Frontend loads and displays tasks from backend
- [ ] `npm test` runs the selftest and exits with success code
- [ ] Docker image builds and container runs the backend

If you want additional production features (DB, auth, secrets management, infra manifests), tell me which and I’ll add them next.