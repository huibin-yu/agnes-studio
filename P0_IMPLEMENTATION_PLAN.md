# P0 Implementation Plan

> **版本**: v1.0
>
> **编制日期**: 2026-06-15
>
> **总工期**: 5 个工作日
>
> **执行团队**: Architect / Backend / Frontend / QA

---

## 目录

- [Epic 1: 用户状态修复](#epic-1-用户状态修复)
- [Epic 2: 首页信任修复](#epic-2-首页信任修复)
- [Epic 3: 数据库迁移基础设施](#epic-3-数据库迁移基础设施)
- [Epic 4: 头像系统修复](#epic-4-头像系统修复)
- [Epic 5: 视频退款竞态修复](#epic-5-视频退款竞态修复)
- [Epic 6: 视频资金路径重构](#epic-6-视频资金路径重构)

---

## Epic 1: 用户状态修复

> **目标**: 消除刷新页面后登录状态丢失的问题
>
> **工期**: Day 1 上午
>
> **负责人**: Frontend

---

### Story 1.1: 重构 Auth Store 状态派生

> 作为已登录用户，我希望刷新页面后仍保持登录状态，以便不必每次重新登录。

---

#### Task 1.1.1: 移除 `isAuthenticated` 独立状态字段

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | `frontend/src/stores/auth.ts` 当前代码（61 行） |
| **输出** | 修改后的 `auth.ts`，不再维护独立的 `isAuthenticated` 布尔值 |
| **依赖** | 无 |
| **验收标准** | ① `AuthState` 接口中无 `isAuthenticated` 字段 ② 初始状态无 `isAuthenticated` ③ `login()` 不设置 `isAuthenticated: true` ④ `logout()` 不设置 `isAuthenticated: false` ⑤ TypeScript 编译通过 |

**具体改动**:
```
文件: frontend/src/stores/auth.ts

1. 删除 interface AuthState 中的 `isAuthenticated: boolean`（line 17）
2. 删除初始状态中的 `isAuthenticated: false`（line 33）
3. 删除 login() 中的 `isAuthenticated: true`（line 40）
4. 删除 logout() 中的 `isAuthenticated: false`（line 44）
5. 从 partialize 中移除（当前未包含，确认无遗漏）
```

#### Task 1.1.2: 新增派生 Selector

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | Task 1.1.1 完成后的 `auth.ts` |
| **输出** | 新增 `useIsAuthenticated` selector hook |
| **依赖** | Task 1.1.1 |
| **验收标准** | ① `useIsAuthenticated()` 在 `user !== null && accessToken !== null` 时返回 `true` ② 在任一为 `null` 时返回 `false` ③ TypeScript 类型正确推断为 `boolean` |

**新增代码**:
```typescript
// 在 auth.ts 末尾导出
export const useIsAuthenticated = () =>
  useAuthStore((s) => s.user !== null && s.accessToken !== null)
```

#### Task 1.1.3: 更新 Navbar 消费方式

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | `frontend/src/components/navbar.tsx` + Task 1.1.2 的 selector |
| **输出** | Navbar 使用 `useIsAuthenticated` 替代原 `isAuthenticated` |
| **依赖** | Task 1.1.2 |
| **验收标准** | ① Navbar 中不再引用 `s.isAuthenticated` ② 使用 `useIsAuthenticated()` 或等效 selector ③ 登录后显示头像，未登录显示登录按钮 ④ TypeScript 编译通过 |

**具体改动**:
```
文件: frontend/src/components/navbar.tsx

搜索 `isAuthenticated` 所有出现位置
替换 useAuthStore((s) => s.isAuthenticated)
为 useIsAuthenticated() 或 useAuthStore((s) => s.user !== null && s.accessToken !== null)
```

#### Task 1.1.4: 全局搜索并更新所有 `isAuthenticated` 消费点

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | 项目全局 `grep` 结果 |
| **输出** | 所有引用 `isAuthenticated` 的文件更新完毕 |
| **依赖** | Task 1.1.2 |
| **验收标准** | ① `grep -r "isAuthenticated" frontend/src/` 仅匹配 Task 1.1.2 的定义和 Task 1.1.3 的使用 ② 无编译错误 ③ 登录/注册流程正常 |

**执行命令**:
```bash
grep -rn "isAuthenticated" frontend/src/
# 预期文件:
# - stores/auth.ts (定义处)
# - components/navbar.tsx (消费处)
# - 可能: login/page.tsx, middleware.ts
```

---

### Story 1.2: 修复 Token 刷新不通知 Store

> 作为已登录用户，我希望 Token 自动刷新后前端状态保持一致，以避免数据读取使用过期 Token。

---

#### Task 1.2.1: 修复 API 拦截器 Token 刷新逻辑

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | `frontend/src/lib/api.ts` 当前代码 |
| **输出** | Token 刷新成功后同步更新 Zustand Store |
| **依赖** | Task 1.1.1（Store 结构确认） |
| **验收标准** | ① 响应拦截器中刷新 Token 成功后调用 `useAuthStore.getState().setAccessToken(newToken)` ② 不再仅修改 localStorage ③ 已登录用户的后续 API 请求使用新 Token |

**具体改动**:
```
文件: frontend/src/lib/api.ts

在 Token 刷新成功的分支中（约 line 55-58）:

// 现有: 直接改 localStorage
// 改为:
import { useAuthStore } from '@/stores/auth'
// ...刷新成功后:
useAuthStore.getState().setAccessToken(newToken)
// 同时更新 localStorage 中的 accessToken（保持 Zustand persist 一致）
```

#### Task 1.2.2: QA 验证登录状态持久化

| 字段 | 内容 |
|------|------|
| **Owner** | QA |
| **输入** | Task 1.1.1 ~ 1.2.1 全部完成 |
| **输出** | 测试报告（Pass/Fail） |
| **依赖** | Task 1.1.4, Task 1.2.1 |
| **验收标准** | 全部以下用例通过: |

| # | 用例 | 步骤 | 预期 |
|---|------|------|------|
| 1 | 刷新保持登录 | 登录 → F5 刷新 | 导航栏显示用户头像和积分 |
| 2 | 退出后刷新 | 退出登录 → F5 | 导航栏显示"登录"按钮 |
| 3 | Token 刷新同步 | 等待 15 分钟 Token 过期 → 触发 API 调用 | 自动刷新成功，页面不跳转登录 |
| 4 | 多标签页同步 | 标签 A 登出 → 标签 B 刷新 | 标签 B 显示未登录（localStorage 已清） |

---

## Epic 2: 首页信任修复

> **目标**: 移除虚假统计数据，消除信任危机
>
> **工期**: Day 1 上午
>
> **负责人**: Frontend

---

### Story 2.1: 移除虚假统计区块

> 作为首次访问用户，我希望看到真实的信息，以信任这个平台。

---

#### Task 2.1.1: 删除 `stats` 数据定义

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | `frontend/src/app/page.tsx` line 41-47 |
| **输出** | `stats` 常量和相关 import 被移除 |
| **依赖** | 无 |
| **验收标准** | ① `const stats = [...]` 代码块已删除 ② 未使用的图标 import 已清理（注意 features 数组仍用 `Users`, `Image`, `Video`, `Sparkles`） ③ TypeScript 编译通过 |

**具体改动**:
```
文件: frontend/src/app/page.tsx

1. 删除 lines 41-47 的 stats 数组
2. 检查 import 中的图标: Users, Image, Video, Sparkles
   → features 数组仍使用这些，不删除
3. 检查 import 中是否有仅 stats 使用的图标
   → Eye, Heart 在 import 中但不在 features 中，可清理
```

#### Task 2.1.2: 删除统计区块 JSX

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | Task 2.1.1 完成后的 `page.tsx` |
| **输出** | 统计 `<section>` 从 JSX 中移除 |
| **依赖** | Task 2.1.1 |
| **验收标准** | ① `<section className="py-16 px-4 border-y">` 及其子元素已删除 ② 页面布局无断裂（Hero → Features → CTA 连贯） ③ 视觉检查无空白异常 |

**具体改动**:
```
文件: frontend/src/app/page.tsx

删除整个 Stats section（约 lines 119-136）:
  {/* Stats */}
  <section className="py-16 px-4 border-y">
    ...
  </section>
```

#### Task 2.1.3: 修正"免费调用"误导标签

| 字段 | 内容 |
|------|------|
| **Owner** | Frontend |
| **输入** | `frontend/src/app/page.tsx` line 68 |
| **输出** | Hero 标签文案更新 |
| **依赖** | 无 |
| **验收标准** | ① 标签显示 `Agnes AI 驱动 · 注册送积分` 而非 `Agnes AI 驱动 · 免费调用` ② 无其他文案受影响 |

**具体改动**:
```
文件: frontend/src/app/page.tsx line 68

- Agnes AI 驱动 · 免费调用
+ Agnes AI 驱动 · 注册送积分
```

#### Task 2.1.4: QA 验证首页

| 字段 | 内容 |
|------|------|
| **Owner** | QA |
| **输入** | Task 2.1.1 ~ 2.1.3 完成 |
| **输出** | 测试报告 |
| **依赖** | Task 2.1.1, Task 2.1.2, Task 2.1.3 |
| **验收标准** | 全部以下用例通过: |

| # | 用例 | 步骤 | 预期 |
|---|------|------|------|
| 1 | 统计区块移除 | 访问首页 | 无 "100K+" 等数字出现 |
| 2 | 页面布局完整 | 滚动首页 | Hero → Features → CTA 连贯无断裂 |
| 3 | 标签文案 | 查看 Hero 标签 | 显示"注册送积分" |
| 4 | 响应式 | 缩小至 375px | 布局正常 |

---

## Epic 3: 数据库迁移基础设施

> **目标**: 建立 Alembic 迁移体系，替换 `create_all`，支持安全的 Schema 变更
>
> **工期**: Day 1 ~ Day 2
>
> **负责人**: Architect（设计审查）+ Backend（实施）

---

### Story 3.1: 初始化 Alembic

> 作为后端开发者，我希望有标准化的数据库迁移工具，以便安全地演进 Schema。

---

#### Task 3.1.1: Architect — 设计迁移策略

| 字段 | 内容 |
|------|------|
| **Owner** | Architect |
| **输入** | `backend/app/core/config.py` 配置、`requirements.txt` 已含 `alembic==1.14.0` |
| **输出** | 迁移策略决策文档（嵌入代码注释） |
| **依赖** | 无 |
| **验收标准** | ① 决策点全部明确: 迁移目录位置、自动生成 vs 手写、启动时是否自动迁移、初始基线 ② Backend 已理解决策并可执行 |

**决策输出**:
```
□ 迁移目录: backend/alembic/
□ 自动生成 + 人工审查
□ 开发环境: 自动迁移（SQLite）。生产环境: 手动执行
□ 初始迁移基线: 从当前 ORM 自动生成
□ 命名约定: {date}_{rev}_{desc}.py
□ compare_type=True, compare_server_default=True
```

#### Task 3.1.2: Backend — 执行 `alembic init`

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | Task 3.1.1 策略确认 |
| **输出** | `backend/alembic/` 目录 + `backend/alembic.ini` 文件 |
| **依赖** | Task 3.1.1 |
| **验收标准** | ① `backend/alembic/` 目录存在，含 `env.py`、`script.py.mako`、`versions/` ② `backend/alembic.ini` 存在 ③ 不影响现有代码运行 |

**执行**:
```bash
cd backend && alembic init alembic
```

#### Task 3.1.3: Backend — 配置 `alembic.ini`

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `backend/alembic.ini`（由 Task 3.1.2 生成） |
| **输出** | 配置完成的 `alembic.ini` |
| **依赖** | Task 3.1.2 |
| **验收标准** | ① `sqlalchemy.url` 从环境变量 `DATABASE_URL` 读取 ② `script_location = alembic` ③ 文件不包含硬编码的数据库密码 |

**改动**:
```
文件: backend/alembic.ini

[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname
# 实际值由 env.py 从 settings.DATABASE_URL 覆盖
```

#### Task 3.1.4: Backend — 配置 `alembic/env.py`

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `backend/alembic/env.py`（由 Task 3.1.2 生成）+ `app/core/config.py` + `app/models/database.py` |
| **输出** | 配置完成的 `env.py`，能正确读取 ORM metadata |
| **依赖** | Task 3.1.2 |
| **验收标准** | ① `target_metadata = Base.metadata` ② `sqlalchemy.url` 从 `settings.DATABASE_URL` 读取 ③ `context.configure()` 含 `compare_type=True` 和 `compare_server_default=True` ④ `alembic revision --autogenerate -m "test"` 能检测到所有 ORM 模型 |

**关键改动**:
```python
# backend/alembic/env.py

from app.core.config import settings
from app.models.database import Base
from app.models import *  # 确保所有模型被导入

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(settings.DATABASE_URL)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
```

#### Task 3.1.5: Backend — 生成初始迁移并审查

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | Task 3.1.4 完成 + 全部 7 个 ORM 模型 |
| **输出** | `backend/alembic/versions/` 下的初始迁移文件 |
| **依赖** | Task 3.1.4 |
| **验收标准** | ① 迁移文件包含全部 7 张表: `users`, `image_generations`, `video_generations`, `gallery_items`, `gallery_likes`, `api_keys`, `credit_transactions` ② 字段类型与 ORM 定义一致 ③ 外键约束正确 ④ 索引正确 ⑤ `unique` 约束正确 ⑥ `ondelete="CASCADE"` 正确 ⑦ Architect 审查通过 |

**执行**:
```bash
cd backend
alembic revision --autogenerate -m "initial_schema"
```

**审查清单** (Architect 签字):
```
□ users 表: email(unique), username(unique), referral_code(unique), token_version
□ image_generations 表: user_id(FK), status 索引
□ video_generations 表: user_id(FK), video_id(索引), status
□ gallery_items 表: user_id(FK), is_public(索引)
□ gallery_likes 表: user_id(FK), item_id(FK), unique(user_id, item_id)
□ api_keys 表: user_id(FK), key(unique, 索引)
□ credit_transactions 表: user_id(FK), type(索引), created_at(索引)
```

---

### Story 3.2: 替换 `create_all` 为迁移检测

> 作为运维人员，我希望应用启动时自动应用数据库迁移，以避免手动执行 SQL。

---

#### Task 3.2.1: Backend — 修改 `lifespan` 函数

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `backend/app/main.py` line 36-46 的 `lifespan` 函数 |
| **输出** | 开发环境自动 `create_all`，生产环境执行 `alembic upgrade head` |
| **依赖** | Task 3.1.5 |
| **验收标准** | ① SQLite 环境（开发）仍使用 `create_all`（向后兼容） ② 非 SQLite 环境执行 `alembic upgrade head` ③ 迁移失败时记录错误日志但不阻止启动（降级为警告） ④ 关闭时 `engine.dispose()` 仍正常执行 |

**改动**:
```
文件: backend/app/main.py

替换 lines 36-46 的 lifespan 函数:

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agnes Studio API...")
    if "sqlite" in settings.DATABASE_URL:
        # 开发环境: create_all 向后兼容
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured (SQLite dev mode).")
    else:
        # 生产环境: Alembic 迁移
        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command as alembic_cmd
            alembic_cfg = AlembicConfig("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            alembic_cmd.upgrade(alembic_cfg, "head")
            logger.info("Database migrations applied successfully.")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            logger.warning("Application starting without migration. Run 'alembic upgrade head' manually.")
    yield
    logger.info("Shutting down Agnes Studio API...")
    await engine.dispose()
```

#### Task 3.2.2: Backend — 生成 `CHECK (credits >= 0)` 迁移

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | Task 3.1.5 的初始迁移已应用 |
| **输出** | 新迁移文件，添加 `CHECK` 约束 |
| **依赖** | Task 3.1.5 |
| **验收标准** | ① 新迁移文件存在 ② `upgrade()` 添加 `CHECK (credits >= 0)` 约束到 `users` 表 ③ `downgrade()` 能安全移除约束 ④ 在 PostgreSQL 上 `UPDATE users SET credits = -1` 应报错 |

**执行**:
```bash
cd backend
alembic revision --autogenerate -m "add_credits_check_constraint"
```

**迁移内容**:
```python
def upgrade():
    op.create_check_constraint(
        'ck_users_credits_non_negative',
        'users',
        'credits >= 0'
    )

def downgrade():
    op.drop_constraint('ck_users_credits_non_negative', 'users')
```

#### Task 3.2.3: Backend — 修复健康检查 `text()` 问题

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `backend/app/main.py` line 106 |
| **输出** | 健康检查使用 `text()` 封装 SQL 字符串 |
| **依赖** | 无 |
| **验收标准** | ① `await session.execute(text("SELECT 1"))` ② `from sqlalchemy import text` 已导入 ③ 健康检查 API 返回 `{"status": "ok", ...}` |

**改动**:
```
文件: backend/app/main.py

Line 106:
- await session.execute("SELECT 1")
+ await session.execute(text("SELECT 1"))

顶部添加:
+ from sqlalchemy import text
```

#### Task 3.2.4: Architect — 审查迁移策略实施

| 字段 | 内容 |
|------|------|
| **Owner** | Architect |
| **输入** | Task 3.1.5 + Task 3.2.1 + Task 3.2.2 全部完成 |
| **输出** | 审查通过/整改清单 |
| **依赖** | Task 3.1.5, Task 3.2.1, Task 3.2.2 |
| **验收标准** | ① 迁移文件内容正确 ② `env.py` 配置安全 ③ `lifespan` 逻辑分支正确 ④ 无硬编码凭据 |

#### Task 3.2.5: QA — 迁移功能验证

| 字段 | 内容 |
|------|------|
| **Owner** | QA |
| **输入** | Task 3.1.5 ~ 3.2.2 全部完成 |
| **输出** | 测试报告 |
| **依赖** | Task 3.2.4 |
| **验收标准** | 全部以下用例通过: |

| # | 用例 | 步骤 | 预期 |
|---|------|------|------|
| 1 | 空库建表 | `rm agnes_studio.db` → 启动应用 | 所有表正确创建 |
| 2 | 已有库迁移 | 已有库执行 `alembic upgrade head` | 无报错，无数据丢失 |
| 3 | 迁移回滚 | `alembic downgrade -1` | 约束安全移除 |
| 4 | 迁移历史 | `alembic history` | 显示完整迁移链 |
| 5 | 健康检查 | `GET /api/health` | `{"status": "ok", "database": "connected"}` |
| 6 | CHECK 约束（PG） | `UPDATE users SET credits = -1` | 数据库拒绝 |

---

## Epic 4: 头像系统修复

> **目标**: 修复头像上传后 404 问题及 WebP 校验漏洞
>
> **工期**: Day 1 上午（30 分钟）
>
> **负责人**: Backend

---

### Story 4.1: 修复头像 URL 路径

> 作为用户，我希望上传头像后能正确显示。

---

#### Task 4.1.1: 修复 avatar_url 路径拼接

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `backend/app/api/users.py` line 64 |
| **输出** | URL 路径与实际文件路径一致 |
| **依赖** | 无 |
| **验收标准** | ① 数据库存储的 URL 与文件系统路径一致 ② `GET /uploads/avatars/{user_id}_{filename}` 返回 200 ③ 无其他代码引用旧路径格式 |

**改动**:
```
文件: backend/app/api/users.py line 64

- current_user.avatar_url = f"/uploads/avatars/{safe_name}"
+ current_user.avatar_url = f"/uploads/avatars/{current_user.id}_{safe_name}"
```

#### Task 4.1.2: 修复 WebP 魔数字节校验括号

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `backend/app/api/users.py` line 47-52 |
| **输出** | 运算符优先级明确，与 `images.py` 一致 |
| **依赖** | 无 |
| **验收标准** | ① WebP 检查有显式括号 `(...)` ② 与 `backend/app/api/images.py` 的校验逻辑一致 ③ 上传 WebP 格式头像验证通过 |

**改动**:
```
文件: backend/app/api/users.py line 47-52

  is_valid_image = (
      content[:3] == b'\xff\xd8\xff' or
      content[:8] == b'\x89PNG\r\n\x1a\n' or
      content[:4] == b'GIF8' or
-     content[:4] == b'RIFF' and content[8:12] == b'WEBP'
+     (content[:4] == b'RIFF' and content[8:12] == b'WEBP')
  )
```

#### Task 4.1.3: QA — 头像功能验证

| 字段 | 内容 |
|------|------|
| **Owner** | QA |
| **输入** | Task 4.1.1 + 4.1.2 完成 |
| **输出** | 测试报告 |
| **依赖** | Task 4.1.1, Task 4.1.2 |
| **验收标准** | 全部以下用例通过: |

| # | 用例 | 步骤 | 预期 |
|---|------|------|------|
| 1 | JPEG 上传 | 上传 .jpg 头像 | 显示正常，无 404 |
| 2 | PNG 上传 | 上传 .png 头像 | 显示正常 |
| 3 | WebP 上传 | 上传 .webp 头像 | 验证通过，显示正常 |
| 4 | 覆盖上传 | 上传两次不同头像 | 第二次覆盖第一次 |
| 5 | 超大文件 | 上传 > 5MB 图片 | 返回 413 错误 |
| 6 | 非图片文件 | 上传 .txt 文件 | 返回 400 错误 |

---

## Epic 5: 视频退款竞态修复

> **目标**: 消除并发轮询导致的双重退款资金泄漏
>
> **工期**: Day 3
>
> **负责人**: Backend（实施）+ Architect（审查）+ QA（并发测试）

---

### Story 5.1: 原子化退款逻辑

> 作为平台运营者，我希望视频退款操作是原子的，以防止并发请求导致双重退款。

---

#### Task 5.1.1: Architect — 审查退款方案

| 字段 | 内容 |
|------|------|
| **Owner** | Architect |
| **输入** | 当前 `video_service.py:219-227` 的 `_refund_if_needed` 闭包 |
| **输出** | 方案审查通过/整改意见 |
| **依赖** | 无 |
| **验收标准** | ① 确认"原子 UPDATE + rowcount"方案在 SQLite 和 PostgreSQL 下均有效 ② 确认不依赖 `SELECT FOR UPDATE` ③ 确认 ORM 对象与数据库状态同步策略正确 ④ 输出签字确认 |

#### Task 5.1.2: Backend — 提取 `_refund_if_needed` 为 Service 方法

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `video_service.py` 当前闭包代码 |
| **输出** | `VideoService._refund_if_needed` 方法，使用原子 UPDATE |
| **依赖** | Task 5.1.1 |
| **验收标准** | ① 方法签名为 `async def _refund_if_needed(self, db, video_gen, reason) -> bool` ② 使用 `update(VideoGeneration).where(..., credits_charged > 0).values(credits_charged=0)` ③ 通过 `result.rowcount == 0` 判断是否已被处理 ④ `rowcount == 1` 时执行 `credit_service.grant()` ⑤ 方法内无 `await db.commit()`（由调用方控制事务）⑥ 返回 `bool` 表示是否执行了退款 |

**新方法**:
```python
async def _refund_if_needed(
    self, db: AsyncSession, video_gen: VideoGeneration, reason: str
) -> bool:
    from sqlalchemy import update as sa_update
    from app.services.credit_service import credit_service
    from app.models.credit_transaction import TX_VIDEO_REFUND

    # 原子抢占退款权
    result = await db.execute(
        sa_update(VideoGeneration)
        .where(
            VideoGeneration.id == video_gen.id,
            VideoGeneration.credits_charged > 0,
        )
        .values(credits_charged=0)
    )

    if result.rowcount == 0:
        logger.info(f"Video {video_gen.id}: refund skipped (already handled)")
        return False

    # 获取退款金额（ORM 对象仍持有旧值）
    refund_amount = video_gen.credits_charged
    await credit_service.grant(
        db, video_gen.user_id, refund_amount,
        type=TX_VIDEO_REFUND,
        ref_type="video", ref_id=video_gen.id,
        note=reason,
    )
    video_gen.credits_charged = 0  # 同步 ORM
    logger.info(f"Video {video_gen.id}: refunded {refund_amount} credits ({reason})")
    return True
```

#### Task 5.1.3: Backend — 更新 `poll_video_status` 调用方式

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `video_service.py:185-266` 的 `poll_video_status` 方法 |
| **输出** | 使用 `self._refund_if_needed()` 替代闭包调用 |
| **依赖** | Task 5.1.2 |
| **验收标准** | ① 删除 line 219-227 的 `_refund_if_needed` 闭包定义 ② line 246（completed_no_url）改为 `await self._refund_if_needed(db, video_gen, "completed_no_url")` ③ line 253（generation_failed）改为 `await self._refund_if_needed(db, video_gen, "generation_failed")` ④ `db.commit()` 仍在方法末尾统一提交 ⑤ TypeScript/Python 无编译错误 |

**具体改动点**:
```
文件: backend/app/services/video_service.py

1. 删除 lines 219-227 的 _refund_if_needed 闭包
2. Line 246: await _refund_if_needed("completed_no_url")
   → await self._refund_if_needed(db, video_gen, "completed_no_url")
3. Line 253: await _refund_if_needed("generation_failed")
   → await self._refund_if_needed(db, video_gen, "generation_failed")
```

#### Task 5.1.4: QA — 并发退款压力测试

| 字段 | 内容 |
|------|------|
| **Owner** | QA |
| **输入** | Task 5.1.2 + 5.1.3 完成 + PostgreSQL 测试环境 |
| **输出** | 并发测试脚本 + 报告 |
| **依赖** | Task 5.1.3 |
| **验收标准** | 全部以下用例通过: |

| # | 用例 | 步骤 | 预期 |
|---|------|------|------|
| 1 | 单次退款 | 视频失败 → 轮询 | 余额 +N，退款记录 1 条 |
| 2 | 并发 10 路退款 | 10 个并发 poll 请求同一失败视频 | 余额仅 +N（1 次），退款记录仅 1 条 |
| 3 | 重复轮询 | poll 成功 → 再次 poll 成功 | 不重复退款，credits_charged 保持 0 |
| 4 | 正常完成 | 视频成功 → poll | 无退款，credits_charged 不变 |

**测试脚本骨架**:
```python
@pytest.mark.asyncio
@pytest.mark.postgresql  # 仅在 PG 下运行
async def test_concurrent_refund_single(db_session, user, video_gen):
    video_gen.credits_charged = 10
    await db_session.commit()
    initial_balance = user.credits

    # 10 个并发轮询
    tasks = [
        video_service.poll_video_status(db_session, video_gen.video_id, user.id)
        for _ in range(10)
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    await db_session.refresh(user)
    assert user.credits == initial_balance + 10  # 仅退一次

    # 验证退款记录
    tx = await get_transactions(db_session, user.id, type="video_refund")
    assert len(tx) == 1
    assert tx[0].amount == 10
```

---

## Epic 6: 视频资金路径重构

> **目标**: 消除"上游任务已创建但积分未扣除"的资金泄漏窗口
>
> **工期**: Day 4 ~ Day 5
>
> **负责人**: Backend（实施）+ Architect（审查）+ QA（回归测试）

---

### Story 6.1: 重构 `create_video` 事务顺序

> 作为平台运营者，我希望视频生成的资金路径尽可能安全，以最小化免费生成的风险窗口。

---

#### Task 6.1.1: Architect — 审查资金路径重构方案

| 字段 | 内容 |
|------|------|
| **Owner** | Architect |
| **输入** | 当前 `video_service.py:62-183` 的 `create_video` 方法 |
| **输出** | 重构方案签字确认 |
| **依赖** | 无 |
| **验收标准** | ① 确认新事务顺序: 预检 → 调 Agnes API → 原子扣费+建记录 → commit ② 确认 Agnes API 不可回滚的风险已接受 ③ 确认孤儿任务日志格式包含足够信息（user_id, task_id, video_id, cost）④ 确认与 `image_service.py` 的模式一致 ⑤ 输出签字 |

#### Task 6.1.2: Backend — 重写 `create_video` 事务流程

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `video_service.py:62-183` 当前代码 + Task 6.1.1 方案 |
| **输出** | 重构后的 `create_video` 方法 |
| **依赖** | Task 6.1.1 |
| **验收标准** | ① 事务顺序: 预检余额 → 调 Agnes API → flush 记录 → charge → commit ② 扣费失败时 `db.rollback()` 回滚记录 ③ 扣费失败时 `logger.error` 输出包含 "ORPHANED TASK" + task_id ④ 正常路径只有一次 `db.commit()` ⑤ 返回值结构不变 ⑥ 无硬编码字符串变更 |

**重构后核心流程**:
```python
async def create_video(self, db, user_id, prompt, ...):
    # ① 预检余额
    user = await self._load_user(db, user_id)
    cost = self._calc_cost(num_frames, frame_rate)
    if user.credits < cost:
        raise HTTPException(402, "Insufficient credits")

    # ② 调 Agnes API（不可回滚）
    try:
        api_response = await agnes_service.create_video_task(...)
    except Exception as e:
        raise HTTPException(503, "Video service unavailable")

    # ③ 创建记录 + 扣费（原子）
    video_gen = VideoGeneration(
        user_id=user_id, prompt=prompt,
        task_id=api_response.get("id"),
        video_id=api_response.get("video_id"),
        status=api_response.get("status", "queued"),
        ...
    )
    db.add(video_gen)
    await db.flush()

    try:
        await credit_service.charge(db, user_id, cost, ...)
    except InsufficientCreditsError:
        logger.error(
            f"ORPHANED TASK: user={user_id} "
            f"task_id={api_response.get('id')} "
            f"video_id={api_response.get('video_id')} cost={cost}"
        )
        await db.rollback()
        raise HTTPException(402, "Insufficient credits at charge time")

    video_gen.credits_charged = cost
    await db.commit()
    await db.refresh(video_gen)
    return video_gen
```

#### Task 6.1.3: Backend — 移除 `videos.py` 中的 Mock 检测代码

| 字段 | 内容 |
|------|------|
| **Owner** | Backend |
| **输入** | `backend/app/api/videos.py` line 27-28 |
| **输出** | `_video_value` 函数不包含 mock 检测逻辑 |
| **依赖** | 无 |
| **验收标准** | ① `if value.__class__.__module__.startswith("unittest.mock")` 代码已删除 ② 函数仍能正确处理 `None` 和默认值 ③ 所有使用 `_video_value` 的地方功能正常 |

#### Task 6.1.4: QA — 视频生成全路径回归测试

| 字段 | 内容 |
|------|------|
| **Owner** | QA |
| **输入** | Task 6.1.2 + 6.1.3 完成 |
| **输出** | 回归测试报告 |
| **依赖** | Task 6.1.2, Task 6.1.3 |
| **验收标准** | 全部以下用例通过: |

| # | 场景 | 步骤 | 预期 |
|---|------|------|------|
| 1 | 正常生成 | 提交视频 → 轮询 → 完成 | 记录创建 + 积分扣减 + URL 提取 |
| 2 | 预检拦截 | 积分 = 0 时提交 | 返回 402，无日志中的 ORPHANED TASK |
| 3 | Agnes API 超时 | 模拟 API 超时 | 返回 503，积分不变，无记录 |
| 4 | 扣费竞败 | 2 个并发请求消耗最后 1 份积分 | 1 个成功，1 个返回 402 + ORPHANED 日志 |
| 5 | 正常轮询失败 | 视频失败 → poll | 状态 failed + 积分退还 |
| 6 | 双重轮询 | 同一视频 poll 两次失败 | 仅退一次款 |
| 7 | 正常轮询成功 | 视频成功 → poll | 状态 completed + URL 正确 + 7 天过期 |

#### Task 6.1.5: QA — 图片生成回归测试

| 字段 | 内容 |
|------|------|
| **Owner** | QA |
| **输入** | Task 6.1.2 完成（确保不影响图片生成） |
| **输出** | 回归测试报告 |
| **依赖** | Task 6.1.2 |
| **验收标准** | 以下用例全部通过（确认重构未波及图片功能）: |

| # | 场景 | 步骤 | 预期 |
|---|------|------|------|
| 1 | 文生图正常 | 提交图片生成 | 成功 + 积分扣减 |
| 2 | 图生图正常 | 上传参考图 + 生成 | 成功 + 积分扣减 |
| 3 | 图片积分不足 | 积分 = 0 时生成 | 返回 402 |
| 4 | 图片生成失败 | Agnes API 异常 | 返回 503，积分不变 |

---

## 依赖关系图

```
Epic 1 (用户状态)         Epic 2 (首页信任)      Epic 4 (头像修复)
  ┌────────────┐            ┌──────────┐          ┌──────────┐
  │ 1.1.1 改Store│           │ 2.1.1 删 │          │ 4.1.1 URL│
  └─────┬──────┘            │  stats   │          │  路径    │
        │                   └────┬─────┘          └────┬─────┘
  ┌─────▼──────┐           ┌─────▼─────┐          ┌────▼──────┐
  │ 1.1.2 新增  │           │ 2.1.2 删  │          │ 4.1.2 括号│
  │ selector   │           │  JSX      │          │  修复     │
  └─────┬──────┘           └─────┬─────┘          └────┬──────┘
  ┌─────▼──────┐           ┌─────▼─────┐          ┌────▼──────┐
  │ 1.1.3 Navbar│          │ 2.1.3 改  │          │ 4.1.3 QA  │
  │ 1.1.4 全局  │          │  文案     │          │  验证     │ ✓
  │ 1.2.1 拦截器│          └─────┬─────┘          └───────────┘
  └─────┬──────┘           ┌─────▼─────┐
        │                  │ 2.1.4 QA  │
  ┌─────▼──────┐           │  验证     │ ✓
  │ 1.2.2 QA   │ ✓         └───────────┘
  └────────────┘

Epic 3 (Alembic)          Epic 5 (退款竞态)      Epic 6 (资金路径)
  ┌────────────┐            ┌──────────┐          ┌──────────┐
  │ 3.1.1 策略 │            │ 5.1.1 审 │          │ 6.1.1 审 │
  │ 设计       │            │  查方案  │          │  查方案  │
  └─────┬──────┘            └────┬─────┘          └────┬─────┘
  ┌─────▼──────┐           ┌─────▼─────┐          ┌────▼──────┐
  │ 3.1.2 init │           │ 5.1.2 新  │          │ 6.1.2 重  │
  └─────┬──────┘           │  方法     │          │  写流程   │
  ┌─────▼──────┐           └─────┬─────┘          └────┬──────┘
  │ 3.1.3 ini  │           ┌─────▼─────┐          ┌────▼──────┐
  │ 3.1.4 env  │           │ 5.1.3 更  │          │ 6.1.3 删  │
  └─────┬──────┘           │  新调用   │          │  mock代码 │
  ┌─────▼──────┐           └─────┬─────┘          └────┬──────┘
  │ 3.1.5 生成 │           ┌─────▼─────┐          ┌────▼──────┐
  │ 初始迁移   │           │ 5.1.4 QA  │          │ 6.1.4 QA  │
  └─────┬──────┘           │  并发测试 │          │  视频回归 │
  ┌─────▼──────┐           └───────────┘ ✓        │ 6.1.5 QA  │
  │ 3.2.1 改   │                                  │  图片回归 │
  │ lifespan   │                                  └───────────┘ ✓
  │ 3.2.2 CHECK│
  │ 3.2.3 text │
  └─────┬──────┘
  ┌─────▼──────┐
  │ 3.2.4 审查 │
  │ 3.2.5 QA   │ ✓
  └────────────┘
```

---

## 任务汇总

| Epic | Story | Task | Owner | 依赖 | 估时 |
|------|-------|------|-------|------|------|
| E1 | S1.1 | 1.1.1 移除独立状态 | FE | — | 10min |
| E1 | S1.1 | 1.1.2 新增 selector | FE | 1.1.1 | 5min |
| E1 | S1.1 | 1.1.3 更新 Navbar | FE | 1.1.2 | 10min |
| E1 | S1.1 | 1.1.4 全局搜索更新 | FE | 1.1.2 | 15min |
| E1 | S1.2 | 1.2.1 修复拦截器 | FE | 1.1.1 | 15min |
| E1 | S1.2 | 1.2.2 QA 验证 | QA | 1.1.4, 1.2.1 | 15min |
| E2 | S2.1 | 2.1.1 删 stats 数据 | FE | — | 5min |
| E2 | S2.1 | 2.1.2 删 stats JSX | FE | 2.1.1 | 5min |
| E2 | S2.1 | 2.1.3 改误导标签 | FE | — | 5min |
| E2 | S2.1 | 2.1.4 QA 验证 | QA | 2.1.1, 2.1.2, 2.1.3 | 15min |
| E3 | S3.1 | 3.1.1 设计策略 | Arc | — | 1h |
| E3 | S3.1 | 3.1.2 alembic init | BE | 3.1.1 | 15min |
| E3 | S3.1 | 3.1.3 配置 ini | BE | 3.1.2 | 10min |
| E3 | S3.1 | 3.1.4 配置 env.py | BE | 3.1.2 | 30min |
| E3 | S3.1 | 3.1.5 生成+审查迁移 | BE+Arc | 3.1.4 | 1h |
| E3 | S3.2 | 3.2.1 改 lifespan | BE | 3.1.5 | 30min |
| E3 | S3.2 | 3.2.2 CHECK 约束迁移 | BE | 3.1.5 | 20min |
| E3 | S3.2 | 3.2.3 修复 text() | BE | — | 5min |
| E3 | S3.2 | 3.2.4 审查迁移实施 | Arc | 3.1.5, 3.2.1, 3.2.2 | 30min |
| E3 | S3.2 | 3.2.5 QA 迁移验证 | QA | 3.2.4 | 1h |
| E4 | S4.1 | 4.1.1 修复 URL 路径 | BE | — | 5min |
| E4 | S4.1 | 4.1.2 修复 WebP 括号 | BE | — | 5min |
| E4 | S4.1 | 4.1.3 QA 验证 | QA | 4.1.1, 4.1.2 | 15min |
| E5 | S5.1 | 5.1.1 审查方案 | Arc | — | 1h |
| E5 | S5.1 | 5.1.2 提取退款方法 | BE | 5.1.1 | 2h |
| E5 | S5.1 | 5.1.3 更新调用方式 | BE | 5.1.2 | 1h |
| E5 | S5.1 | 5.1.4 QA 并发测试 | QA | 5.1.3 | 2h |
| E6 | S6.1 | 6.1.1 审查方案 | Arc | — | 1h |
| E6 | S6.1 | 6.1.2 重写 create_video | BE | 6.1.1 | 3h |
| E6 | S6.1 | 6.1.3 删除 mock 代码 | BE | — | 10min |
| E6 | S6.1 | 6.1.4 QA 视频回归 | QA | 6.1.2, 6.1.3 | 2h |
| E6 | S6.1 | 6.1.5 QA 图片回归 | QA | 6.1.2 | 1h |

---

## 工时统计

| 角色 | 工时 | 占比 |
|------|------|------|
| **Architect** | 3.5h（设计审查） | 9% |
| **Backend** | 14.5h（实施开发） | 38% |
| **Frontend** | 1.25h（状态修复 + 统计移除） | 3% |
| **QA** | 7h（测试验证） | 18% |
| **Buffer** | 12h（沟通、Code Review、返工） | 32% |
| **总计** | **38.25h ≈ 5 人天** | 100% |

---

## Definition of Done

每个 Task 满足以下条件方可关闭:

```
□ 代码已提交并通过 CI（lint + typecheck + test）
□ 验收标准逐项确认通过
□ 相关文件已更新（KNOWN_ISSUES.md 标记已修复）
□ Code Review 通过（至少 1 人 Approve）
□ 无新增 TypeScript / Python 编译警告
□ QA 测试报告已归档
```

每个 Epic 满足以下条件方可关闭:

```
□ 所有 Task 状态为 Done
□ 端到端流程验证通过
□ 无已知遗留问题
□ 全团队签字确认
```

---

*本方案所有文件路径和行号基于 2026-06-15 代码库快照。如有冲突以实际代码为准。*
