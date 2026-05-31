"""Blog API Mock Server - 异步高性能版 (aiohttp)"""
import json
import time
import hashlib
import asyncio
import threading
import logging
from aiohttp import web
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ─── 模拟数据 ─────────────────────────────────────────────────────────────────

_users: Dict[int, Dict] = {
    1: {
        "id": 1, "account": "admin", "nickName": "管理员",
        "password": "abc123", "salt": "random-salt",
        "email": "admin@blog.com", "avatar": "https://api.dicebear.com/avatar/admin",
        "status": "1", "admin": True, "createDate": 1622505600000,
        "lastLogin": 1622592000000, "mobilePhoneNumber": "13800138000"
    },
    2: {
        "id": 2, "account": "tester", "nickName": "测试用户",
        "password": "123456", "salt": "test-salt",
        "email": "tester@blog.com", "avatar": "https://api.dicebear.com/avatar/tester",
        "status": "1", "admin": False, "createDate": 1622592000000,
        "lastLogin": 1622678400000, "mobilePhoneNumber": "13900139000"
    },
}
_next_user_id = 3

_articles: Dict[int, Dict] = {
    1: {
        "id": 1, "title": "Spring Boot 入门指南", "summary": "本文介绍 Spring Boot 基础用法",
        "viewCounts": 1024, "commentCounts": 15, "weight": 1,
        "authorId": 1, "bodyId": 101, "categoryId": 1,
        "createDate": "2024-01-15T10:00:00",
        "tags": [{"id": 1, "tagName": "Spring"}, {"id": 2, "tagName": "Java"}],
        "category": {"id": 1, "categoryName": "技术", "avatar": ""}
    },
    2: {
        "id": 2, "title": "MyBatis Plus 实战总结", "summary": "MyBatis Plus 常用功能汇总",
        "viewCounts": 856, "commentCounts": 8, "weight": 0,
        "authorId": 1, "bodyId": 102, "categoryId": 1,
        "createDate": "2024-01-20T14:30:00",
        "tags": [{"id": 1, "tagName": "MyBatis"}, {"id": 3, "tagName": "ORM"}],
        "category": {"id": 1, "categoryName": "技术", "avatar": ""}
    },
    3: {
        "id": 3, "title": "Docker 从入门到实践", "summary": "Docker 容器化部署指南",
        "viewCounts": 2341, "commentCounts": 22, "weight": 1,
        "authorId": 2, "bodyId": 103, "categoryId": 2,
        "createDate": "2024-02-01T09:15:00",
        "tags": [{"id": 4, "tagName": "Docker"}, {"id": 5, "tagName": "DevOps"}],
        "category": {"id": 2, "categoryName": "DevOps", "avatar": ""}
    },
}
_next_article_id = 4

_tags: Dict[int, Dict] = {
    1: {"id": 1, "tagName": "Spring", "avatar": "https://api.dicebear.com/tag/spring"},
    2: {"id": 2, "tagName": "Java", "avatar": "https://api.dicebear.com/tag/java"},
    3: {"id": 3, "tagName": "MyBatis", "avatar": "https://api.dicebear.com/tag/mybatis"},
    4: {"id": 4, "tagName": "Docker", "avatar": "https://api.dicebear.com/tag/docker"},
    5: {"id": 5, "tagName": "DevOps", "avatar": "https://api.dicebear.com/tag/devops"},
}

_categories: Dict[int, Dict] = {
    1: {"id": 1, "categoryName": "技术", "avatar": "", "description": "技术文章"},
    2: {"id": 2, "categoryName": "DevOps", "avatar": "", "description": "DevOps 文章"},
    3: {"id": 3, "categoryName": "随笔", "avatar": "", "description": "随笔感想"},
}

_comments: Dict[int, Dict] = {
    1: {"id": 1, "content": "写得很好，收藏了！", "articleId": 1, "authorId": 2,
        "createDate": "2024-01-16T08:00:00", "username": "tester", "toUserId": None, "parent": None},
    2: {"id": 2, "content": "请问有源码吗？", "articleId": 1, "authorId": 2,
        "createDate": "2024-01-17T10:00:00", "username": "tester", "toUserId": 1, "parent": None},
}
_next_comment_id = 3

_tokens: Dict[str, Dict] = {}  # token -> user info


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def success(data: Any = None) -> Dict:
    return {"success": True, "code": 200, "msg": "success", "data": data}

def fail(code: int, msg: str) -> Dict:
    return {"success": False, "code": code, "msg": msg, "data": None}

