# Media Archive

命令行工具，用于从豆瓣、Bilibili、网易云音乐三个平台提取个人媒体数据，保存到本地 SQLite 数据库，支持 JSON/CSV 导出。专为 AI Agent（Hermes、OpenCode 等）设计，可直接被调用。

## 功能

| 平台 | 数据 | 说明 |
|------|------|------|
| 豆瓣 | 看过的影视 | 标题、评分、日期、链接 |
| Bilibili | 追番-看过 | 标题、封面、进度、链接 |
| 网易云 | 我喜欢 | 歌曲名、歌手、专辑、时长 |
| 网易云 | 听歌排行 | 歌曲名、歌手、播放次数、得分 |

## 安装

```bash
# 方式1: pip 安装（推荐）
pip install -e .

# 方式2: uv
uv pip install -e .
```

## 配置凭证

每个平台需要登录 Cookie。获取方式：

### 豆瓣
1. 浏览器登录 https://www.douban.com
2. F12 → Network → 刷新页面 → 点击第一个请求
3. 复制 `Cookie:` 行全部内容

```bash
media-archive cred --platform douban
# 粘贴 Cookie
```

### Bilibili
1. 浏览器登录 https://www.bilibili.com
2. F12 → Application → Cookies → `www.bilibili.com`
3. 复制 `SESSDATA` 和 `bili_jct` 值，用分号拼接

```bash
media-archive cred --platform bilibili
```

### 网易云音乐
1. 浏览器登录 https://music.163.com
2. F12 → Network → 复制 Cookie（需要包含 `MUSIC_U` 和 `__csrf`）

```bash
media-archive cred --platform netease
```

## 使用

```bash
# 查看状态
media-archive status

# 抓取所有平台
media-archive fetch

# 单独抓取某个平台
media-archive fetch-douban
media-archive fetch-bilibili
media-archive fetch-netease

# 限制数量（0 = 全部）
media-archive fetch --limit 50

# 导出数据
media-archive export --format json   # 输出到 ~/.media_archive/media_archive.json
media-archive export --format csv    # 输出到 ~/.media_archive/media_archive.csv

# 查看配置
media-archive show

# 清除凭证
media-archive clear --platform douban
media-archive clear                 # 清除全部
```

## 数据格式

JSON 输出示例：
```json
{
  "douban": [
    {
      "title": "电影名称",
      "url": "https://movie.douban.com/subject/xxxx/",
      "rating": "9.7",
      "date": "2024-01-15",
      "platform": "douban",
      "type": "movie",
      "status": "watched"
    }
  ],
  "bilibili": [...],
  "netease": {
    "liked": [...],
    "play_history": [...]
  }
}
```

## 架构

```
~/.media_archive_creds.json   # 凭证（自动 chmod 600）
~/.media_archive/archive.db   # SQLite 数据库
```

## 注意事项

- Cookie 会过期（通常 30 天），失效后需重新登录获取
- 各平台有反爬机制，批量抓取时请控制频率
- 本工具仅供个人数据备份使用

## 开源协议

MIT
