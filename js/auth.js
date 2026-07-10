/**
 * 实习通 · 认证模块
 * JWT token 管理 + 登录状态 + 顶栏UI更新
 */
const Auth = {
  getToken() {
    return localStorage.getItem('token');
  },
  setToken(token) {
    localStorage.setItem('token', token);
  },
  getUser() {
    try {
      const u = localStorage.getItem('user');
      return u ? JSON.parse(u) : null;
    } catch (_) { return null; }
  },
  setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
  },
  isLoggedIn() {
    return !!this.getToken();
  },
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    this.updateUI();
  },

  /** 检查当前用户是否为会员（管理员始终有会员权限） */
  isMember() {
    const user = this.getUser();
    if (!user) return false;
    // 管理员权限最大，无需绑定邮箱
    if (user.role === 'admin') return true;
    return user.is_member === 1;
  },

  /** 需要会员权限，否则跳转绑定邮箱页（管理员直接放行） */
  requireMember(redirectUrl) {
    if (!this.isLoggedIn()) {
      location.href = 'login.html?redirect=' + encodeURIComponent(redirectUrl || location.href);
      return false;
    }
    if (!this.isMember()) {
      location.href = 'bind-email.html?redirect=' + encodeURIComponent(redirectUrl || location.href);
      return false;
    }
    return true;
  },

  /** 刷新当前用户信息（用于邮箱绑定后更新 localStorage） */
  async refreshUser() {
    try {
      const user = await UserAPI.me();
      // 保留原 token 中的额外信息
      this.setUser({ ...this.getUser(), ...user });
      this.updateUI();
      return user;
    } catch (e) {
      console.log('刷新用户信息失败:', e.message);
      return null;
    }
  },

  async login(username, password) {
    const data = await UserAPI.login(username, password);
    this.setToken(data.token);
    this.setUser(data.user);
    this.updateUI();
    return data;
  },

  async register(formData) {
    const data = await UserAPI.register(formData);
    return data;
  },

  // 登录后自动跳转（注册成功 → 自动登录 → 跳转）
  async registerAndLogin(formData) {
    await this.register(formData);
    return this.login(formData.username, formData.password);
  },

  /** 根据登录状态更新顶栏UI */
  updateUI() {
    const user = this.getUser();
    const loginBtn  = document.getElementById('header-login-btn');
    const userArea  = document.getElementById('header-user-area');
    const avatarEl  = document.getElementById('header-avatar');
    const nameEl    = document.getElementById('header-username');

    if (user) {
      if (loginBtn) loginBtn.style.display = 'none';
      if (userArea) { userArea.style.display = 'flex'; userArea.style.flexWrap = 'nowrap'; }
      if (avatarEl) avatarEl.textContent = user.username ? user.username.charAt(0) : '我';
      if (nameEl)   nameEl.textContent = user.username || '';
    } else {
      if (loginBtn) loginBtn.style.display = '';
      if (userArea) userArea.style.display = 'none';
    }

    // 首页侧边栏个人快捷入口
    this.updateSidebarCard(user);
    // 通知铃铛
    this.refreshNotifBadge();
  },

  /** 刷新通知未读数 */
  async refreshNotifBadge() {
    const bell = document.getElementById('header-notif-bell');
    const badge = document.getElementById('notif-badge');
    if (!bell || !badge) return;
    if (!this.isLoggedIn()) { bell.style.display = 'none'; return; }
    bell.style.display = '';
    try {
      const { count } = await NotifAPI.unreadCount();
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'flex';
      } else {
        badge.style.display = 'none';
      }
    } catch(e) { /* 后端未连接时隐藏 */ }
  },

  /** 更新首页侧边栏个人卡片 */
  updateSidebarCard(user) {
    const card = document.getElementById('sidebarUserCard');
    if (!card) return; // 非首页，没有这个元素

    if (user) {
      card.style.display = '';
      const avatar = document.getElementById('sidebarAvatar');
      const name   = document.getElementById('sidebarUsername');
      const role   = document.getElementById('sidebarRole');
      const bind   = document.getElementById('sidebarBindLink');

      if (avatar) avatar.textContent = (user.username || '?').charAt(0);
      if (name)   name.textContent  = user.username || '';

      if (role) {
        if (user.role === 'admin') {
          role.textContent = '🛡️ 管理员 · 全部权限';
        } else if (user.is_member === 1) {
          role.textContent = '✨ 会员 · 可发布和评论';
        } else {
          role.textContent = '📋 普通用户 · 仅浏览';
        }
      }
      if (bind) {
        bind.style.display = (user.role !== 'admin' && user.is_member !== 1) ? 'flex' : 'none';
      }
    } else {
      card.style.display = 'none';
    }
  },
};

/* 等待组件加载完成后更新UI */
document.addEventListener('components-loaded', () => Auth.updateUI());
/* DOMContentLoaded 也跑一次（兜底） */
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => Auth.updateUI(), 100);
});
