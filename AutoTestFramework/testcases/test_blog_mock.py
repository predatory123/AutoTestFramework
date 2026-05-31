"""Blog API Mock 测试套件 - 测试 blog_api_mock.py 实现的 Mock 服务"""
import pytest
import allure
import time


# ─── 共享 fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def blog_mock_auth(request_engine, blog_mock_server):
    """动态登录获取 token"""
    resp = request_engine.post(
        f"{blog_mock_server.base_url}/login",
        data={"account": "admin", "password": "abc123"}
    )
    assert resp.status_code == 200, f"Login failed: {resp.body}"
    token = resp.body["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


# ─── 认证模块 ─────────────────────────────────────────────────────────────────

@allure.feature("认证模块-Mock")
class TestBlogMockAuth:
    """登录 / 注册 / 登出"""

    def test_login_success(self, request_engine, blog_mock_server):
        """正常登录 - admin"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/login",
            data={"account": "admin", "password": "abc123"}
        )
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert "token" in resp.body["data"]
        assert resp.body["data"]["user"]["account"] == "admin"

    def test_login_wrong_password(self, request_engine, blog_mock_server):
        """登录失败 - 密码错误"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/login",
            data={"account": "admin", "password": "wrongpass"}
        )
        assert resp.status_code == 401
        assert resp.body["success"] is False

    def test_login_user_not_exists(self, request_engine, blog_mock_server):
        """登录失败 - 用户不存在"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/login",
            data={"account": "nobody", "password": "anypass"}
        )
        assert resp.status_code == 401
        assert resp.body["code"] == 401

    def test_register_success(self, request_engine, blog_mock_server):
        """注册成功 - 新用户"""
        unique_name = f"user_{int(time.time())}"
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/register",
            data={"account": unique_name, "password": "Pass123456", "nickName": unique_name}
        )
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert "token" in resp.body["data"]

    def test_register_duplicate_account(self, request_engine, blog_mock_server):
        """注册失败 - 账号已存在"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/register",
            data={"account": "admin", "password": "Pass123456", "nickName": "Admin2"}
        )
        assert resp.status_code == 400
        assert resp.body["code"] == 400

    def test_logout(self, request_engine, blog_mock_server, blog_mock_auth):
        """登出"""
        resp = request_engine.post(f"{blog_mock_server.base_url}/logout")
        assert resp.status_code == 200


# ─── 用户模块 ─────────────────────────────────────────────────────────────────

