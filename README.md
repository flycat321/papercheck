# 民国报纸信息提取系统

一个基于OCR技术自动从民国时期报纸图像和PDF文件中提取文本信息的系统。

![系统界面](docs/images/system_preview.png)

## 项目简介

民国报纸信息提取系统是一款专为研究民国时期历史和文献的学者、档案馆工作人员以及相关研究人员设计的辅助工具。系统利用现代OCR技术，能够从扫描的民国报纸图像或PDF文件中自动识别并提取文字内容，便于历史资料的数字化和研究。

### 主要功能

- **文本自动提取**：支持从图片和PDF文件中自动提取文字内容
- **报纸版面结构识别**：自动识别报纸的标题、正文、日期等信息
- **全文检索**：对识别后的文本内容进行全文检索
- **关键词提取**：自动提取报纸文章中的关键词
- **批量处理**：支持批量处理多份报纸文件
- **用户友好界面**：直观的Web界面，方便操作和查看结果

## 技术架构

- **前端**：HTML, CSS, JavaScript, Bootstrap
- **后端**：Flask (Python Web框架)
- **OCR引擎**：PaddleOCR（针对中文识别进行优化）
- **数据库**：SQLite (通过SQLAlchemy ORM访问)
- **PDF处理**：pdf2image + Poppler
- **自然语言处理**：jieba分词

## 安装指南

### 系统要求

- Python 3.8+
- 操作系统：Windows, Linux, macOS
- 内存：建议4GB+
- 硬盘空间：根据需处理的报纸数量，建议10GB+

### 安装步骤

1. **克隆项目仓库**

```bash
git clone https://github.com/你的用户名/民国报纸信息提取系统.git
cd 民国报纸信息提取系统
```

2. **创建虚拟环境**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **安装Poppler (用于PDF处理)**

- **Windows**: 下载[Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)，解压后将bin目录添加到系统PATH环境变量，或在`.env`文件中设置`POPPLER_PATH`
- **Linux**: `sudo apt-get install poppler-utils`
- **macOS**: `brew install poppler`

更多详细信息，请参考[Poppler安装说明](poppler安装说明.md)。

5. **配置环境变量**

复制`.env.example`文件为`.env`，并根据需要修改配置：

```bash
cp .env.example .env
```

主要配置项：
- `DB_PATH`：数据库路径
- `USE_GPU`：是否使用GPU加速OCR（如有NVIDIA GPU且已安装CUDA）
- `POPPLER_PATH`：Poppler的安装路径（仅Windows需要）
- `SECRET_KEY`：Flask应用密钥，请修改为随机字符串

6. **初始化数据库**

```bash
python -c "from app.database import init_db; init_db()"
```

## 使用指南

### 启动系统

```bash
python app/main.py
```

然后在浏览器中访问 http://localhost:5000

### 上传报纸文件

1. 点击"上传"按钮
2. 选择要处理的报纸图片或PDF文件
3. 输入报纸名称（可选）
4. 点击"上传并处理"按钮
5. 等待处理完成

### 查看内容

- 在首页可以查看最近处理的报纸列表
- 点击报纸名称查看详细信息和所有页面
- 点击页面查看OCR识别的文本内容和提取的文章
- 点击文章查看详细内容和关键词

### 搜索信息

1. 点击顶部导航栏的"搜索"
2. 输入搜索关键词
3. 选择搜索类型（内容或关键词）
4. 点击"搜索"按钮
5. 查看匹配的文章列表

### API使用

系统提供了简单的API接口，可用于集成到其他系统：

- `POST /api/ocr`：上传并处理报纸文件
- `GET /api/search?q=关键词&type=content`：搜索文章

## 维护与高级设置

### 数据备份

定期备份`data/newspaper.db`文件可以保护您的数据：

```bash
# 示例：备份数据库
cp data/newspaper.db data/newspaper_backup_$(date +%Y%m%d).db
```

### 自定义字典

如果需要识别特定的民国时期词汇，可以创建自定义词典：

1. 创建`dictionaries/custom.txt`文件
2. 每行添加一个词条
3. 在`app/ocr_handler.py`中取消注释并更新以下行：
   ```python
   jieba.load_userdict("dictionaries/custom.txt")
   ```

### OCR参数调整

如需调整OCR识别参数，可以修改`app/ocr_handler.py`中PaddleOCR初始化参数：

```python
self.ocr = PaddleOCR(
    use_gpu=use_gpu,
    lang="ch",  # 中文
    use_angle_cls=True,  # 使用角度分类器
    det_db_box_thresh=0.5,  # 检测框阈值，可以尝试调整
    # 其他参数...
)
```

## 常见问题解答

**Q: 为什么我上传的PDF文件无法处理？**  
A: 确保已正确安装Poppler并在`.env`文件中设置了`POPPLER_PATH`（Windows用户）。另外，请确保PDF文件是真正的文本PDF，而不是只包含扫描图像的PDF。

**Q: OCR识别效果不理想怎么办？**  
A: 民国时期的报纸因字体和印刷质量问题可能影响识别率。可以尝试：
1. 提高原始扫描图像的质量和分辨率
2. 在上传前对图像进行预处理（提高对比度、去除噪点等）
3. 调整OCR参数或使用自定义字典增强识别效果

**Q: 系统支持繁体字识别吗？**  
A: 是的，PaddleOCR支持繁体中文识别。默认配置应该能够处理大多数民国时期的繁体字报纸。

## 贡献指南

欢迎对本项目做出贡献！贡献方式包括：

1. 提交Issue报告bug或提出新功能建议
2. 提交Pull Request改进代码或文档
3. 完善自定义字典，提高民国时期特殊词汇的识别率

## 许可证

本项目采用MIT许可证。详情请参见[LICENSE](LICENSE)文件。

## 致谢

感谢以下开源项目：
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Flask](https://flask.palletsprojects.com/)
- [pdf2image](https://github.com/Belval/pdf2image)
- [jieba](https://github.com/fxsjy/jieba)

## 联系方式

如有任何问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送电子邮件至：[your-email@example.com]

---

© 2025 民国报纸信息提取系统 