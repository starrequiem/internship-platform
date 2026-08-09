/**
 * 实习通 · 认证模块
 * JWT token 管理 + 登录状态 + 顶栏UI更新
 */
const Auth = {
  getToken() { return localStorage.getItem('token'); },
  setToken(token) { localStorage.setItem('token', token); },
  getUser() {
    try { const u = localStorage.getItem('user'); return u ? JSON.parse(u) : null; }
    catch (_) { return null; }
  },
  setUser(user) { localStorage.setItem('user', JSON.stringify(user)); },
  isLoggedIn() { return !!this.getToken(); },
  logout() { localStorage.removeItem('token'); localStorage.removeItem('user'); this.updateUI(); },

  async login(username, password) {
    const data = await UserAPI.login(username, password);
    this.setToken(data.token);
    this.setUser(data.user);
    this.updateUI();
    return data;
  },

  async registerAndLogin(formData) {
    await UserAPI.register(formData);
    return this.login(formData.username, formData.password);
  },

  updateUI() {
    const user = this.getUser();
    const loginBtn = document.getElementById('header-login-btn');
    const userArea = document.getElementById('header-user-area');
    const avatarEl = document.getElementById('header-avatar');
    const nameEl   = document.getElementById('header-username');

    if (user) {
      if (loginBtn) loginBtn.style.display = 'none';
      if (userArea) { userArea.style.display = 'flex'; userArea.style.flexWrap = 'nowrap'; }
      if (avatarEl) avatarEl.textContent = user.username ? user.username.charAt(0) : '?';
      if (nameEl)   nameEl.textContent = user.username || '';
    } else {
      if (loginBtn) loginBtn.style.display = '';
      if (userArea) userArea.style.display = 'none';
    }
  }
};

document.addEventListener('components-loaded', () => Auth.updateUI());
document.addEventListener('DOMContentLoaded', () => { setTimeout(() => Auth.updateUI(), 100); });
