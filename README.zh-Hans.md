<div align="center">
    <img alt="icon" src="https://github.com/receyuki/stable-diffusion-prompt-reader/raw/master/sd_prompt_reader/resources/icon.png" width=20% height=20%>
    <h1>Stable Diffusion Prompt Reader</h1>
    <a href="https://github.com/receyuki/stable-diffusion-prompt-reader/releases/latest">
        <img alt="GitHub releases" src="https://img.shields.io/github/downloads/receyuki/stable-diffusion-prompt-reader/total"></a>
    <a href="https://github.com/receyuki/stable-diffusion-prompt-reader/blob/master/LICENSE">
        <img alt="GitHub" src="https://img.shields.io/github/license/receyuki/stable-diffusion-prompt-reader"></a>
    <a href="https://github.com/receyuki/stable-diffusion-prompt-reader/releases/latest">
        <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/receyuki/stable-diffusion-prompt-reader"></a>
    <a href="https://pypi.org/project/sd-prompt-reader/">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/sd-prompt-reader"></a>
    <a href="https://github.com/psf/black">
        <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
    <img alt="platform" src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey">
    <br><br>

[English](https://github.com/receyuki/stable-diffusion-prompt-reader/blob/master/README.md) | [简体中文](https://github.com/receyuki/stable-diffusion-prompt-reader/blob/master/README.zh-Hans.md)

一个独立的简易 AI 图片 prompt 查看器，用于在不依赖 webui 的情况下提取由 Stable Diffusion 生成图片内包含的 prompt
    <br>
  <p>
    <a href="#功能">功能</a> •
    <a href="#支持格式">支持格式</a> •
    <a href="#下载">下载</a> •
    <a href="#使用方式">使用方式</a> •
    <a href="#常见问题">常见问题</a> •
    <a href="#credits">Credits</a>
  </p>
    <img src="./images/screenshot_v132.png">
</div>

## 功能
- 支持 macOS、 Windows 和 Linux
- 简单的拖放交互
- 复制 prompt 到剪贴板
- 去除图片中的 prompt
- 导出 prompt 到 txt 文件
- 编辑或导入 prompt 到图片
- 竖排显示以及根据字母排序
- 检测生成工具
- 支持多种格式
- 支持系统深色和浅色模式

## 支持格式
|                                                                          | PNG | JPEG | WEBP | TXT* |
|--------------------------------------------------------------------------|:---:|:----:|:----:|:----:|
| [A1111's webUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) |  ✅  |  ✅   |  ✅   |  ✅   |
| [Easy Diffusion](https://github.com/easydiffusion/easydiffusion)         |  ✅  |  ✅   |  ✅   |      |
| [StableSwarmUI](https://github.com/Stability-AI/StableSwarmUI)*          |  ✅  |  ✅   |      |      |
| [InvokeAI](https://github.com/invoke-ai/InvokeAI)                        |  ✅  |      |      |      |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI)*                    |  ✅  |      |      |      |
| [NovelAI](https://novelai.net/)                                          |  ✅  |      |      |      |
| [Draw Things](https://drawthings.ai/)                                    |  ✅  |      |      |      |
| Naifu(4chan)                                                             |  ✅  |      |      |      |

\* 见[格式限制](#TXT).

如果你使用的工具或格式不在这个列表中，请帮助我支持你的格式：将你的工具生成的原始图片文件上传到 issues，谢谢。

## 下载
### Windows 用户
从 [GitHub Releases](https://github.com/receyuki/stable-diffusion-prompt-reader/releases/latest) 下载可执行文件
### macOS 用户
从 [GitHub Releases](https://github.com/receyuki/stable-diffusion-prompt-reader/releases/latest) 下载可执行文件
#### 通过 Homebrew Cask 安装
你也可以通过 [Homebrew](http://brew.sh/) cask 安装 SD Prompt Reader。  
```bash
brew install --no-quarantine receyuki/sd-prompt-reader/sd-prompt-reader
```
使用 `--no-quarantine` 参数是因为目前 SD Prompt Reader 并未签名，具体原因请查看[这里](https://github.com/receyuki/stable-diffusion-prompt-reader/blob/master/README.zh-Hans.md#sd-prompt-readerapp-%E5%B7%B2%E6%8D%9F%E5%9D%8F%E6%97%A0%E6%B3%95%E6%89%93%E5%BC%80%E6%82%A8%E5%BA%94%E8%AF%A5%E5%B0%86%E5%AE%83%E7%A7%BB%E5%88%B0%E5%BA%9F%E7%BA%B8%E7%AF%93)

### Linux 用户 (不定期测试)
~~我很确定 Linux 用户可以在没有可执行文件的情况下搞明白怎么用~~
- 最低Python版本要求: 3.10
- 确保你的 Python 中安装了 tkinter 包。  
如果没有，请使用软件包管理器安装 python3-tk 包。  
e.g. `sudo apt-get install python3-tk` (基于 Debian 的发行版)  

你可以选择使用 pip 进行安装或者手动运行
#### 使用 pip 或 pipx 安装
```bash
pip install sd-prompt-reader
```
or
```bash
pipx install sd-prompt-reader
```
在终端内输入 `sd-prompt-reader` 来启动 app.
#### 手动运行源码
1. Clone repo
    ```bash
    git clone https://github.com/receyuki/stable-diffusion-prompt-reader.git
    ```
   或者直接下载 repo 为 zip 格式.
2. CD 到文件夹并安装依赖
    ```bash
    cd stable-diffusion-prompt-reader  
    pip install -r requirements.txt
    ```
3. Run
    ```bash
   python main.py
   ```

## 使用方式
### 读取 prompt
- 打开可执行文件 (.exe 或 .app) 并将图片拖入窗口.

或
- 右键图片选择使用 SD Prompt Reader 作为打开方式

或
- 直接将图片拖入可执行文件 (.exe 或 .app).

### 导出 prompt 到 txt 文件
- 点击 "Export" 将在图像文件旁生成一个txt文件.
- 要保存到另一个位置，点击展开的箭头并点击 "select directory".  
![export](./images/export.png)

### 去除图片中的 prompt
- 点击 "Clear" 将在原图像文件旁生成一个后缀为"_data_removed"的图像文件.
- 要保存到另一个位置，点击展开的箭头并点击 "select directory".
- 要覆盖原始图像文件，点击展开的箭头并点击 "overwrite the original image".  
![remove](./images/remove.png)

### 编辑图片
***请注意，编辑后的图片将以 A1111 格式进行写入，这意味着任何格式的图片在编辑后都将变为 A1111 格式.***
- 点击 "Edit" 进入编辑模式
- 直接在文本框中编辑 prompt，或者导入 txt 格式的prompt数据.
- 点击 "Save" 将在原图像文件旁生成一个后缀为 "_edited" 的编辑后图像文件.
- 要保存到另一个位置，点击展开的箭头并点击 "select directory".
- 要覆盖原始图像文件，点击展开的箭头并点击 "overwrite the original image".  
![save](./images/save.png)

### 复制为单行 prompt
将图片 prompt 和设置复制为可被 [Prompts from file or textbox](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features#prompts-from-file-or-textbox) 读取的格式
支持以下参数:

| 设置                      | 参数                   |
|-------------------------|----------------------|
| Seed                    | --seed               |
| Variation seed strength | --subseed_strength   |
| Seed resize from        | --seed_resize_from_h |
| Seed resize from        | --seed_resize_from_w |
| Sampler                 | --sampler_name       |
| Steps                   | --steps              |
| CFG scale               | --cfg_scale          |
| Size                    | --width              |
| Size                    | --height             |
| Face restoration        | --restore_faces      |

- 点击展开的箭头并点击 "single line prompt".
- 将其粘贴到 webui 脚本 "Prompts from file or textbox" 下方的文本框.  
![single line prompt](./images/single_line_prompt.png)

### ComfyUI SDXL 流程
***SDXL 流程不支持编辑，如有需要请去除图片中的 prompt 后再进行编辑***  
如果图片中 workflow 包含多组 SDXL 的 prompt，
也就是 Clip G(text_g), Clip L(text_l) 和 Refiner 时，
SD Prompt Reader 会切换到如下图所示的多组 prompt 显示模式。
多组 prompt 显示模式有两种界面供你选择，你可以通过按钮来进行切换。  
![comfyui_sdxl.png](https://github.com/receyuki/stable-diffusion-prompt-reader/raw/master/images/comfyui_sdxl.png)

## 格式限制
### TXT
1. txt 文件仅能在编辑模式下导入.
2. 仅支持 A1111 格式的 txt 文件. 你可以使用 A1111 webui 生成的txt文件, 或使用 SD prompt reader 从 A1111 生成的图片中导出 txt.
### StableSwarmUI
StableSwarmUI 依然处于 Alpha 测试状态，其格式未来可能会发生改变，我将会持续跟进 StableSwarmUI 未来的更新。
### ComfyUI
***对 comfyUI 的支持需要更多测试。如果你认为你的图片不能正常显示，请将 ComfyUI 生成的原始文件以压缩文件的形式上传到 issues.***
1. 如果设置框中有多组数据(seed, steps, CFG, etc.)，这意味着流程中有多个 KSampler 节点
2. 由于 ComfyUI 的特性，workflow 中的所有节点和流程都存储在图像中，包括没有被使用的。并且一个流程可以有多个分支，多个输入和输出.
(e.g. 在一个流程中同时生成原图和 hires. fix 后的图像)
SD Prompt Reader 会遍历所有的流程和分支，并显示拥有完整的输入和输出的最长分支.
### Easy Diffusion
默认设置下, Easy Diffusion 不会将 prompt 写入图片. 请更改设置中的 _Metadata format_ 为 _embed_ 来写入 prompt 到图片中.

## 常见问题
### 病毒警告
错误的病毒警报是由我使用的打包工具 _pyinstaller_ 造成的, 这对 _pyinstaller_ 用户是一个常见的问题. 
我花费了许多时间来解决 Windows Defender 的错误警报, 但我没法对每个杀毒软件单独解决问题. 
因此, 你可以选择相信 Windows Defender 或者使用 Linux 用户的使用说明来使用 app.
### "SD Prompt Reader.app" 已损坏，无法打开。您应该将它移到废纸篓。
这是一个使用非 appstore 的未签名软件时常见的 macOS 问题, 开发者需要付给苹果每年 $99 来避免这个问题. 
你可以在设置中**隐私与安全性**的**安全性**中选择**允许任何来源**, 但这可能造成危险. 
我推荐的方式是移除 quarantine attributes.
1. 在应用程序中打开终端. 
2. 输入以下命令并按回车. 

    `xattr -r -d com.apple.quarantine app的路径`

    比如:

    `xattr -r -d com.apple.quarantine /Applications/SD\ Prompt\ Reader.app`

如果你仍然担心安全性可以选择使用 Linux 用户的使用说明来使用 app.

## 待办
- 图像批处理功能
- 多图像/文件夹模式

## Credits
- Inspired by [Stable Diffusion web UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui/)
- App icon generated using Stable Diffusion with [IconsMI](https://huggingface.co/jvkape/IconsMI-AppIconsModelforSD)
- Special thanks to [Azusachan](https://github.com/Azusachan) for providing SD server
