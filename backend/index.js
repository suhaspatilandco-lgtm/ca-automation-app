// Minimal Express backend with a built-in self-test mode.
// Listens on process.env.PORT || 4000
const express = require('express');
const http = require('http');

const app = express();
app.use(express.json());

// Sample in-memory data to simulate tasks/workflow items
let tasks = [
  { id: 1, title: 'Client onboarding - collect KYC', status: 'pending' },
  { id: 2, title: 'Prepare tax computation', status: 'in-progress' },
  { id: 3, title: 'Finalize audit checklist', status: 'done' }
];

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

app.get('/api/tasks', (req, res) => {
  res.json({ count: tasks.length, tasks });
});

app.post('/api/tasks', (req, res) => {
  const { title } = req.body;
  if (!title) return res.status(400).json({ error: 'title required' });
  const id = tasks.length ? tasks[tasks.length - 1].id + 1 : 1;
  const task = { id, title, status: 'pending' };
  tasks.push(task);
  res.status(201).json(task);
});

const port = Number(process.env.PORT || 4000);

// Start server normally
if (!process.argv.includes('--selftest')) {
  app.listen(port, () => {
    console.log(`Backend listening at http://localhost:${port}`);
  });
}

// Self-test mode: start on ephemeral port, request /api/health and exit with code
async function runSelfTest() {
  return new Promise((resolve) => {
    const server = app.listen(0, () => {
      const p = server.address().port;
      const opts = { hostname: '127.0.0.1', port: p, path: '/api/health', method: 'GET' };
      const req = http.request(opts, (res) => {
        let body = '';
        res.on('data', (c) => (body += c));
        res.on('end', () => {
          try {
            const j = JSON.parse(body);
            if (j && j.status === 'ok') {
              console.log('SELFTEST: PASS');
              server.close(() => resolve(0));
            } else {
              console.error('SELFTEST: FAIL - bad payload', body);
              server.close(() => resolve(2));
            }
          } catch (e) {
            console.error('SELFTEST: FAIL - exception', e.message);
            server.close(() => resolve(3));
          }
        });
      });
      req.on('error', (e) => {
        console.error('SELFTEST: FAIL - request error', e.message);
        server.close(() => resolve(4));
      });
      req.end();
    });
  });
}

if (process.argv.includes('--selftest')) {
  runSelfTest().then((code) => process.exit(code));
}