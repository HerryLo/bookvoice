# OCR文字识别准确度提升方案

## 问题描述
- OCR文字识别不准确，部分文字漏识别
- 当前置信度阈值0.3过高，有意义的内容被过滤

## 解决方案

### 组合方案：降低阈值 + 智能过滤

**1. 降低置信度阈值**
- 从 0.3 降至 0.1
- 保留更多easyocr检测到的文字

**2. 智能文字过滤**
- 在低阈值基础上，进一步过滤纯乱码
- 保留可能存在误识别的内容（如@符号）

### 过滤规则

```python
def is_valid_text(text: str) -> bool:
    # 最短长度检查
    if len(text.strip()) < 2:
        return False

    # 统计中文字符
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    if len(chinese_chars) > 0:
        return True  # 有中文就保留

    # 无中文：检查是否有足够的字母数字
    alphanumeric = re.findall(r'[a-zA-Z0-9]', text)
    if len(alphanumeric) >= 2:
        return True

    return False  # 既无中文又无足够字母数字，才是乱码
```

### 保留示例
- `@_天〉内不修改` → 有中文，保留
- `36个月内在中华人民共和国境内...` → 有中文，保留

### 过滤示例
- `%aitam辽 &0` → 无中文，字母数字少，过滤
- `(驭账: %aitam辽 &0` → 无中文，字母数字少，过滤

## 修改文件

**modules/ocr.py**

修改 `extract_structured_text` 方法：
1. 将置信度阈值从 0.3 改为 0.1
2. 添加 `is_valid_text` 过滤函数

## 验证方式

1. 使用测试图片验证
2. 对比修改前后识别的文字数量
3. 检查是否有乱码被保留