@allure.feature("用户模块-Mock")
class TestBlogMockUser:
    """当前用户 / 热门用户"""

    def test_current_user(self, request_engine, blog_mock_server, blog_mock_auth):
        """获取当前登录用户信息"""
        resp = request_engine.get(
            f"{blog_mock_server.base_url}/users/currentUser",
            headers=blog_mock_auth
        )
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert resp.body["data"]["account"] == "admin"

    def test_current_user_no_auth(self, request_engine, blog_mock_server):
        """未登录获取当前用户 - 401"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/users/currentUser")
        assert resp.status_code == 401

    def test_hot_users(self, request_engine, blog_mock_server):
        """获取热门用户"""
        resp = request_engine.post(f"{blog_mock_server.base_url}/user/hotUsers")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert len(resp.body["data"]) >= 2


# ─── 文章模块 ─────────────────────────────────────────────────────────────────

@allure.feature("文章模块-Mock")
class TestBlogMockArticle:
    """文章列表 / 热门 / 最新 / 归档 / 详情 / 发布"""

    def test_list_articles(self, request_engine, blog_mock_server):
        """文章列表 - 分页"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/articles/list",
            data={"page": 1, "pageSize": 5}
        )
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert "records" in resp.body["data"]
        assert resp.body["data"]["total"] >= 3

    def test_list_articles_pagination(self, request_engine, blog_mock_server):
        """文章列表 - 分页参数"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/articles/list",
            data={"page": 1, "pageSize": 2}
        )
        assert resp.status_code == 200
        assert len(resp.body["data"]["records"]) <= 2

    def test_hot_articles(self, request_engine, blog_mock_server):
        """热门文章"""
        resp = request_engine.post(f"{blog_mock_server.base_url}/articles/hot")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        articles = resp.body["data"]
        assert len(articles) >= 1
        for i in range(len(articles) - 1):
            assert articles[i]["viewCounts"] >= articles[i + 1]["viewCounts"]

    def test_new_articles(self, request_engine, blog_mock_server):
        """最新文章"""
        resp = request_engine.post(f"{blog_mock_server.base_url}/articles/new")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert len(resp.body["data"]) >= 1

    def test_list_archives(self, request_engine, blog_mock_server):
        """文章归档"""
        resp = request_engine.post(f"{blog_mock_server.base_url}/articles/listArchives")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        archives = resp.body["data"]
        assert len(archives) >= 1
        for arch in archives:
            assert "year" in arch
            assert "month" in arch
            assert "count" in arch

    def test_view_article(self, request_engine, blog_mock_server):
        """查看文章详情"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/articles/view/1")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert resp.body["data"]["id"] == 1
        assert "title" in resp.body["data"]

    def test_view_article_not_found(self, request_engine, blog_mock_server):
        """查看文章 - 不存在"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/articles/view/9999")
        assert resp.status_code == 404

    def test_publish_article(self, request_engine, blog_mock_server, blog_mock_auth):
        """发布文章"""
        unique_title = f"测试文章_{int(time.time())}"
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/articles/publish",
            headers=blog_mock_auth,
            data={
                "title": unique_title,
                "summary": "这是一篇测试文章",
                "body": {"content": "文章正文内容", "contentHtml": "<p>文章正文内容</p>"},
                "category": {"id": 1, "categoryName": "技术"},
                "tags": [{"id": 1, "tagName": "测试"}]
            }
        )
        assert resp.status_code in (200, 201)
        assert resp.body["success"] is True
        assert resp.body["data"]["title"] == unique_title

    def test_publish_article_no_title(self, request_engine, blog_mock_server, blog_mock_auth):
        """发布文章 - 缺少标题"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/articles/publish",
            headers=blog_mock_auth,
            data={"title": "", "summary": "无标题文章"}
        )
        assert resp.status_code == 400


# ─── 评论模块 ─────────────────────────────────────────────────────────────────

@allure.feature("评论模块-Mock")
class TestBlogMockComment:
    """文章评论 / 发布评论"""

    def test_get_comments(self, request_engine, blog_mock_server):
        """获取文章评论"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/comments/article/1")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert isinstance(resp.body["data"], list)

    def test_create_comment(self, request_engine, blog_mock_server, blog_mock_auth):
        """发布评论"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/comments/create/change",
            headers=blog_mock_auth,
            data={"articleId": 1, "content": f"自动化测试评论_{int(time.time())}"}
        )
        assert resp.status_code in (200, 201)
        assert resp.body["success"] is True
        assert resp.body["data"]["articleId"] == 1

    def test_create_comment_empty_content(self, request_engine, blog_mock_server, blog_mock_auth):
        """发布评论 - 空内容"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/comments/create/change",
            headers=blog_mock_auth,
            data={"articleId": 1, "content": ""}
        )
        assert resp.status_code == 400


# ─── 分类模块 ─────────────────────────────────────────────────────────────────

@allure.feature("分类模块-Mock")
class TestBlogMockCategory:
    """分类列表 / 分类详情"""

    def test_list_categories(self, request_engine, blog_mock_server):
        """获取全部分类"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/categorys")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        cats = resp.body["data"]
        assert len(cats) >= 3
        assert any(c["categoryName"] == "技术" for c in cats)

    def test_category_detail(self, request_engine, blog_mock_server):
        """获取分类详情 + 该分类文章"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/categorys/detail/1")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert "category" in resp.body["data"]
        assert resp.body["data"]["category"]["categoryName"] == "技术"

    def test_category_detail_not_found(self, request_engine, blog_mock_server):
        """分类详情 - 不存在"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/categorys/detail/9999")
        assert resp.status_code == 404

    def test_categories_detail(self, request_engine, blog_mock_server):
        """获取全部分类详情"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/categorys/detail")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert len(resp.body["data"]) >= 3


# ─── 标签模块 ─────────────────────────────────────────────────────────────────

@allure.feature("标签模块-Mock")
class TestBlogMockTag:
    """标签列表 / 热门标签 / 标签详情"""

    def test_list_tags(self, request_engine, blog_mock_server):
        """获取全部标签"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/tags")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert len(resp.body["data"]) >= 5

    def test_hot_tags(self, request_engine, blog_mock_server):
        """热门标签"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/tags/hot")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert len(resp.body["data"]) >= 1

    def test_tag_detail(self, request_engine, blog_mock_server):
        """标签详情"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/tags/detail/1")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert "tag" in resp.body["data"]
        assert resp.body["data"]["tag"]["tagName"] == "Spring"

    def test_tag_detail_not_found(self, request_engine, blog_mock_server):
        """标签详情 - 不存在"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/tags/detail/9999")
        assert resp.status_code == 404

    def test_tags_detail(self, request_engine, blog_mock_server):
        """全标签详情"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/tags/detail")
        assert resp.status_code == 200
        assert resp.body["success"] is True
        assert len(resp.body["data"]) >= 5


