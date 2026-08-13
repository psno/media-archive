// ==UserScript==
// @name         Media Archive - Cookie Extractor
// @namespace    https://github.com/psno/media-archive
// @version      1.0.0
// @description  一键提取各平台 Cookie，支持复制到剪贴板，用于 media-archive CLI 配置
// @author       psno
// @match        https://www.douban.com/*
// @match        https://movie.douban.com/*
// @match        https://www.bilibili.com/*
// @match        https://music.163.com/*
// @icon         data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%234CAF50'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z'/%3E%3C/svg%3E
// @grant        GM_setClipboard
// @grant        GM_notification
// @connect      github.com
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // ── 通用 UI 构建 ───────────────────────────────────────────────

    function createPanel() {
        const panel = document.createElement('div');
        panel.id = 'media-archive-cookie-extractor';
        panel.innerHTML = `
            <style>
                #media-archive-cookie-extractor {
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    width: 320px;
                    background: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }
                #media-archive-cookie-extractor.collapsed {
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    cursor: pointer;
                }
                .ma-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 12px 16px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .ma-title {
                    font-size: 14px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .ma-title svg {
                    width: 18px;
                    height: 18px;
                }
                .ma-close {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 18px;
                    line-height: 1;
                    padding: 0;
                    opacity: 0.8;
                    transition: opacity 0.2s;
                }
                .ma-close:hover {
                    opacity: 1;
                }
                .ma-body {
                    padding: 16px;
                }
                .ma-platform {
                    margin-bottom: 16px;
                }
                .ma-platform:last-child {
                    margin-bottom: 0;
                }
                .ma-platform-name {
                    font-size: 12px;
                    font-weight: 600;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }
                .ma-cookie-row {
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }
                .ma-cookie-input {
                    flex: 1;
                    height: 36px;
                    padding: 0 12px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    font-size: 12px;
                    font-family: "SF Mono", Monaco, monospace;
                    color: #333;
                    background: #f8f9fa;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .ma-cookie-input:focus {
                    outline: none;
                    border-color: #667eea;
                    background: white;
                }
                .ma-btn {
                    height: 36px;
                    padding: 0 16px;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    white-space: nowrap;
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
                .ma-btn-extract {
                    background: #f0f0f0;
                    color: #333;
                }
                .ma-btn-extract:hover {
                    background: #e0e0e0;
                }
                .ma-status {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    font-size: 11px;
                    padding: 2px 8px;
                    border-radius: 10px;
                    margin-left: auto;
                }
                .ma-status.logged-in {
                    background: #e8f5e9;
                    color: #2e7d32;
                }
                .ma-status.not-logged-in {
                    background: #ffebee;
                    color: #c62828;
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
                .ma-footer a:hover {
                    text-decoration: underline;
                }
                .ma-toggle {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                    display: none;
                    align-items: center;
                    justify-content: center;
                    z-index: 999998;
                    font-size: 20px;
                }
                .ma-toggle.show {
                    display: flex;
                }
                .ma-toggle:hover {
                    transform: scale(1.1);
                }
                .ma-checklist {
                    margin-top: 12px;
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    font-size: 12px;
                }
                .ma-checklist-title {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 8px;
                }
                .ma-checklist-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 4px 0;
                    color: #666;
                }
                .ma-checklist-item svg {
                    width: 14px;
                    height: 14px;
                    flex-shrink: 0;
                }
            </style>

            <div class="ma-header">
                <div class="ma-title">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z"/></svg>
                    Media Archive
                </div>
                <button class="ma-close" onclick="this.closest('#media-archive-cookie-extractor').style.display='none';document.querySelector('.ma-toggle').classList.add('show')">×</button>
            </div>
            <div class="ma-body">
                <div id="ma-content"></div>
                <div class="ma-checklist">
                    <div class="ma-checklist-title">配置步骤：</div>
                    <div class="ma-checklist-item">
                        <svg viewBox="0 0 24 24" fill="#4CAF50"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                        确保已登录目标网站
                    </div>
                    <div class="ma-checklist-item">
                        <svg viewBox="0 0 24 24" fill="#4CAF50"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                        点击「提取 Cookie」获取当前会话
                    </div>
                    <div class="ma-checklist-item">
                        <svg viewBox="0 0 24 24" fill="#4CAF50"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                        复制后运行：media-archive cred --platform <平台名>
                    </div>
                    <div class="ma-checklist-item">
                        <svg viewBox="0 0 24 24" fill="#4CAF50"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                        粘贴 Cookie 并回车
                    </div>
                </div>
            </div>
            <div class="ma-footer">
                <a href="https://github.com/psno/media-archive" target="_blank">GitHub</a> · 仅供个人数据备份使用
            </div>
        `;

        document.body.appendChild(panel);
        updatePlatformStatus();
    }

    function showToggle() {
        let toggle = document.querySelector('.ma-toggle');
        if (!toggle) {
            toggle = document.createElement('button');
            toggle.className = 'ma-toggle show';
            toggle.innerHTML = '📦';
            toggle.onclick = () => {
                const panel = document.getElementById('media-archive-cookie-extractor');
                if (panel) {
                    panel.style.display = 'block';
                    toggle.classList.remove('show');
                }
            };
            document.body.appendChild(toggle);
        }
    }

    function updatePlatformStatus() {
        const content = document.getElementById('ma-content');
        if (!content) return;

        const cookies = document.cookie.split(';').reduce((acc, c) => {
            const [k, ...v] = c.trim().split('=');
            acc[k.trim()] = v.join('=');
            return acc;
        }, {});

        const platforms = [
            {
                name: '豆瓣',
                key: 'douban',
                check: ['dbcl2', 'bid'],
                sample: cookies['dbcl2'] ? `dbcl2="${cookies['dbcl2']}"` : null
            },
            {
                name: 'Bilibili',
                key: 'bilibili',
                check: ['SESSDATA', 'bili_jct'],
                sample: cookies['SESSDATA'] ? `SESSDATA=${cookies['SESSDATA']}; bili_jct=${cookies['bili_jct']}` : null
            },
            {
                name: '网易云',
                key: 'netease',
                check: ['MUSIC_U'],
                sample: cookies['MUSIC_U'] ? `MUSIC_U=${cookies['MUSIC_U']}; __csrf=${cookies['__csrf'] || ''}` : null
            }
        ];

        content.innerHTML = platforms.map(p => {
            const hasAll = p.check.every(k => cookies[k]);
            const statusClass = hasAll ? 'logged-in' : 'not-logged-in';
            const statusText = hasAll ? '✓ 已登录' : '✗ 未登录';

            return `
                <div class="ma-platform">
                    <div class="ma-platform-name">${p.name}</div>
                    <div class="ma-cookie-row">
                        <input type="text" class="ma-cookie-input" id="ma-cookie-${p.key}"
                            value="${hasAll ? p.sample || '' : ''}"
                            readonly
                            placeholder="未提取到 Cookie...">
                        <button class="ma-btn ma-btn-copy" id="ma-copy-${p.key}"
                            onclick="copyCookie('${p.key}', '${p.name}')">
                            复制
                        </button>
                    </div>
                    <span class="ma-status ${statusClass}">${statusText}</span>
                </div>
            `;
        }).join('');
    }

    window.copyCookie = function(key, platformName) {
        const input = document.getElementById(`ma-cookie-${key}`);
        const btn = document.getElementById(`ma-copy-${key}`);
        if (!input || !input.value) return;

        // 使用 GM_setClipboard 或 fallback
        if (typeof GM_setClipboard !== 'undefined') {
            GM_setClipboard(input.value);
        } else {
            input.select();
            document.execCommand('copy');
        }

        btn.textContent = '✓ 已复制';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = '复制';
            btn.classList.remove('copied');
        }, 2000);

        // 显示提示
        const msg = `已复制 ${platformName} Cookie！\n\n运行命令：\nmedia-archive cred --platform ${key}`;
        if (typeof GM_notification !== 'undefined') {
            GM_notification({
                title: 'Media Archive',
                text: msg,
                timeout: 5000
            });
        } else {
            alert(msg);
        }
    };

    // ── 初始化 ──────────────────────────────────────────────────────

    const existing = document.getElementById('media-archive-cookie-extractor');
    if (!existing) {
        createPanel();
    }

    // 如果面板被关闭，显示浮动按钮
    const observer = new MutationObserver(() => {
        const panel = document.getElementById('media-archive-cookie-extractor');
        if (panel && panel.style.display === 'none') {
            showToggle();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

})();