def get_token(request: web.Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    return auth[7:] if auth.startswith("Bearer ") else None

def authenticate(request: web.Request) -> Optional[Dict]:
    token = get_token(request)
    return _tokens.get(token)

def json_response(data: Any, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


# ─── Handlers ─────────────────────────────────────────────────────────────────

async def handle_login(request: web.Request) -> web.Response:
    body = await request.json()
    account, password = body.get("account", ""), body.get("password", "")
    for user in _users.values():
        if user["account"] == account:
            if user["password"] == password:
                token = f"blog_token_{int(time.time())}_{user['id']}"
                _tokens[token] = {"id": user["id"], "account": user["account"], "nickName": user["nickName"]}
                resp_user = {k: v for k, v in user.items() if k not in ("password", "salt")}
                return json_response(success({"token": token, "user": resp_user}))
            return json_response(fail(401, "密码错误"), status=401)
    return json_response(fail(401, "用户不存在"), status=401)

async def handle_register(request: web.Request) -> web.Response:
    body = await request.json()
    account, password = body.get("account", ""), body.get("password", "")
    nick_name = body.get("nickName", account)
    if any(u["account"] == account for u in _users.values()):
        return json_response(fail(400, "账号已存在"), status=400)
    global _next_user_id
    new_id = _next_user_id
    _next_user_id += 1
    new_user = {
        "id": new_id, "account": account, "nickName": nick_name,
        "password": password, "salt": "reg-salt",
        "email": f"{account}@blog.com", "avatar": f"https://api.dicebear.com/avatar/{account}",
        "status": "1", "admin": False, "createDate": int(time.time() * 1000),
        "lastLogin": int(time.time() * 1000), "mobilePhoneNumber": ""
    }
    _users[new_id] = new_user
    token = f"blog_token_{int(time.time())}_{new_id}"
    _tokens[token] = {"id": new_id, "account": account, "nickName": nick_name}
    resp_user = {k: v for k, v in new_user.items() if k not in ("password", "salt")}
    return json_response(success({"token": token, "user": resp_user}))

async def handle_logout(request: web.Request) -> web.Response:
    token = get_token(request)
    if token in _tokens:
        del _tokens[token]
    return json_response(success())

async def handle_current_user(request: web.Request) -> web.Response:
    info = authenticate(request)
    if not info:
        return json_response(fail(401, "未登录"), status=401)
    user = _users.get(info["id"])
    if user:
        resp_user = {k: v for k, v in user.items() if k not in ("password", "salt")}
        return json_response(success(resp_user))
    return json_response(fail(404, "用户不存在"), status=404)

async def handle_hot_users(request: web.Request) -> web.Response:
    users = sorted(_users.values(), key=lambda u: u.get("createDate", 0), reverse=True)[:3]
    resp = [{k: v for k, v in u.items() if k not in ("password", "salt")} for u in users]
    return json_response(success(resp))

async def handle_list_articles(request: web.Request) -> web.Response:
    body = await request.json()
    page, page_size = body.get("page", 1), body.get("pageSize", 10)
    articles = list(_articles.values())
    total = len(articles)
    start = (page - 1) * page_size
    return json_response(success({
        "records": articles[start:start + page_size],
        "total": total, "page": page, "pageSize": page_size
    }))

async def handle_hot_articles(request: web.Request) -> web.Response:
    arts = sorted(_articles.values(), key=lambda a: a.get("viewCounts", 0), reverse=True)[:5]
    return json_response(success(arts))

async def handle_new_articles(request: web.Request) -> web.Response:
    arts = sorted(_articles.values(), key=lambda a: a.get("createDate", ""), reverse=True)[:5]
    return json_response(success(arts))

async def handle_list_archives(request: web.Request) -> web.Response:
    archives = {}
    for a in _articles.values():
        ym = a.get("createDate", "")[:7]
        if ym not in archives:
            archives[ym] = {"year": ym[:4], "month": ym[5:7], "count": 0}
        archives[ym]["count"] += 1
    return json_response(success(list(archives.values())))

async def handle_view_article(request: web.Request) -> web.Response:
    article_id = request.match_info["id"]
    try:
        aid = int(article_id)
    except ValueError:
        return json_response(fail(400, "Invalid article ID"), status=400)
    article = _articles.get(aid)
    if not article:
        return json_response(fail(404, "Article not found"), status=404)
    article["viewCounts"] = article.get("viewCounts", 0) + 1
    return json_response(success(article))

async def handle_publish_article(request: web.Request) -> web.Response:
    body = await request.json()
    if not body.get("title"):
        return json_response(fail(400, "标题不能为空"), status=400)
    global _next_article_id
    new_id = _next_article_id
    _next_article_id += 1
    new_article = {
        "id": new_id, "title": body["title"], "summary": body.get("summary", ""),
        "viewCounts": 0, "commentCounts": 0, "weight": 0,
        "authorId": 1, "bodyId": 200 + new_id,
        "categoryId": (body.get("category") or {}).get("id", 1),
        "createDate": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tags": body.get("tags", []),
        "category": body.get("category", {"id": 1, "categoryName": "技术"})
    }
    _articles[new_id] = new_article
    return json_response(success(new_article), status=201)

async def handle_get_comments(request: web.Request) -> web.Response:
    article_id = request.match_info["id"]
    try:
        aid = int(article_id)
    except ValueError:
        return json_response(fail(400, "Invalid article ID"), status=400)
    comments = [c for c in _comments.values() if c.get("articleId") == aid]
    return json_response(success(comments))

async def handle_create_comment(request: web.Request) -> web.Response:
    body = await request.json()
    if not body.get("content"):
        return json_response(fail(400, "评论内容不能为空"), status=400)
    global _next_comment_id
    new_id = _next_comment_id
    _next_comment_id += 1
    new_comment = {
        "id": new_id, "articleId": body.get("articleId"),
        "content": body["content"], "authorId": 2,
        "createDate": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "username": "tester", "toUserId": body.get("toUserId"),
        "parent": body.get("parent")
    }
    _comments[new_id] = new_comment
    article_id = body.get("articleId")
    if article_id in _articles:
        _articles[article_id]["commentCounts"] = _articles[article_id].get("commentCounts", 0) + 1
    return json_response(success(new_comment), status=201)

async def handle_list_tags(request: web.Request) -> web.Response:
    return json_response(success(list(_tags.values())))

async def handle_hot_tags(request: web.Request) -> web.Response:
    tags = sorted(_tags.values(), key=lambda t: t.get("id", 0), reverse=True)[:6]
    return json_response(success(tags))

async def handle_tags_detail(request: web.Request) -> web.Response:
    return json_response(success(list(_tags.values())))

async def handle_tag_detail(request: web.Request) -> web.Response:
    try:
        tid = int(request.match_info["id"])
    except ValueError:
        return json_response(fail(400, "Invalid tag ID"), status=400)
    tag = _tags.get(tid)
    if not tag:
        return json_response(fail(404, "Tag not found"), status=404)
    articles = [a for a in _articles.values() if any(t.get("id") == tid for t in a.get("tags", []))]
    return json_response(success({"tag": tag, "articles": articles}))

async def handle_list_categories(request: web.Request) -> web.Response:
    return json_response(success(list(_categories.values())))

async def handle_categories_detail(request: web.Request) -> web.Response:
    return json_response(success(list(_categories.values())))

async def handle_category_detail(request: web.Request) -> web.Response:
    try:
        cid = int(request.match_info["id"])
    except ValueError:
        return json_response(fail(400, "Invalid category ID"), status=400)
    cat = _categories.get(cid)
    if not cat:
        return json_response(fail(404, "Category not found"), status=404)
    articles = [a for a in _articles.values() if a.get("categoryId") == cid]
    return json_response(success({"category": cat, "articles": articles}))


# ─── 路由构建 ─────────────────────────────────────────────────────────────────

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_route("POST", "/login", handle_login)
    app.router.add_route("POST", "/register", handle_register)
    app.router.add_route("POST", "/logout", handle_logout)
    app.router.add_route("GET", "/users/currentUser", handle_current_user)
    app.router.add_route("POST", "/user/hotUsers", handle_hot_users)
    app.router.add_route("POST", "/articles/list", handle_list_articles)
    app.router.add_route("POST", "/articles/hot", handle_hot_articles)
    app.router.add_route("POST", "/articles/new", handle_new_articles)
    app.router.add_route("POST", "/articles/listArchives", handle_list_archives)
    app.router.add_route("POST", "/articles/publish", handle_publish_article)
    app.router.add_route("GET", "/articles/view/{id}", handle_view_article)
    app.router.add_route("GET", "/comments/article/{id}", handle_get_comments)
    app.router.add_route("POST", "/comments/create/change", handle_create_comment)
    app.router.add_route("GET", "/tags", handle_list_tags)
    app.router.add_route("GET", "/tags/hot", handle_hot_tags)
    app.router.add_route("GET", "/tags/detail", handle_tags_detail)
    app.router.add_route("GET", "/tags/detail/{id}", handle_tag_detail)
    app.router.add_route("GET", "/categorys", handle_list_categories)
    app.router.add_route("GET", "/categorys/detail", handle_categories_detail)
    app.router.add_route("GET", "/categorys/detail/{id}", handle_category_detail)
    return app


# ─── Server ────────────────────────────────────────────────────────────────────

class BlogAPIServer:
    """Blog API Mock 服务器 - aiohttp 异步版，线程内运行"""

    def __init__(self, host: str = "localhost", port: int = 19998):
        self.host = host
        self.port = port
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self):
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            app = create_app()
            self._runner = web.AppRunner(app)
            self._loop.run_until_complete(self._runner.setup())
            self._site = web.TCPSite(self._runner, self.host, self.port)
            self._loop.run_until_complete(self._site.start())
            logger.info(f"BlogAPI server started at {self.base_url}")
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        # 等待服务就绪
        time.sleep(0.5)

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=3)
            self._loop = None
            logger.info("BlogAPI server stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
