# Poppler安装指南

为了让民国报纸信息提取系统能够处理PDF文件，您需要安装一个名为Poppler的开源库。Poppler提供了将PDF文件转换为图像的工具，这对于OCR处理是必需的。

## Windows用户安装指南

1. 访问 [Poppler for Windows 发布页面](https://github.com/oschwartz10612/poppler-windows/releases/) 下载最新版本
2. 下载最新的zip文件（例如：`Release-xx.xx.x-0.zip`）
3. 解压缩下载的文件到一个容易找到的位置，例如 `C:\poppler-xx.xx.x`
4. 有两种方式配置Poppler路径：

### 方法一：添加到系统PATH（推荐）

1. 右键点击"此电脑"或"我的电脑"，选择"属性"
2. 点击"高级系统设置"
3. 点击"环境变量"按钮
4. 在"系统变量"部分，找到并选择"Path"变量，然后点击"编辑"
5. 点击"新建"，添加Poppler的bin目录路径，例如 `C:\poppler-xx.xx.x\Library\bin`
6. 点击"确定"保存所有更改
7. 重启应用程序或计算机以确保更改生效

### 方法二：在.env文件中配置

1. 打开项目根目录下的`.env`文件
2. 找到`POPPLER_PATH=`这一行
3. 设置路径，例如：`POPPLER_PATH=C:\poppler-xx.xx.x\Library\bin`
4. 保存文件并重启应用程序

## Linux用户安装指南

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

### Fedora/CentOS
```bash
sudo dnf install poppler-utils
```

### Arch Linux
```bash
sudo pacman -S poppler
```

## macOS用户安装指南

使用Homebrew安装：
```bash
brew install poppler
```

## 验证安装是否成功

安装后，您可以通过以下步骤验证Poppler是否安装成功：

1. 打开命令行终端（Windows上的命令提示符或PowerShell）
2. 输入命令 `pdftoppm -h` 或 `pdfinfo -h`
3. 如果命令被识别并显示帮助信息，则表示安装成功

## 常见问题

1. **错误：找不到Poppler**
   - 确保您已正确设置PATH环境变量或在.env文件中配置了正确的路径
   - Windows用户可能需要重启计算机以使PATH更改生效

2. **错误：不支持的文件类型**
   - 这通常表示Poppler未正确安装或配置
   - 检查您的Poppler路径配置和安装

3. **错误：PDF转换失败**
   - 确保PDF文件未加密且未损坏
   - 尝试使用其他PDF阅读器打开文件，确认其可以正常查看

如果仍然遇到问题，请检查应用程序日志以获取更详细的错误信息。 