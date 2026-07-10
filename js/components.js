/**
 * 公共组件加载器
 * 修改 components/ 目录下的文件，全站自动同步更新
 *
 * 用法：在页面中放置 <div data-component="header"></div> 即可自动加载
 *
 * 注意：需通过 http:// 访问（不要直接用 file:// 打开）
 *       运行 start-server.bat 启动本地服务器
 */
(async function loadComponents() {
  const placeholders = document.querySelectorAll('[data-component]');

  for (const el of placeholders) {
    const name = el.dataset.component;
    let html = '';

    // 方式1: fetch (适用于 http://)
    try {
      const resp = await fetch(`components/${name}.html`);
      if (resp.ok) {
        html = await resp.text();
      }
    } catch (_) {
      // fetch 在 file:// 协议下会失败，尝试 XHR 回退
    }

    // 方式2: XMLHttpRequest 回退 (兼容 file://)
    if (!html) {
      try {
        html = await new Promise((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open('GET', `components/${name}.html`, false); // 同步模式兼容 file://
          try {
            xhr.send();
            if (xhr.status === 0 || xhr.status === 200) {
              resolve(xhr.responseText);
            } else {
              reject(new Error(`XHR status ${xhr.status}`));
            }
          } catch (e) {
            reject(e);
          }
        });
      } catch (_) {}
    }

    if (html) {
      el.innerHTML = html;
      // 重新执行内联脚本（如果有的话）
      const scripts = el.querySelectorAll('script');
      scripts.forEach(old => {
        const s = document.createElement('script');
        s.textContent = old.textContent;
        old.replaceWith(s);
      });
    } else {
      // 最终回退：显示简易顶栏
      el.innerHTML = getFallbackHTML(name);
    }
  }

  // 通知其他脚本：组件已加载完毕
  document.dispatchEvent(new CustomEvent('components-loaded'));
})();

function getFallbackHTML(name) {
  if (name === 'header') {
    return `<header class="header">
      <div class="header-inner">
        <a href="index.html" class="logo">实习<span>通</span></a>
        <div class="search-box"><input type="search" placeholder="搜索..."></div>
        <a href="publish.html" class="btn-post">📤 发布</a>
        <a href="login.html" class="btn-login">登录</a>
      </div>
    </header>`;
  }
  if (name === 'footer') {
    return `<footer style="background:#fff;border-top:1px solid #e5e7eb;padding:24px;text-align:center;font-size:13px;color:#9ca3af;margin-top:48px">
      &copy; 2026 实习通 · H5响应式
    </footer>`;
  }
  return '';
}
