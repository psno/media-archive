// ==UserScript==
// @name         Media Archive - Cookie Extractor
// @namespace    https://github.com/psno/media-archive
// @version      1.1.0
// @description  一键提取各平台完整 Cookie（含 HttpOnly），用于 media-archive CLI 配置
// @author       psno
// @match        https://www.douban.com/*
// @match        https://movie.douban.com/*
// @match        https://www.bilibili.com/*
// @match        https://music.163.com/*
// @icon         data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234CAF50'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z'/%3E%3C/svg%3E
// @grant        GM_setClipboard
// @grant        GM_notification
// @grant        GM_cookie
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // 平台配置：每个平台提取哪些 cookie
    const PLATFORMS = {
        douban: {
            name: '豆瓣',
            urlPattern: /douban\.com/,
            // 需要的字段（其他字段也会一并保留）
            required: ['dbcl2', 'bid'],
            // 推荐保留的字段
            keep: ['dbcl2', 'bid', 'ck', 'll'],
        },
        bilibili: {
            name: 'Bilibili',
            urlPattern: /bilibili\.com/,
            required: ['SESSDATA', 'bili_jct'],
            keep: ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'buvid3'],
        },
        netease: {
            name: '网易云',
            urlPattern: /music\.163\.com/,
            required: ['MUSIC_U'],
            keep: ['MUSIC_U', '__csrf', '__remember_me', 'NMTID'],
        }
    };

    function detectPlatform() {
        for (const [key, info] of Object.entries(PLATFORMS)) {
            if (info.urlPattern.test(window.location.href)) return key;
        }
        return null;
    }

    // 读取完整 Cookie（包含 HttpOnly）
    // 优先用 GM_cookie（Tampermonkey 5.x 支持），fallback 到 document.cookie
    async function getAllCookies() {
        if (typeof GM_cookie !== 'undefined' && GM_cookie.list) {
            try {
                const cookies = await GM_cookie.list({ url: window.location.href });
                const result = {};
                cookies.forEach(c => {
                    result[c.name] = c.value;
                });
                return result;
            } catch (e) {
                console.warn('GM_cookie.list failed:', e);
            }
        }
        // Fallback：仅能读到非 HttpOnly
        return document.cookie.split(';').reduce((acc, c) => {
            const [k, ...v] = c.trim().split('=');
            if (k) acc[k.trim()] = v.join('=');
            return acc;
        }, {});
    }

    function buildCookieString(cookies, platform) {
        const info = PLATFORMS[platform];
        const parts = [];

        // 先添加 keep 列表中的字段
        for (const key of info.keep) {
            if (cookies[key]) {
                // dbcl2 需要加引号
                if (key === 'dbcl2') {
                    parts.push(`${key}="${cookies[key]}"`);
                } else {
                    parts.push(`${key}=${cookies[key]}`);
                }
            }
        }

        // 检查必需字段
        const missing = info.required.filter(k => !cookies[k]);
        return {
            cookie: parts.join('; '),
            missing: missing,
            hasAllRequired: missing.length === 0,
        };
    }

    function createPanel(platform, cookies) {
        const info = PLATFORMS[platform];
        const result = buildCookieString(cookies, platform);

        const panel = document.createElement('div');
        panel.id = 'media-archive-cookie-panel';
        panel.innerHTML = `
            <style>
                #media-archive-cookie-panel {
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    width: 360px;
                    max-height: 80vh;
                    overflow-y: auto;
                    background: #fff;
                    border-radius: 12px;
                    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    transition: all 0.3s ease;
                }
                #media-archive-cookie-panel.collapsed { display: none; }
                .ma-header {
                    padding: 12px 16px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: move;
                }
                .ma-title {
                    font-size: 14px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .ma-close, .ma-minimize {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 16px;
                    line-height: 1;
                    opacity: 0.85;
                    padding: 4px 8px;
                }
                .ma-close:hover, .ma-minimize:hover { opacity: 1; }
                .ma-body { padding: 16px; }
                .ma-status {
                    font-size: 12px;
                    padding: 8px 12px;
                    border-radius: 6px;
                    margin-bottom: 12px;
                }
                .ma-status.success { color: #2e7d32; background: #e8f5e9; }
                .ma-status.error { color: #c62828; background: #ffebee; }
                .ma-status.warning { color: #f57c00; background: #fff3e0; }
                .ma-cookie-display {
                    width: 100%;
                    min-height: 100px;
                    max-height: 200px;
                    padding: 8px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    font-size: 11px;
                    font-family: "SF Mono", Monaco, monospace;
                    background: #f8f9fa;
                    color: #333;
                    resize: vertical;
                    margin-bottom: 12px;
                    word-break: break-all;
                    overflow-wrap: break-word;
                }
                .ma-btn-row { display: flex; gap: 8px; margin-bottom: 12px; }
                .ma-btn {
                    flex: 1;
                    padding: 10px;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .ma-btn-copy {
                    background: #667eea;
                    color: white;
                }
                .ma-btn-copy:hover { background: #5a6fd6; }
                .ma-btn-copy.copied { background: #4CAF50; }
                .ma-btn-refresh {
                    background: #f0f0f0;
                    color: #333;
                }
                .ma-btn-refresh:hover { background: #e0e0e0; }
                .ma-cookie-list {
                    background: #f8f9fa;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 11px;
                    margin-bottom: 12px;
                }
                .ma-cookie-list-title {
                    font-weight: 600;
                    margin-bottom: 6px;
                    color: #333;
                }
                .ma-cookie-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 2px 0;
                    color: #666;
                    font-family: monospace;
                }
                .ma-cookie-item.missing { color: #c62828; }
                .ma-cookie-key { font-weight: 500; }
                .ma-cookie-val {
                    color: #999;
                    max-width: 180px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .ma-tips {
                    font-size: 11px;
                    color: #999;
                    padding: 8px;
                    background: #f5f5f5;
                    border-radius: 6px;
                    line-height: 1.5;
                }
                .ma-tips code {
                    background: #e3f2fd;
                    padding: 1px 4px;
                    border-radius: 3px;
                    color: #1565c0;
                }
            </style>

            <div class="ma-header">
                <div class="ma-title">
                    <span>📦</span>
                    <span>${info.name} Cookie 提取器</span>
                </div>
                <div>
                    <button class="ma-minimize" title="最小化">−</button>
                    <button class="ma-close" title="关闭">×</button>
                </div>
            </div>
            <div class="ma-body">
                <div class="ma-status ${result.hasAllRequired ? 'success' : 'error'}">
                    ${result.hasAllRequired
                        ? '✓ 检测到完整登录态'
                        : '✗ 缺少必需字段: ' + result.missing.join(', ')}
                </div>

                <div class="ma-cookie-list">
                    <div class="ma-cookie-list-title">检测到的 Cookie 字段：</div>
                    ${info.keep.map(k => {
                        const has = !!cookies[k];
                        const val = has ? cookies[k].substring(0, 30) + (cookies[k].length > 30 ? '...' : '') : '未找到';
                        return `<div class="ma-cookie-item ${has ? '' : 'missing'}">
                            <span class="ma-cookie-key">${k}</span>
                            <span class="ma-cookie-val">${val}</span>
                        </div>`;
                    }).join('')}
                </div>

                <textarea class="ma-cookie-display" readonly>${result.cookie || '（无有效 Cookie）'}</textarea>

                <div class="ma-btn-row">
                    <button class="ma-btn ma-btn-copy" ${!result.cookie ? 'disabled' : ''}>
                        📋 复制 Cookie
                    </button>
                    <button class="ma-btn ma-btn-refresh">
                        🔄 重新读取
                    </button>
                </div>

                <div class="ma-tips">
                    <strong>使用方法：</strong><br>
                    1. 复制上面的 Cookie 字符串<br>
                    2. 在终端运行：<br>
                    <code>media-archive cred --platform ${platform}</code><br>
                    3. 粘贴 Cookie 并回车<br>
                    <br>
                    <strong>提示：</strong>如果显示"缺少必需字段"，请先在当前网站登录账号后刷新页面。
                </div>
            </div>
        `;

        document.body.appendChild(panel);

        // 绑定事件
        panel.querySelector('.ma-close').onclick = () => panel.remove();
        panel.querySelector('.ma-minimize').onclick = () => panel.classList.toggle('collapsed');

        const copyBtn = panel.querySelector('.ma-btn-copy');
        const refreshBtn = panel.querySelector('.ma-btn-refresh');

        copyBtn.onclick = () => {
            const text = panel.querySelector('.ma-cookie-display').value;
            if (!text || text.startsWith('（')) return;
            if (typeof GM_setClipboard !== 'undefined') {
                GM_setClipboard(text);
            } else {
                panel.querySelector('.ma-cookie-display').select();
                document.execCommand('copy');
            }
            copyBtn.textContent = '✓ 已复制';
            copyBtn.classList.add('copied');
            setTimeout(() => {
                copyBtn.textContent = '📋 复制 Cookie';
                copyBtn.classList.remove('copied');
            }, 2000);
            if (typeof GM_notification !== 'undefined') {
                GM_notification({
                    title: 'Media Archive',
                    text: `${info.name} Cookie 已复制！\n运行：media-archive cred --platform ${platform}`,
                    timeout: 4000
                });
            }
        };

        refreshBtn.onclick = async () => {
            panel.remove();
            const freshCookies = await getAllCookies();
            createPanel(platform, freshCookies);
        };

        // 拖拽
        makeDraggable(panel, panel.querySelector('.ma-header'));
    }

    function makeDraggable(element, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        handle.onmousedown = (e) => {
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = () => {
                document.onmouseup = null;
                document.onmousemove = null;
            };
            document.onmousemove = (e) => {
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                element.style.top = (element.offsetTop - pos2) + 'px';
                element.style.right = 'auto';
                element.style.left = (element.offsetLeft - pos1) + 'px';
            };
        };
    }

    // ── 初始化 ──────────────────────────────────────────────────────

    const platform = detectPlatform();
    if (!platform) return;

    if (document.getElementById('media-archive-cookie-panel')) return;

    getAllCookies().then(cookies => {
        createPanel(platform, cookies);
    });
})();
