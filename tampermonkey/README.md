# Media Archive - Tampermonkey 配套脚本

## 安装方式

1. 安装 [Tampermonkey](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) 浏览器扩展
2. 下载 `media-archive-cookie-extractor.user.js`
3. 在 Tampermonkey 中创建新脚本，粘贴内容并保存

## 使用步骤

### 1. 打开目标网站并确保已登录

| 平台 | 网址 |
|------|------|
| 豆瓣 | https://www.douban.com |
| Bilibili | https://www.bilibili.com |
| 网易云音乐 | https://music.163.com |

### 2. 提取 Cookie

页面右侧会自动出现 **Media Archive** 浮窗，显示各平台登录状态：
- ✓ 已登录（绿色）
- ✗ 未登录（红色）

点击「复制」按钮即可将 Cookie 复制到剪贴板。

### 3. 配置到 CLI

```bash
# 豆瓣
media-archive cred --platform douban
# 粘贴 Cookie → 回车

# Bilibili
media-archive cred --platform bilibili
# 粘贴 Cookie → 回车

# 网易云
media-archive cred --platform netease
# 粘贴 Cookie → 回车
```

## 支持的 Cookie 字段

| 平台 | 必需字段 | 说明 |
|------|----------|------|
| 豆瓣 | `dbcl2`, `bid` | `dbcl2` 包含用户ID |
| Bilibili | `SESSDATA`, `bili_jct` | 登录态凭据 |
| 网易云 | `MUSIC_U`, `__csrf` | `MUSIC_U` 为加密的用户ID |

## 注意事项

- 脚本仅在上述三个平台域名下生效
- Cookie 有效期约 30 天，过期后需重新登录提取
- 请勿将 Cookie 分享给他人，以免账号被盗
- 本脚本仅读取 `document.cookie`，不会上传任何数据
