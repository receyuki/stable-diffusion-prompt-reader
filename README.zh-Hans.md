<div align="center">
    <img src="/resources/icon.png" width=20% height=20%>
    <h1>Stable Diffusion Prompt Reader</h1>
    <a href="https://github.com/receyuki/stable-diffusion-prompt-reader/releases/latest">
        <img alt="GitHub releases" src="https://img.shields.io/github/downloads/receyuki/stable-diffusion-prompt-reader/total"></a>
    <a href="https://github.com/receyuki/stable-diffusion-prompt-reader/blob/master/LICENSE">
        <img alt="GitHub" src="https://img.shields.io/github/license/receyuki/stable-diffusion-prompt-reader"></a>
    <a href="https://github.com/receyuki/stable-diffusion-prompt-reader/releases/latest">
        <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/receyuki/stable-diffusion-prompt-reader"></a>
        <img src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey">
    <br>
    一个独立的简易查看器，用于在 webui 之外读取由 Stable Diffusion 生成图片内包含的 prompt
    <br>
    <img src="/images/screenshot.png" width=80% height=80%>
</div>

## 功能
- 支持 macOS、 Windows 和 Linux
- 简单的拖放互动
- 复制 prompt 到剪贴板
- 支持多种格式

## 支持格式
|               | PNG | JPEG | WEBP |
|---------------|:---:|:----:|:----:|
| A1111's webui |  ✅  |  ✅   |  ✅   |
| NovelAI       |  ✅  |  ❎   |  ❎   |
| Naifu(4chan)  |  ✅  |  ❎   |  ❎   |

如果你使用的工具或格式不在这个列表中，请帮助我支持你的格式：将你的工具生成的原始图片文件压缩并上传到 issues，谢谢。

## 下载
### macOS 和 Windows 用户
从 [GitHub Releases](https://github.com/receyuki/stable-diffusion-prompt-reader/releases/latest) 下载可执行文件
### Linux 用户 (不定期测试)
~~我很确定 Linux 用户可以在没有可执行文件的情况下搞明白怎么用~~
1. 确保你的 Python 中安装了 tkinter 包。
如果没有，请使用软件包管理器安装 python3-tk 包。  
e.g. `sudo apt-get install python3-tk` (基于 Debian 的发行版)
2. Clone repo
    ```bash
    git clone https://github.com/receyuki/stable-diffusion-prompt-reader.git
    ```
   或者直接下载 repo 为 zip 格式.
3. CD 到文件夹并安装依赖
    ```bash
    cd stable-diffusion-prompt-reader  
    pip install -r requirements.txt
    ```
4. Run
    ```bash
   python main.py
   ```

## 待办
- 一键移除图片中的 prompt
- 添加更多格式支持
- 优化设置显示框
- 导出 prompt 为txt格式

## Credits
- Inspired by [Stable Diffusion web UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui/)
- Function icons from [Icons8](https://icons8.com/)
- App icon generated using [IconsMI](https://huggingface.co/jvkape/IconsMI-AppIconsModelforSD)
- Special thanks to [Azusachan](https://github.com/Azusachan) for providing SD server
