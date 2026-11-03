# Agent 工作指南

适用于本仓库。参考 [andrej-karpathy-skills 的指导原则](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md)，结合项目实际流程编写。用户当前明确要求优先；本文件不是功能 roadmap，也不代表已经决定重写、迁移框架或停止某个平台的支持。

## 1. 先明确问题，再修改代码

- 先阅读相关实现、调用方和样本，区分已发布行为、本地未提交改动、用户报告与尚未验证的推测。
- 说明会影响结果的假设。普通、可逆的实现选择自行推进；只有会改变需求、兼容性或数据处理方式的实质歧义才需要澄清。
- 多步骤任务先给出简短计划及对应验证方法。小修正不需要完整设计流程。
- 对明显过大的方案提出更简单的选择。讨论中的建议、旧 TODO、旧功能分支和开放 issue 都不是自动获准实施的任务。

## 2. 保持简单

- 实现当前要求所需的最小方案，不预先增加插件系统、通用框架、配置层或推测中的功能。
- 优先复用现有解析器、CLI 和数据结构。不要因局部修复而迁移 GUI、包管理器或构建工具。
- 新格式通常放在 `sd_prompt_reader/format/`；格式判断在 `ImageDataReader` 中接入，避免把解析逻辑塞进 GUI 回调。
- 解析逻辑应能脱离 GUI 使用；不要为核心解析新增 Tk、剪贴板、网络或平台专属依赖。不要在无关任务中顺带完成整个依赖拆分。

## 3. 只做必要改动

- 开始前检查 `git status --short` 和相关 diff，保留用户已有的 staged、unstaged 和 untracked 工作。不要擅自 reset、清理、覆盖或提交它们。
- 遵循现有代码风格；项目使用 Black。只格式化本次涉及的文件，不做全仓库格式化。
- 清理本次修改导致的无用代码；发现原有无关问题时报告，不顺手重构。
- 不修改相邻的 `comfyui-prompt-reader-node` 仓库或它的子模块副本，除非任务明确包含该范围。可以只读检查下游调用。
- 不把 `venv/`、`.idea/`、`build/`、`dist/`、临时图片或打包产物当作源码修改对象。

## 4. 用可验证的结果完成任务

- 修复解析或文件读写行为时，先用样本或最小复现确认问题，再增加针对该行为的回归测试。
- 测试预期应来自格式说明、原始元数据或人工核对，不能仅复制当前实现的输出；不要为了通过测试而批量重生成预期文件。
- 先运行相关测试。修改格式识别、公共基类或共享辅助函数时，再运行格式回归套件。
- 文案和纯文档改动通常只检查内容、路径和 diff，不为它们新增测试或重复运行无关套件。
- 验证失败时区分代码问题、依赖问题和缺少样本，不用跳过断言或扩大异常捕获掩盖失败。
- 完成后说明改了什么、实际执行了哪些验证、哪些平台或流程尚未验证。构建成功不等于 GUI 可用，旧样本通过不等于支持所有新格式。

## 项目结构与兼容性

| 路径 | 职责 |
| --- | --- |
| `sd_prompt_reader/image_data_reader.py` | 图片读取、格式识别、解析入口、元数据保存 |
| `sd_prompt_reader/format/base_format.py` | 解析器公共属性、参数和状态 |
| `sd_prompt_reader/format/*.py` | 各生成工具的格式解析 |
| `sd_prompt_reader/cli.py` | Click CLI、文件和目录处理 |
| `sd_prompt_reader/app.py`、`*_viewer.py` 等 | CustomTkinter GUI 与交互 |
| `sd_prompt_reader/utility.py`、`constants.py` | 当前共享辅助函数、常量及 GUI 资源配置 |
| `pyproject.toml`、`requirements.txt` | Python 包声明与运行/打包依赖 |
| `setup.py`、`win.spec` | macOS py2app、Windows PyInstaller 构建 |
| `tests/` | 本地格式样本、预期 JSON、pytest 测试与实验脚本 |

- `ImageDataReader` 不仅供桌面程序使用，也被 CLI 和 ComfyUI 节点调用。修改属性名、类型、状态、参数字典键或导出结构前，检查这些调用方；不能把现有 API 当成 GUI 内部实现随意改动。
- 为新格式增加字段兼容时保留旧样本，例如支持新旧模型名称字段。不要仅因上游更新就删除旧格式支持。
- 基于图片实际携带的数据解析，不根据模型名猜测字段，不从像素内容臆造 prompt。ComfyUI 的未知节点、多分支与部分结果应明确表达，不能把未识别内容伪装成完整解析成功。
- 图片元数据是外部输入。解析它，不执行其中的代码，也不为解析任意工作流而自动安装或运行自定义节点。
- 编辑、导出、清除测试使用临时目录和样本副本。验证目标文件可重新读取，检查元数据与像素/透明度等本次操作需要保留的内容；不要覆盖原始样本。
- 清除普通 PNG/EXIF 字段不等于清除 NovelAI stealth 信息。涉及清除功能时，必须覆盖隐藏信息的复读检查。
- 修复保存逻辑时，失败应传递到调用方，不能仍显示成功或计入成功数量。

