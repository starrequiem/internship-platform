/**
 * 实习通 · API 工具模块
 * 封装 fetch 请求，自动附带 JWT 认证头
 */
const API_BASE = 'http://localhost:3000/api';

async function api(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || '请求失败');
  return data;
}

/* ---- 实习 ---- */
const InternAPI = {
  list(params = {}) {
    var clean = {};
    for (var k in params) { if (params[k] !== undefined && params[k] !== null && params[k] !== '') { clean[k] = params[k]; } }
    var qs = new URLSearchParams(clean).toString();
    return api('/internships' + (qs ? '?' + qs : ''));
  },
  detail(id) {
    return api(`/internships/${id}`);
  },
  hot() {
    return api('/internships/hot/list');
  },
  urgent() {
    return api('/internships/urgent/list');
  },
  create(data) {
    return api('/internships', { method: 'POST', body: JSON.stringify(data) });
  },
  update(id, data) {
    return api(`/internships/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  },
  close(id) {
    return api(`/internships/${id}/close`, { method: 'PUT' });
  },
};

/* ---- 用户 ---- */
const UserAPI = {
  login(username, password) {
    return api('/users/login', { method: 'POST', body: JSON.stringify({ username, password }) });
  },
  register(data) {
    return api('/users/register', { method: 'POST', body: JSON.stringify(data) });
  },
  profile(id) {
    return api(`/users/${id}`);
  },
  me() {
    return api('/users/me/profile');
  },
  updateProfile(data) {
    return api('/users/profile', { method: 'PUT', body: JSON.stringify(data) });
  },
  internships(id) {
    return api(`/users/${id}/internships`);
  },
  favorites(id) {
    return api(`/users/${id}/favorites`);
  },
  preferences(id) {
    return api(`/users/${id}/preferences`);
  },
  addPreference(id, tag_name) {
    return api(`/users/${id}/preferences`, { method: 'POST', body: JSON.stringify({ tag_name }) });
  },
  removePreference(id, tagName) {
    return api(`/users/${id}/preferences/${encodeURIComponent(tagName)}`, { method: 'DELETE' });
  },
  sendVerifyCode(email) {
    return api('/users/bind-email/send-code', { method: 'POST', body: JSON.stringify({ email }) });
  },
  verifyEmail(email, code) {
    return api('/users/bind-email/verify', { method: 'POST', body: JSON.stringify({ email, code }) });
  },
  forgotPassword(email, username) {
    return api('/users/forgot-password', { method: 'POST', body: JSON.stringify({ email, username }) });
  },
  resetPassword(email, code, new_password) {
    return api('/users/reset-password', { method: 'POST', body: JSON.stringify({ email, code, new_password }) });
  },
};

/* ---- 收藏（user_id 由后端从 token 获取） ---- */
const FavAPI = {
  add(internship_id) {
    return api('/favorites', { method: 'POST', body: JSON.stringify({ internship_id }) });
  },
  remove(internship_id) {
    return api('/favorites', { method: 'DELETE', body: JSON.stringify({ internship_id }) });
  },
  check(internship_id) {
    return api(`/favorites/check?internship_id=${internship_id}`);
  },
};

/* ---- 标签 ---- */
const TagAPI = {
  list() {
    return api('/tags');
  },
};

/* ---- 订阅 ---- */
const SubAPI = {
  subscribe(data) {
    return api('/subscriptions', { method: 'POST', body: JSON.stringify(data) });
  },
  list() {
    return api('/subscriptions');
  },
  remove(id) {
    return api(`/subscriptions/${id}`, { method: 'DELETE' });
  },
};

/* ---- 通知 ---- */
const NotifAPI = {
  list(unreadOnly) {
    return api('/notifications' + (unreadOnly ? '?unread_only=1' : ''));
  },
  unreadCount() {
    return api('/notifications/unread-count');
  },
  markRead(id) {
    return api(`/notifications/${id}/read`, { method: 'PUT' });
  },
  markAllRead() {
    return api('/notifications/read-all', { method: 'PUT' });
  },
};

/* ---- 投递 ---- */
const AppAPI = {
  apply(internship_id) {
    return api('/applications', { method: 'POST', body: JSON.stringify({ internship_id }) });
  },
  list() {
    return api('/applications');
  },
};

/* ---- 文件上传 ---- */
async function uploadFile(type, file) {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('请先登录');
  const formData = new FormData();
  formData.append('file', file);
  const resp = await fetch(`${API_BASE}/upload/${type}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || '上传失败');
  return data;
}
