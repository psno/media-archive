# Media Archive - Tampermonkey 配套脚本

## 关键说明

油猴脚本中 `document.cookie` **无法读取 HttpOnly Cookie**（这是浏览器安全策略，所有网站都这样）。所以脚本做了以下处理：

1. **优先使用 `GM_cookie.list()`**（Tampermonkey 5.x+ 的实验性 API）读取完整 Cookie
2. **如果没有 GM_cookie**，会回退到 `document.cookie`，此时只能读取非 HttpOnly 字段
3. **明确告知用户缺少哪些必需字段**

## 安装方式

### 方式一：Tampermonkey 5.x+（推荐）

支持 `GM_cookie` API，可读取 HttpOnly Cookie。

1. 安装 [Tampermonkey Beta](https://chrome.google.com/webstore/detail/tampermonkey-beta/cgddlpjdbgkmabifnlfhgblgldjclmah) 或 Tampermonkey 5.x+
2. 创建新脚本，粘贴 `media-archive-cookie-extractor.user.js` 内容
3. 保存并启用

### 方式二：传统 Tampermonkey

`GM_cookie` 不可用时，回退到 `document.cookie`。此时可能无法读取 HttpOnly 字段（如 `SESSDATA`、豆瓣 `dbcl2` 等），需要用 CLI 的二维码登录功能：

```bash
# 网易云/B站 - 二维码登录
media-archive login --platform netease
media-archive login --platform bilibili
```

## 使用流程

### 推荐流程（无需油猴脚本）

**B站和网易云**直接用二维码登录：
```bash
media-archive login --platform netease   # 终端显示二维码，手机APP扫码
media-archive login --platform bilibili  # 终端显示二维码，手机APP扫码
```

**豆瓣**没有官方二维码登录，需要在浏览器登录后用油猴脚本提取。

### 油猴脚本流程

1. 在浏览器打开目标网站并登录
2. 页面右侧会出现「Cookie 提取器」浮窗
3. 浮窗会显示检测到的 Cookie 字段（绿色=已找到，红色=缺失）
4. 点击「📋 复制 Cookie」按钮
5. 终端运行 `media-archive cred --platform <平台>` 并粘贴

## 各平台必需 Cookie 字段

| 平台 | 必需字段 | 是否 HttpOnly |
|------|----------|---------------|
| 豆瓣 | `dbcl2`, `bid` | `dbcl2` 是 HttpOnly |
| Bilibili | `SESSDATA`, `bili_jct` | `SESSDATA` 是 HttpOnly |
| 网易云 | `MUSIC_U`, `__csrf` | `MUSIC_U` 是 HttpOnly |

**这就是为什么油猴脚本的 `document.cookie` 读不到！** 这些关键字段都是 HttpOnly 标记的。

## 解决方案对比

| 方式 | 优点 | 缺点 |
|------|------|------|
| CLI 二维码登录（Netease/B站） | 完整可靠，自动获取 HttpOnly | 豆瓣不支持 |
| 油猴脚本 + GM_cookie | 一次配置，无限复用 | 需要 Tampermonkey 5.x+ |
| 油猴脚本 + document.cookie | 兼容性好 | 读不到 HttpOnly，可能失败 |
| 手动复制（F12 → Network → Cookie） | 100% 可靠 | 操作繁琐 |

## 推荐组合

- **B站** → `media-archive login --platform bilibili`（二维码）
- **网易云** → `media-archive login --platform netease`（二维码）
- **豆瓣** → 油猴脚本提取（用 GM_cookie 模式）