## 本地运行与测试

不依赖 PyCharm 才能工作。先检查解释器和依赖，优先使用本项目可用的虚拟环境，不直接使用 PATH 中不明来源的全局 Python，也不升级全局环境。

当前开发目录保留了 `venv/`，已验证的旧环境是 Python 3.11.2、pytest 8.2.1、Pillow 10.3.0；这是本地基线，不是未来版本锁定要求，也不能假定新 checkout 一定存在。

以下命令从仓库根目录执行，适用于当前 macOS/Linux 目录布局；Windows 对应解释器路径为 `venv\Scripts\python.exe`，环境变量语法按 shell 调整。

```sh
# 确认实际解释器与测试工具
venv/bin/python --version
venv/bin/python -m pytest --version

# 明确选择 CLI 或 GUI 入口
venv/bin/python -m sd_prompt_reader.cli --help
venv/bin/python -m sd_prompt_reader.app
```

`main.py` 会根据 stdin/TTY 状态选择 CLI 或 GUI；需要验证某个入口时使用上面的显式模块命令。PyCharm 配置在 `.idea/workspace.xml`，可以参考其中的参数和工作目录，但旧配置可能引用已经不存在的文件。

格式回归测试要求以 `tests/` 为工作目录，并显式把仓库根目录加入导入路径：

```sh
(
  cd tests
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. ../venv/bin/python -m pytest -q -p no:cacheprovider \
    a1111 comfyui drawthings easydiffusion fooocus invokeai novelai swarmui ruinedfooocus maintenance
)
```

- 2026-11-04 在原开发环境执行上述套件（格式解析及维护回归）得到 279 项通过。任务完成时报告本次实际结果，不引用这个历史数字代替验证。
- 单格式修复可把目录列表缩减为对应目录。不要默认对整个 `tests/` 做无差别收集：`misc/` 等含 GUI 实验和手工脚本。
- **旧格式样本与测试仍被 Git 忽略；`.gitignore` 为 `tests/ruinedfooocus/` 的指定测试、样本、说明文件及 `tests/maintenance/test_clear.py` 开放例外。** 新 checkout 或 CI 不能假设拥有完整本地套件。新增回归测试时安排可提交的测试与最小样本，必要时局部调整忽略规则；不要把整套本地资料强制加入 Git，也不要擅自暂存文件。
- `tests/generator/testGenerator.py` 会根据当前解析器输出生成并写入预期 JSON 和测试脚本，不是只读测试命令，不要盲目执行。
- CLI 写入/清除、GUI 拖放/保存和跨平台启动需要各自验证；格式套件不覆盖这些完整流程。

## 依赖与打包

- 修改依赖前同时检查 `pyproject.toml`、`requirements.txt`、锁文件和打包配置的用途。运行依赖与平台构建依赖不同，避免无关锁文件重写或把版本全部升级到最新。
- Python 支持范围要与依赖 wheel、实际安装测试一致。旧环境能运行不能证明新的 Python 版本也能安装。
- 只有构建/发布任务才执行打包，不把 `setup.py` 用作普通测试或环境检查。
- macOS 的现有构建入口是 `venv/bin/python setup.py py2app`；Windows 是 `venv\Scripts\python.exe setup.py`。先检查当前脚本和依赖，再在隔离输出或临时副本中验证，保留原有产物。
- 当前 `setup.py` 会写入 `sd_prompt_reader/__version__.py`；macOS 流程还复制 Tcl/Tk，并调用 `poetry add` 修改依赖文件。执行前考虑这些副作用，执行后核对 diff，不混入非预期变化。
- `win.spec` 包含本地依赖路径；`whl/` 有 Pillow 双架构合并和 PyInstaller bootloader 构建脚本。只在相关构建需要时检查、使用，不默认重建或安装这些产物。
- 本地 `dist/dev.sh` 会删除旧产物并重命名应用，不是通用、安全的只读发布检查命令。
- Windows 产物在 Windows 环境验证；macOS universal 产物需要检查依赖架构并分别验证目标架构。不能用当前 Mac 上的测试结果代替这些验证。
- 构建、GUI 冒烟测试、安装包制作、签名/公证和上传发布是不同步骤。按任务范围执行，未经发布授权不创建 tag 或上传 release；只报告实际完成的步骤。

## 交付检查

- 检查新增文件是否被忽略，以及本次 diff 是否只包含任务所需修改；保留原有工作区状态。
- 行为、安装方式或格式支持改变时，同步相关文档；涉及用户说明时兼顾 `README.md` 与 `README.zh-Hans.md`，不要声称尚未验证的兼容性。
- README 沿用原有简短说明、列表和示例风格，控制篇幅；changelog 沿用 GitHub Releases 的 `Changes since …` 列表，commit message 优先使用 `Add / Fix / Update` 短句，必要时补充简短正文。
- 默认用中文向用户简洁说明结果，沿用仓库现有代码、标识符与注释风格。不要未经要求修改版本号、提交、推送或发布。
