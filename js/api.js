/**
 * 实习通 · API 工具模块
 * 封装 fetch 请求，自动附带 JWT 认证头
 */
const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') && location.port === '8080'
  ? 'http://localhost:3000/api'
  : '/api';

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
  captcha(username) {
    return api('/users/captcha', { method: 'POST', body: JSON.stringify({ username }) });
  },
  changePassword(old_password, new_password) {
    return api('/users/password', { method: 'PUT', body: JSON.stringify({ old_password, new_password }) });
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
  list() { return api('/tags'); },
};
