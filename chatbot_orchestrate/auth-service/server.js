// server.js (诊断版)
require('dotenv').config();
const express = require('express');
const bcrypt = require('bcryptjs'); // 确认是 bcryptjs（纯JS）
const jwt = require('jsonwebtoken');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const app = express();
app.use(express.json());

// —— 请求级日志，确认请求是否到达 ——
app.use((req, res, next) => {
  console.log(new Date().toISOString(), req.method, req.url);
  next();
});

app.use(helmet());
app.use(cors({ origin: true, credentials: true }));
app.use(rateLimit({ windowMs: 60 * 1000, max: 60 }));

// —— 健康检查路由 ——
// 用于 curl /health 快速验证链路
app.get('/health', (_req, res) => res.json({ ok: true, t: Date.now() }));

// —— 同步种子用户（避免异步竞态） ——
const USERS = [
  { id: 'u1', username: 'user', passwordHash: bcrypt.hashSync('pass123', 10), roles: ['student'] },
];

function signAccess(payload) {
  return jwt.sign(payload, process.env.JWT_SECRET || 'dev-secret', {
    expiresIn: process.env.JWT_EXPIRES_IN || '15m',
    audience: 'utas-coursemate',
    issuer: 'auth-service',
  });
}

function auth(req, res, next) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'missing token' });
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET || 'dev-secret', {
      audience: 'utas-coursemate',
      issuer: 'auth-service',
    });
    next();
  } catch {
    return res.status(401).json({ error: 'invalid token' });
  }
}

app.post('/auth/login', async (req, res) => {
  try {
    console.log('LOGIN body =', req.body); // ← 看看有没有收到
    const { username, password } = req.body || {};
    if (!username || !password) return res.status(400).json({ error: 'username/password required' });
    const u = USERS.find(x => x.username === username);
    if (!u) return res.status(401).json({ error: 'invalid credentials' });
    const ok = await bcrypt.compare(password, u.passwordHash);
    if (!ok) return res.status(401).json({ error: 'invalid credentials' });
    const token = signAccess({ sub: u.id, username: u.username, roles: u.roles });
    return res.json({ access_token: token, token_type: 'Bearer', expires_in: 900 });
  } catch (e) {
    console.error('LOGIN_ERROR', e);
    return res.status(500).json({ error: 'server error' });
  }
});

app.get('/me', auth, (req, res) => {
  res.json({ user: { id: req.user.sub, username: req.user.username, roles: req.user.roles } });
});

app.get('/protected/ping', auth, (_req, res) => res.json({ ok: true, t: Date.now() }));

const port = process.env.PORT || 3000;
const host = process.env.HOST || '0.0.0.0'; // 显式绑定所有网卡
app.listen(port, host, () => console.log(`auth service running on ${host}:${port}`));
