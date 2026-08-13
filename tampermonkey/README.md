# Media Archive - Tampermonkey 配套脚本

## 安装方式

1. 安装 [Tampermonkey](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) 或类似浏览器扩展
2. 下载或复制 `media-archive-cookie-extractor.user.js` 内容
3. 在 Tampermonkey 中创建新脚本，粘贴内容并保存

## 使用步骤

### 1. 打开目标网站并确保已登录

| 平台 | 网址 |
|------|------|
| 豆瓣 | https://www.douban.com |
| Bilibili | https://www.bilibili.com |
| 网易云音乐 | https://music.163.com |

### 2. 提取 Cookie

页面右侧会自动出现 **Media Archive** 浮窗，显示当前平台的 Cookie 状态：
- ✓ 绿色：已登录，Cookie 已提取
- ✗ 红色：未检测到登录态

点击「复制 Cookie」按钮将 Cookie 复制到剪贴板。

### 3. 配置到 CLI

打开终端，运行以下命令：

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

### 4. 开始抓取

```bash
# 抓取所有平台
media-archive fetch

# 或单独抓取某个平台
media-archive fetch-douban
media-archive fetch-bilibili
media-archive fetch-netease
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
- 如果浮窗未显示，刷新页面或检查 Tampermonkey 是否启用

## 手动获取 Cookie（备选方案）

如果油猴脚本无法正常工作，可以手动获取：

1. 打开浏览器开发者工具（F12）
2. 进入 Network 标签，刷新页面
3. 点击任意一个请求，查看 Request Headers
4. 复制 `Cookie:` 行全部内容
5. 粘贴到 media-archive 的 cred 命令中
