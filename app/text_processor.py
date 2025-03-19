import re
import jieba
import jieba.analyse
import logging
from datetime import datetime
import numpy as np
from collections import Counter

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Text_Processor")

class TextProcessor:
    """文本处理类，用于分析报纸中的文本内容"""
    
    def __init__(self, custom_dict_path=None):
        """
        初始化文本处理器
        
        Args:
            custom_dict_path: 自定义词典路径，可以包含民国时期特有词汇
        """
        # 加载自定义词典
        if custom_dict_path:
            jieba.load_userdict(custom_dict_path)
        
        # 初始化停用词表（可以根据需要扩充）
        self.stopwords = set([
            "的", "了", "和", "是", "在", "有", "与", "为", "以", "之",
            "于", "不", "也", "而", "其", "中", "此", "又", "等", "被"
        ])
        
        logger.info("文本处理器初始化完成")
    
    def extract_keywords(self, text, top_k=10):
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
            top_k: 提取的关键词数量
            
        Returns:
            关键词列表及其权重
        """
        # 使用TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
        return keywords
    
    def extract_date(self, text):
        """
        从文本中提取日期信息
        
        Args:
            text: 输入文本
            
        Returns:
            提取的日期（datetime对象）或None
        """
        # 尝试匹配各种可能的日期格式
        # 1. 民国年份格式，如"民国十五年五月三日"
        minguo_match = re.search(r'民国[一二三四五六七八九十百零〇]{1,4}年[一二三四五六七八九十]{1,2}月[一二三四五六七八九十]{1,2}[日号]', text)
        if minguo_match:
            try:
                date_str = minguo_match.group(0)
                # 将中文数字转换为阿拉伯数字
                # 这里需要实现一个中文数字到阿拉伯数字的转换函数
                # 简化起见这里略过实现
                return None  # 替换为实际转换结果
            except Exception as e:
                logger.error(f"处理民国日期出错: {e}")
                
        # 2. 阿拉伯数字格式，如"1926年5月3日"或"1926-5-3"
        arabic_match = re.search(r'(\d{2,4})[年/-](\d{1,2})[月/-](\d{1,2})[日号]?', text)
        if arabic_match:
            try:
                year, month, day = map(int, arabic_match.groups())
                # 处理民国年份或其他特殊年份格式
                if year < 100:
                    # 假设是民国年份，转换为公元年份
                    year += 1911
                return datetime(year, month, day).date()
            except ValueError as e:
                logger.error(f"处理数字日期出错: {e}")
        
        return None
    
    def segment_text(self, text):
        """
        对文本进行分词
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果列表
        """
        words = jieba.cut(text)
        # 去除停用词
        filtered_words = [word for word in words if word and word not in self.stopwords]
        return filtered_words
    
    def extract_named_entities(self, text):
        """
        从文本中提取命名实体（人名、地名、机构名等）
        
        Args:
            text: 输入文本
            
        Returns:
            命名实体列表，按类型分组
        """
        # 此功能需要更高级的NLP库支持，如HanLP或者百度LAC
        # 这里使用简化的实现
        
        # 人名识别（简化，仅基于常见姓氏前缀）
        common_surnames = ["张", "王", "李", "赵", "钱", "孙", "周", "吴", "郑", "陈"]
        words = self.segment_text(text)
        
        # 简单的人名识别（以常见姓氏开头，长度2-3的词）
        potential_names = []
        for word in words:
            if len(word) in [2, 3] and any(word.startswith(surname) for surname in common_surnames):
                potential_names.append(word)
        
        # 简单的地名识别（以"省"、"市"、"县"等结尾的词）
        potential_locations = []
        location_suffixes = ["省", "市", "县", "区", "镇", "村", "街", "路"]
        for word in words:
            if any(word.endswith(suffix) for suffix in location_suffixes):
                potential_locations.append(word)
        
        # 简单的机构名识别（包含"局"、"部"、"会"等的词）
        potential_organizations = []
        org_keywords = ["局", "部", "会", "院", "所", "校", "厂"]
        for word in words:
            if any(keyword in word for keyword in org_keywords) and len(word) >= 3:
                potential_organizations.append(word)
        
        return {
            "人名": list(set(potential_names)),
            "地名": list(set(potential_locations)),
            "机构": list(set(potential_organizations))
        }
    
    def categorize_content(self, text):
        """
        对文本内容进行分类
        
        Args:
            text: 输入文本
            
        Returns:
            可能的文章类别
        """
        # 简单的基于关键词的分类
        categories = {
            "政治": ["政府", "总统", "国家", "政策", "法律", "党", "军事", "战争", "军队"],
            "经济": ["经济", "商业", "贸易", "货币", "银行", "产业", "市场", "价格", "金融"],
            "社会": ["社会", "民众", "生活", "教育", "文化", "艺术", "风俗", "习惯"],
            "国际": ["国际", "外交", "条约", "外国", "世界", "洋人", "欧洲", "美国", "日本"]
        }
        
        # 分词
        words = self.segment_text(text)
        word_counts = Counter(words)
        
        # 计算每个类别的匹配度
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(word_counts.get(keyword, 0) for keyword in keywords)
            category_scores[category] = score
        
        # 返回得分最高的类别（如果有足够的匹配词）
        max_category = max(category_scores.items(), key=lambda x: x[1])
        if max_category[1] > 0:
            return max_category[0]
        else:
            return "其他"
    
    def extract_article_structure(self, text):
        """
        提取文章的结构（标题、正文、署名等）
        
        Args:
            text: 输入文本
            
        Returns:
            文章结构字典
        """
        lines = text.split('\n')
        
        # 去除空行
        lines = [line.strip() for line in lines if line.strip()]
        
        if not lines:
            return {
                "title": "",
                "content": "",
                "author": "",
                "source": ""
            }
        
        # 假设第一行是标题
        title = lines[0]
        
        # 尝试找出作者署名（通常在文章末尾）
        author = ""
        source = ""
        
        # 寻找可能的署名格式，如"(作者：XXX)"、"【XXX报导】"等
        for line in lines[-3:]:  # 查看最后几行
            author_match = re.search(r'[（(【［][记者|作者|编辑]?[:：]?\s*([^）)】］]+)[）)】］]', line)
            if author_match:
                author = author_match.group(1).strip()
            
            source_match = re.search(r'来源[:：]?\s*([^\s]+)', line)
            if source_match:
                source = source_match.group(1).strip()
        
        # 正文内容（除去标题和最后可能包含署名的行）
        content = '\n'.join(lines[1:])
        
        return {
            "title": title,
            "content": content,
            "author": author,
            "source": source
        }
    
    def analyze_sentiment(self, text):
        """
        简单的情感分析
        
        Args:
            text: 输入文本
            
        Returns:
            情感倾向（正面、负面或中性）
        """
        # 简化的情感词典
        positive_words = [
            "好", "正", "优", "佳", "美", "赞", "成功", "进步", "胜利", "繁荣",
            "发展", "提高", "增长", "改善", "幸福", "和平", "稳定"
        ]
        
        negative_words = [
            "坏", "差", "劣", "败", "负", "失败", "衰退", "下降", "危机", "困难",
            "问题", "冲突", "战争", "灾害", "贫困", "腐败", "混乱"
        ]
        
        # 分词
        words = self.segment_text(text)
        
        # 计算正面和负面词的出现次数
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # 确定情感倾向
        if positive_count > negative_count:
            return "正面"
        elif negative_count > positive_count:
            return "负面"
        else:
            return "中性"

# 单独测试
if __name__ == "__main__":
    processor = TextProcessor()
    
    # 测试文本
    test_text = """
    中华民国十五年五月三日
    
    经济困难之原因与对策
    
    近来全国商业不振，市场萧条，物价下跌，百业凋敝，民生困苦。
    究其原因，一则战乱频仍，道路不通；二则外货倾销，本国工业难与竞争；
    三则货币贬值，金融紊乱。凡此种种，皆为经济困难之症结所在。
    
    欲振兴经济，必须首先恢复和平，稳定政局，整顿交通，保障商旅。
    其次当发展实业，保护国货，使本国产业得以发达。
    最后则应整理财政，统一币制，稳定物价，以利商业发展。
    唯有全国上下一心，共同努力，方能渡过此次经济危机。
    
    【商报记者 李文通】
    """
    
    # 测试各种功能
    print("【关键词】")
    keywords = processor.extract_keywords(test_text)
    for word, weight in keywords:
        print(f"{word}: {weight:.4f}")
    
    print("\n【日期】")
    date = processor.extract_date(test_text)
    print(date)
    
    print("\n【分类】")
    category = processor.categorize_content(test_text)
    print(category)
    
    print("\n【文章结构】")
    structure = processor.extract_article_structure(test_text)
    for key, value in structure.items():
        print(f"{key}: {value[:50]}...")
    
    print("\n【情感分析】")
    sentiment = processor.analyze_sentiment(test_text)
    print(sentiment)
    
    print("\n【命名实体】")
    entities = processor.extract_named_entities(test_text)
    for entity_type, entity_list in entities.items():
        print(f"{entity_type}: {', '.join(entity_list)}") 