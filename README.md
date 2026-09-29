# 若依系统自动化测试项目

[![RuoYi automation CI/CD](https://github.com/chunyingw909-code/ruoyi_test/actions/workflows/ci.yml/badge.svg)](https://github.com/chunyingw909-code/ruoyi_test/actions/workflows/ci.yml)

基于 pytest、requests、Playwright 和 Allure 的若依管理系统自动化测试项目。

## 建设原则

1. **接口自动化为主**：业务规则、异常分支、数据增删改查优先通过 API 覆盖。
2. **UI 自动化为辅**：只覆盖登录、关键业务主路径和必须由浏览器验证的交互。
3. **测试类型优先、业务模块次之**：测试先分 API/UI，再在各自目录内按业务模块扩展。
4. **测试数据可隔离**：自动创建的数据使用唯一 `AUTOTEST-` 前缀，并按唯一 ID 清理。
5. **前置优先走接口**：若 UI 动作本身不是测试目标，使用 API 准备和清理数据。

## 项目结构

```text
api/
  auth/                 # 认证接口封装
  system/               # 系统管理接口封装
pages/
  auth/                 # 认证页面对象
  system/               # 系统管理页面对象
data/
  auth/                 # 认证模块参数化数据
  system/               # 系统管理参数化数据
testcases/
  api/                   # 主测试集：业务规则和数据流
    auth/                # 认证接口用例
    system/user/         # 用户管理接口用例及专属前置
  ui/                    # 辅助测试集：关键用户路径
    auth/                # 登录页面核心用例
    system/user/         # 用户管理页面核心用例及页面前置
common/                  # 跨模块公共能力
config/                  # 环境配置
```

新增模块时沿用相同路径。例如角色管理使用 `api/system/role_api.py`、
`pages/system/role_page.py`、`data/system/role_*.yaml` 和
`testcases/api/system/role/`；只有需要浏览器验证的核心路径才增加
`testcases/ui/system/role/`。

## 分层约定

- `api/`：只封装接口请求，不写测试断言。
- `pages/`：固定定位器放在 Page Object 的 `__init__`；仅复合操作和动态定位写方法。
- 根 `conftest.py`：管理 API/UI 共用的认证、唯一数据和安全清理能力。
- 模块 `conftest.py`：只管理该测试类型、该模块专属的 Fixture。
- `testcases/api/`：优先覆盖协议结果、业务结果和数据落库结果。
- `testcases/ui/`：保留用户可见结果断言，不重复大批接口异常组合。

## 接口用例断言层次

接口自动化通过 `requests.Session` 直接向后端发 HTTP 请求，不经过浏览器。每条关键
接口通常按以下层次断言：

1. HTTP 状态，例如 `response.status_code == 200`。
2. 业务状态和消息，例如 `response['code']`、`response['msg']`。
3. 响应结构和关键字段，例如 token、当前账号、角色、权限和路由。
4. 后续业务效果，例如 token 能否访问认证资源、退出后是否立即失效、增删改后重新
   查询的数据是否正确。

若依的部分业务失败仍返回 HTTP 200，因此不能只检查 HTTP 状态。公共客户端返回的
`ApiResponse` 同时保留 `status_code` 和 JSON 响应体，并兼容字典式取值。

当前登录模块已经覆盖：成功登录、错误/缺失凭据、验证码配置、有效/无效 token、
当前用户信息、菜单路由和退出登录；UI 只覆盖登录页展示、密码掩码、记住密码控件、
成功登录及必要的表单错误。

当前用户管理模块的 API 已覆盖：列表筛选与分页、详情、部门树、新增及字段校验、
修改、启停、重置密码、单个/批量删除、导入模板、Excel 导入和筛选导出。UI 只保留
页面结构、查询重置、新增校验、编辑、启停、删除、导入和导出这些关键用户路径。

当前角色管理模块的 API 已覆盖：列表筛选与分页、详情、新增及重复校验、修改、启停、
菜单树、自定义数据权限、用户单个/批量分配与取消、单个/批量删除和筛选导出。UI 只
保留页面结构、查询重置、新增校验、编辑、启停、数据权限、删除和导出这些关键路径。

## 环境配置

默认配置位于 `config/config.yaml`：

- API：`http://localhost:8080`
- UI：`http://localhost:81`
- 管理员：`admin / admin123`

CI 可通过 `BASE_URL`、`UI_URL`、`ADMIN_USERNAME` 和 `ADMIN_PASSWORD`
环境变量覆盖本地配置。

## CI/CD

GitHub Actions 会在临时 Ubuntu Runner 中通过 Docker Compose 启动 MySQL、Redis、
若依后端和前端，随后依次执行 API 与 UI 测试。测试结果、Docker 日志会作为构建产物
保存；主分支测试通过后，Allure 报告会自动部署到 GitHub Pages。

流水线支持 push、PR、手动运行和每日定时运行，配置见
`.github/workflows/ci.yml`。

## 运行方式

```powershell
pip install -r requirements.txt

# 默认优先运行接口用例
pytest -m api

# 运行关键 UI 用例；CI=1 时 Chromium 使用无头模式
$env:CI='1'
pytest -m ui

# 运行全部用例
pytest

# 查看报告
allure serve ./allure-results
```
