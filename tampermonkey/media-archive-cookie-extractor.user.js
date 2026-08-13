// ==UserScript==
// @name         Media Archive - Cookie Extractor
// @namespace    https://github.com/psno/media-archive
// @version      1.0.0
// @description  一键提取各平台 Cookie，用于 media-archive CLI 配置
// @author       psno
// @match        https://www.douban.com/*
// @match        https://movie.douban.com/*
// @match        https://www.bilibili.com/*
// @match        https://music.163.com/*
// @icon         data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234CAF50'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z'/%3E%3C/svg%3E
// @grant        GM_setClipboard
// @grant        GM_notification
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // 获取当前域名的 Cookie
    function getCookies() {
        return document.cookie.split(';').reduce((acc, c) => {
            const [k, ...v] = c.trim().split('=');
            acc[k.trim()] = v.join('=');
            return acc;
        }, {});
    }

    // 判断当前平台
    function getPlatform() {
        const url = window.location.href;
        if (url.includes('douban.com')) return 'douban';
        if (url.includes('bilibili.com')) return 'bilibili';
        if (url.includes('music.163.com')) return 'netease';
        return null;
    }

    // 创建浮窗
    function createPanel() {
        const platform = getPlatform();
        if (!platform) return;

        const cookies = getCookies();
        let cookieValue = '';
        let instructions = '';

        switch (platform) {
            case 'douban':
                // 豆瓣需要 dbcl2 和 bid
                if (cookies['dbcl2'] && cookies['bid']) {
                    cookieValue = `bid=${cookies['bid']}; dbcl2="${cookies['dbcl2']}"`;
                    instructions = '豆瓣 Cookie 已提取';
                } else {
                    instructions = '未检测到登录态，请先登录';
                }
                break;
            case 'bilibili':
                // B站需要 SESSDATA 和 bili_jct
                if (cookies['SESSDATA'] && cookies['bili_jct']) {
                    cookieValue = `SESSDATA=${cookies['SESSDATA']}; bili_jct=${cookies['bili_jct']}`;
                    instructions = 'B站 Cookie 已提取';
                } else {
                    instructions = '未检测到登录态，请先登录';
                }
                break;
            case 'netease':
                // 网易云需要 MUSIC_U 和 __csrf
                if (cookies['MUSIC_U']) {
                    cookieValue = `MUSIC_U=${cookies['MUSIC_U']}; __csrf=${cookies['__csrf'] || ''}`;
                    instructions = '网易云 Cookie 已提取';
                } else {
                    instructions = '未检测到登录态，请先登录';
                }
                break;
        }

        // 创建浮窗元素
        const panel = document.createElement('div');
        panel.id = 'media-archive-cookie-panel';
        panel.innerHTML = `
            <style>
                #media-archive-cookie-panel {
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    width: 300px;
                    background: #fff;
                    border-radius: 12px;
                    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    overflow: hidden;
                }
                .ma-header {
                    padding: 12px 16px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .ma-title {
                    font-size: 14px;
                    font-weight: 600;
                }
                .ma-close {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 18px;
                    line-height: 1;
                }
                .ma-body {
                    padding: 16px;
                }
                .ma-status {
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 12px;
                    padding: 8px;
                    background: #f5f5f5;
                    border-radius: 6px;
                }
                .ma-status.success {
                    color: #2e7d32;
                    background: #e8f5e9;
                }
                .ma-status.error {
                    color: #c62828;
                    background: #ffebee;
                }
                .ma-cookie-display {
                    width: 100%;
                    height: 80px;
                    padding: 8px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    font-size: 11px;
                    font-family: monospace;
                    resize: none;
                    background: #f8f9fa;
                    color: #333;
                    margin-bottom: 12px;
                }
                .ma-btn {
                    width: 100%;
                    padding: 10px;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .ma-btn-copy {
                    background: #667eea;
                    color: white;
                }
                .ma-btn-copy:hover {
                    background: #5a6fd6;
                }
                .ma-btn-copy.copied {
                    background: #4CAF50;
                }
                .ma-footer {
                    padding: 12px 16px;
                    border-top: 1px solid #eee;
                    font-size: 11px;
                    color: #999;
                    text-align: center;
                }
                .ma-footer a {
                    color: #667eea;
                    text-decoration: none;
                }
                .ma-config-steps {
                    margin-top: 12px;
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    font-size: 12px;
                }
                .ma-config-steps-title {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 8px;
                }
                .ma-step {
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    padding: 4px 0;
                    color: #666;
                }
                .ma-step-num {
                    width: 18px;
                    height: 18px;
                    border-radius: 50%;
                    background: #667eea;
                    color: white;
                    font-size: 11px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }
                .ma-step-code {
                    font-family: monospace;
                    background: #e3f2fd;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 11px;
                    color: #1565c0;
                }
            </style>

            <div class="ma-header">
                <div class="ma-title">📦 Media Archive</div>
                <button class="ma-close" onclick="this.closest('#media-archive-cookie-panel').remove()">×</button>
            </div>
            <div class="ma-body">
                <div class="ma-status ${cookieValue ? 'success' : 'error'}">
                    ${instructions}
                </div>
                <textarea class="ma-cookie-display" readonly>${cookieValue || '暂无数据'}</textarea>
                <button class="ma-btn ma-btn-copy" onclick="copyCookie()" ${!cookieValue ? 'disabled' : ''}>
                    📋 复制 Cookie
                </button>
                <div class="ma-config-steps">
                    <div class="ma-config-steps-title">配置 CLI：</div>
                    <div class="ma-step">
                        <div class="ma-step-num">1</div>
                        <div>粘贴 Cookie 后运行：
                            <code class="ma-step-code">media-archive cred --platform ${platform}</code>
                        </div>
                    </div>
                    <div class="ma-step">
                        <div class="ma-step-num">2</div>
                        <div>在终端中粘贴并回车</div>
                    </div>
                    <div class="ma-step">
                        <div class="ma-step-num">3</div>
                        <div>运行 <code class="ma-step-code">media-archive fetch</code> 开始抓取</div>
                    </div>
                </div>
            </div>
            <div class="ma-footer">
                <a href="https://github.com/psno/media-archive" target="_blank">GitHub 文档</a> · 仅供个人数据备份使用
            </div>
        `;

        document.body.appendChild(panel);

        // 点击外部关闭
        setTimeout(() => {
            document.addEventListener('click', function handler(e) {
                if (!panel.contains(e.target)) {
                    panel.remove();
                    document.removeEventListener('click', handler);
                }
            });
        }, 100);
    }

    // 复制 Cookie
    window.copyCookie = function() {
        const textarea = document.querySelector('.ma-cookie-display');
        const btn = document.querySelector('.ma-btn-copy');
        if (!textarea || !btn) return;

        const text = textarea.value;
        if (!text || text === '暂无数据') return;

        // 尝试使用 GM_setClipboard
        if (typeof GM_setClipboard !== 'undefined') {
            GM_setClipboard(text);
        } else {
            // Fallback
            textarea.select();
            document.execCommand('copy');
        }

        // 更新按钮状态
        btn.textContent = '✓ 已复制到剪贴板';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = '📋 复制 Cookie';
            btn.classList.remove('copied');
        }, 2000);

        // 显示通知
        const platform = getPlatform();
        if (typeof GM_notification !== 'undefined') {
            GM_notification({
                title: 'Media Archive',
                text: `${platform} Cookie 已复制！\n请运行：media-archive cred --platform ${platform}`,
                timeout: 5000
            });
        }
    };

    // 初始化
    createPanel();
})();
