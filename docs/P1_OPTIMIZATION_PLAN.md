# P1 优化执行计划

## 方案 A：渐进式优化

### 阶段一：安全加固
1. **token_version 字段实现 token 撤销**
   - User 模型添加 token_version 字段
   - JWT payload 包含 token_version
   - 修改密码时递增 token_version
   - 验证 token 时检查版本匹配

2. **slowapi 速率限制**
   - 添加 slowapi 依赖
   - 配置可配置的限制参数
   - 应用到登录/注册端点
   - 应用到生成端点

3. **视频轮询最小间隔**
   - 前端添加 3 秒最小轮询间隔
   - 防止过度请求

### 阶段二：代码清理
4. **删除 agnes_ai.py 重复常量**
   - 从 config.py 导入，删除本地定义

5. **删除 api/images.py 重复 schema**
   - 复用 schemas/image.py 中的定义

6. **修复前端 Profile 页面 any 类型**
   - 添加 TypeScript 接口定义

### 阶段三：基础设施
7. **添加 pyproject.toml**
   - 统一 Python 项目配置
   - 包含开发依赖

8. **SQLite 并发警告**
   - 检测 SQLite + 多 worker 配置
   - 输出警告日志

9. **日志级别环境变量**
   - 从环境变量读取 LOG_LEVEL
   - 支持 DEBUG/INFO/WARNING/ERROR

## 验证标准
- [ ] 修改密码后旧 token 失效
- [ ] 速率限制生效（超出返回 429）
- [ ] 视频轮询有最小间隔
- [ ] 代码无重复定义
- [ ] 前端无 any 类型警告
- [ ] pyproject.toml 可用
- [ ] 日志级别可配置
