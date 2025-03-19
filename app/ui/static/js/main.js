/**
 * 报纸阅读与信息提取系统
 * 主JavaScript文件
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 上传区域拖放功能
    setupFileDragDrop();
    
    // 图片预览功能
    setupImagePreview();
    
    // 报纸页面导航
    setupPageNavigation();
});

/**
 * 设置文件拖放上传功能
 */
function setupFileDragDrop() {
    const dropArea = document.querySelector('.upload-area');
    if (!dropArea) return;
    
    // 阻止浏览器默认拖放行为
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // 高亮显示拖放区域
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('border-primary');
    }
    
    function unhighlight() {
        dropArea.classList.remove('border-primary');
    }
    
    // 处理文件拖放
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const fileInput = document.getElementById('file');
            if (fileInput) {
                fileInput.files = files;
                
                // 触发change事件，以便预览和表单验证
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        }
    }
}

/**
 * 设置图片预览功能
 */
function setupImagePreview() {
    const fileInput = document.getElementById('file');
    const previewContainer = document.getElementById('preview-container');
    
    if (!fileInput || !previewContainer) return;
    
    fileInput.addEventListener('change', function() {
        // 清除现有预览
        previewContainer.innerHTML = '';
        
        const file = this.files[0];
        if (!file) return;
        
        // 检查文件类型
        if (file.type.match('image.*')) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'img-fluid';
                img.alt = file.name;
                
                previewContainer.appendChild(img);
            };
            
            reader.readAsDataURL(file);
        } else if (file.type === 'application/pdf') {
            // PDF预览（简单显示PDF图标）
            const pdfIcon = document.createElement('div');
            pdfIcon.className = 'text-center p-4';
            pdfIcon.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" class="bi bi-file-earmark-pdf text-danger" viewBox="0 0 16 16">
                    <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                    <path d="M4.603 14.087a.81.81 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645 19.697 19.697 0 0 0 1.062-2.227 7.269 7.269 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.712 5.712 0 0 1-.911-.95 11.651 11.651 0 0 0-1.997.406 11.307 11.307 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.793.793 0 0 1-.58.029zm1.379-1.901c-.166.076-.32.156-.459.238-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361.01.022.02.036.026.044a.266.266 0 0 0 .035-.012c.137-.056.355-.235.635-.572a8.18 8.18 0 0 0 .45-.606zm1.64-1.33a12.71 12.71 0 0 1 1.01-.193 11.744 11.744 0 0 1-.51-.858 20.801 20.801 0 0 1-.5 1.05zm2.446.45c.15.163.296.3.435.41.24.19.407.253.498.256a.107.107 0 0 0 .07-.015.307.307 0 0 0 .094-.125.436.436 0 0 0 .059-.2.095.095 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a3.876 3.876 0 0 0-.612-.053zM8.078 7.8a6.7 6.7 0 0 0 .2-.828c.031-.188.043-.343.038-.465a.613.613 0 0 0-.032-.198.517.517 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822.024.111.054.227.09.346z"/>
                </svg>
                <p class="mt-2">${file.name}</p>
            `;
            
            previewContainer.appendChild(pdfIcon);
        }
    });
}

/**
 * 设置报纸页面导航功能
 */
function setupPageNavigation() {
    const pageLinks = document.querySelectorAll('.page-nav-link');
    const contentFrame = document.getElementById('page-content-frame');
    
    if (!pageLinks.length || !contentFrame) return;
    
    pageLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除当前活动页的标记
            document.querySelector('.page-nav-link.active')?.classList.remove('active');
            
            // 标记当前页为活动状态
            this.classList.add('active');
            
            // 加载新页面内容
            const targetUrl = this.getAttribute('href');
            
            // 显示加载指示器
            contentFrame.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-2">加载中...</p>
                </div>
            `;
            
            // 使用fetch加载页面内容
            fetch(targetUrl)
                .then(response => response.text())
                .then(html => {
                    contentFrame.innerHTML = html;
                })
                .catch(error => {
                    contentFrame.innerHTML = `<div class="alert alert-danger">加载失败: ${error.message}</div>`;
                });
        });
    });
    
    // 默认加载第一个页面
    pageLinks[0]?.click();
}

/**
 * 全文内容搜索高亮
 * @param {string} searchText 要高亮的搜索文本
 */
function highlightSearchText(searchText) {
    if (!searchText || searchText.trim() === '') return;
    
    const articleContent = document.querySelector('.article-content');
    if (!articleContent) return;
    
    // 简单的文本替换方式，实际项目可能需要更复杂的实现
    const content = articleContent.innerHTML;
    const regex = new RegExp(searchText, 'gi');
    
    articleContent.innerHTML = content.replace(regex, match => `<mark>${match}</mark>`);
}

/**
 * 显示确认对话框
 * @param {string} message 确认消息
 * @param {Function} callback 确认后的回调函数
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
} 