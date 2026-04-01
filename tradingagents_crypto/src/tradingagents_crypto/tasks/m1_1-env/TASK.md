# M1.1：环境搭建

**状态**: 🔵 就绪（未开始）
**周期**: Day 1-2
**前置依赖**: M1.0 ✅

---

## 任务目标

搭建 `tradingagents-crypto` 独立开发环境（Python 3.10），创建完整包目录结构，验证 SDK 连接。

---

## 详细子任务

### T1.1.1 创建虚拟环境
- [ ] 创建 conda 或 venv：`conda create -n tradingagents-crypto python=3.10`
- [ ] 激活环境
- [ ] 验证 Python 版本：`python --version` → 3.10.x

### T1.1.2 安装核心依赖
- [ ] `pip install hyperliquid-python-sdk>=0.3`
- [ ] `pip install pandas>=2.0 numpy>=1.25 ta>=0.10 requests>=2.31`
- [ ] `pip install tenacity>=8.2 pydantic>=2.0`
- [ ] `pip install pytest pytest-asyncio`（测试依赖）
- [ ] 创建 `requirements.txt` 锁定版本

### T1.1.3 创建包目录结构
- [ ] 创建主包目录：
  ```
  tradingagents_crypto/
  ├── __init__.py
  ├── default_config.py
  ├── dataflows/
  │   ├── __init__.py
  │   └── hyperliquid/
  │       ├── __init__.py
  │       └── ...
  ├── agents/
  │   ├── __init__.py
  │   ├── base.py
  │   └── analysts/
  │       ├── __init__.py
  │       └── ...
  └── graph/
      ├── __init__.py
      └── ...
  ```
- [ ] 在各目录创建空的 `__init__.py`
- [ ] 创建 `pyproject.toml` 或 `setup.py`

### T1.1.4 验证 SDK 连接
- [ ] 编写验证脚本 `scripts/test_hl_connection.py`：
  ```python
  from hyperliquid.info import Info
  from hyperliquid.utils import constants
  
  info = Info(constants.MAINNET_API_URL, skip_ws=True)
  mids = info.all_mids()
  assert "BTC" in mids, "Failed to connect to Hyperliquid API"
  print("✅ SDK connection verified. BTC price:", mids["BTC"])
  ```
- [ ] 运行脚本，确认输出 `BTC price: <value>`

### T1.1.5 初始化 Git（可选）
- [ ] `git init`
- [ ] 创建 `.gitignore`（参考原项目）

---

## 交付物

| 文件 | 说明 |
|------|------|
| `requirements.txt` | 依赖锁定文件 |
| `tradingagents_crypto/` | 完整包目录（含空 `__init__.py`） |
| `pyproject.toml` | 项目配置 |
| `scripts/test_hl_connection.py` | SDK 连接验证脚本 |

---

## 验收标准

- [ ] `python --version` 输出 3.10.x
- [ ] `pip list | grep hyperliquid` 显示已安装
- [ ] `python scripts/test_hl_connection.py` 输出 `BTC price: <value>`
- [ ] 包可被 import：`import tradingagents_crypto`

---

## 预计工时

- 手动操作（环境创建）：30 分钟
- 依赖安装：10 分钟
- 目录结构：15 分钟
- SDK 验证：10 分钟
- **合计**：~1.5 小时

---

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| Poetry v2 不支持 Python 3.10 | 依赖安装失败 | 使用 pip 或 conda，绕过 Poetry |
| SDK 版本变化 | API 签名改变 | 固定 `>=0.3` 版本，后续发现 breaking change 再处理 |