# ─── 综合测试 ─────────────────────────────────────────────────────────────────

@allure.feature("综合测试-Mock")
class TestBlogMockIntegration:
    """完整业务流程测试"""

    def test_full_article_workflow(self, request_engine, blog_mock_server, blog_mock_auth):
        """完整流程: 发文章 → 查看 → 评论 → 获取评论"""
        publish_resp = request_engine.post(
            f"{blog_mock_server.base_url}/articles/publish",
            headers=blog_mock_auth,
            data={
                "title": f"完整流程测试文章_{int(time.time())}",
                "summary": "测试完整业务流程",
                "body": {"content": "正文", "contentHtml": "<p>正文</p>"},
                "category": {"id": 1, "categoryName": "技术"},
                "tags": [{"id": 1, "tagName": "Spring"}]
            }
        )
        assert publish_resp.status_code in (200, 201)
        article_id = publish_resp.body["data"]["id"]

        view_resp = request_engine.get(f"{blog_mock_server.base_url}/articles/view/{article_id}")
        assert view_resp.status_code == 200
        assert view_resp.body["data"]["title"] == publish_resp.body["data"]["title"]

        comment_resp = request_engine.post(
            f"{blog_mock_server.base_url}/comments/create/change",
            headers=blog_mock_auth,
            data={"articleId": article_id, "content": "测试评论"}
        )
        assert comment_resp.status_code in (200, 201)

        comments_resp = request_engine.get(f"{blog_mock_server.base_url}/comments/article/{article_id}")
        assert comments_resp.status_code == 200
        assert len(comments_resp.body["data"]) >= 1

    @pytest.mark.parametrize("article_id", [1, 2, 3])
    def test_view_multiple_articles(self, request_engine, blog_mock_server, article_id):
        """批量查看文章"""
        resp = request_engine.get(f"{blog_mock_server.base_url}/articles/view/{article_id}")
        assert resp.status_code == 200
        assert resp.body["data"]["id"] == article_id

    @pytest.mark.parametrize("username,password,expect_code", [
        ("admin", "abc123", 200),
        ("admin", "wrongpass", 401),
        ("tester", "123456", 200),
        ("tester", "badpass", 401),
        ("", "", 401),
    ])
    def test_login_parametrized(self, request_engine, blog_mock_server, username, password, expect_code):
        """参数化登录测试"""
        resp = request_engine.post(
            f"{blog_mock_server.base_url}/login",
            data={"account": username, "password": password}
        )
        assert resp.status_code == expect_code
