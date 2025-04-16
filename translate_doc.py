import os
import glob
import re
import asyncio
import aiofiles
import uuid
from openai import AsyncOpenAI

API_KEY = os.getenv("DEEPSEEK_API_KEY")
client = AsyncOpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

translate_prompt = """请将以下技术文档内容翻译成地道、流畅自然的中文。

翻译规则：
1. 保持原文的段落和格式结构不变
2. 不要翻译代码块、命令、变量名、函数名、类名等技术术语
3. 不要翻译人名、产品名、专有名词
4. 保留所有原始的特殊标记（如%%PLACEHOLDER_XXX%%）
5. 适当调整语序使中文表达更加自然流畅
6. 保留原文的标点符号样式（如括号、引号等）
7. 对于技术术语，如果有广泛接受的中文翻译则使用中文，否则保留英文
8. "Large Language Model" 一律翻译为“大模型”，"Prompt" 一律翻译为“提示词”
9. "title: "标记和"description: " 标记禁止进行翻译，但要对其对应的内容进行翻译

以下是需要翻译的内容：
"""

# 使用不太可能在文档中出现的格式作为占位符
PLACEHOLDER_PREFIX = "%%PH_"
PLACEHOLDER_SUFFIX = "%%"

def is_chinese(text):
    """检测文本是否为中文（通过判断中文字符比例）"""
    sample = text[:500]  # 增加样本大小以提高准确性
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', sample)
    return len(chinese_chars) > 5  # 如果有超过5个中文字符，认为是中文文档

async def translate_text(text):
    """调用翻译API翻译文本"""
    prompt = translate_prompt + f"\n{text}"
    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = await client.chat.completions.create(
            max_tokens=8192,
            model="deepseek-chat",
            messages=messages,
            stream=True
        )

        translated = ""
        async for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                translated += delta.content
        return translated
    except Exception as e:
        print(f"翻译API调用失败: {str(e)}")
        raise

def generate_placeholder():
    """生成唯一的占位符"""
    return f"{PLACEHOLDER_PREFIX}{uuid.uuid4().hex[:8]}{PLACEHOLDER_SUFFIX}"

async def process_markdown_for_translation(content):
    """处理Markdown/MDX文本，保留特殊部分不翻译"""
    lines = content.splitlines()
    translatable_content = []
    placeholder_map = {}
    
    # 多行元素的状态标记
    in_code_block = False
    in_html_block = False
    in_jsx_block = False
    in_frontmatter = False
    in_table = False
    
    code_buffer = []
    current_block = []
    
    # 正则表达式预编译
    code_fence_re = re.compile(r'^```')
    frontmatter_re = re.compile(r'^---$')
    jsx_open_re = re.compile(r'<[A-Z][A-Za-z0-9]*|<[a-z]+\.[A-Z]')
    jsx_close_re = re.compile(r'</[A-Z][A-Za-z0-9]*>|</[a-z]+\.[A-Z]')
    html_tag_re = re.compile(r'<([a-z][a-z0-9]*)\b[^>]*>|</([a-z][a-z0-9]*)>')
    url_re = re.compile(r'(https?://[^\s)\]]+)')
    image_re = re.compile(r'!\[.*?\]\(.*?\)')
    link_re = re.compile(r'\[.*?\]\(.*?\)')
    inline_code_re = re.compile(r'`[^`]+`')
    table_re = re.compile(r'^\|.*\|$')
    divider_re = re.compile(r'^-{3,}$|^\*{3,}$|^_{3,}$')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 1. 处理代码块
        if code_fence_re.match(line):
            if not in_code_block:
                in_code_block = True
                code_buffer = [line]
            else:
                code_buffer.append(line)
                # 结束代码块，生成占位符
                placeholder = generate_placeholder()
                code_content = "\n".join(code_buffer)
                placeholder_map[placeholder] = code_content
                translatable_content.append(placeholder)
                in_code_block = False
                code_buffer = []
            i += 1
            continue
            
        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue
            
        # # 2. 处理Front Matter (---之间的YAML)
        # if frontmatter_re.match(line):
        #     if not in_frontmatter:
        #         in_frontmatter = True
        #         current_block = [line]
        #     else:
        #         current_block.append(line)
        #         placeholder = generate_placeholder()
        #         block_content = "\n".join(current_block)
        #         placeholder_map[placeholder] = block_content
        #         translatable_content.append(placeholder)
        #         in_frontmatter = False
        #         current_block = []
        #     i += 1
        #     continue
            
        if in_frontmatter:
            current_block.append(line)
            i += 1
            continue
            
        # 3. 处理表格
        if table_re.match(line):
            if not in_table:
                in_table = True
                current_block = [line]
            else:
                current_block.append(line)
            i += 1
            continue
        elif in_table and (not line.strip() or not line.strip().startswith('|')):
            # 表格结束
            placeholder = generate_placeholder()
            block_content = "\n".join(current_block)
            placeholder_map[placeholder] = block_content
            translatable_content.append(placeholder)
            in_table = False
            current_block = []
            # 不增加 i，让空行或非表格行在下一次迭代中处理
        elif in_table:
            current_block.append(line)
            i += 1
            continue
            
        # 4. 处理JSX组件（MDX特有）
        if jsx_open_re.search(line) and not jsx_close_re.search(line):
            in_jsx_block = True
            current_block = [line]
            i += 1
            continue
        elif in_jsx_block and jsx_close_re.search(line):
            current_block.append(line)
            placeholder = generate_placeholder()
            block_content = "\n".join(current_block)
            placeholder_map[placeholder] = block_content
            translatable_content.append(placeholder)
            in_jsx_block = False
            current_block = []
            i += 1
            continue
        elif in_jsx_block:
            current_block.append(line)
            i += 1
            continue
            
        # 5. 处理HTML标签
        if html_tag_re.search(line) and ('</' not in line or line.find('<') < line.find('</')):
            html_opening = html_tag_re.search(line).group(1)
            if html_opening in ['div', 'table', 'ul', 'ol', 'details', 'summary']:
                in_html_block = True
                current_block = [line]
                i += 1
                continue
        
        if in_html_block and html_tag_re.search(line) and f'</{html_tag_re.search(line).group(2)}>' in line:
            current_block.append(line)
            placeholder = generate_placeholder()
            block_content = "\n".join(current_block)
            placeholder_map[placeholder] = block_content
            translatable_content.append(placeholder)
            in_html_block = False
            current_block = []
            i += 1
            continue
        elif in_html_block:
            current_block.append(line)
            i += 1
            continue
        
        # 6. 处理行内元素
        processed_line = line
        
        # 保护图片
        img_matches = list(image_re.finditer(processed_line))
        for match in reversed(img_matches):
            start, end = match.span()
            img = match.group(0)
            placeholder = generate_placeholder()
            placeholder_map[placeholder] = img
            processed_line = processed_line[:start] + placeholder + processed_line[end:]
        
        # 保护行内代码
        code_matches = list(inline_code_re.finditer(processed_line))
        for match in reversed(code_matches):
            start, end = match.span()
            code = match.group(0)
            placeholder = generate_placeholder()
            placeholder_map[placeholder] = code
            processed_line = processed_line[:start] + placeholder + processed_line[end:]
        
        # 保护分隔线
        if divider_re.match(line):
            placeholder = generate_placeholder()
            placeholder_map[placeholder] = line
            translatable_content.append(placeholder)
        else:
            # 添加处理后的行
            translatable_content.append(processed_line)
        
        i += 1
    
    # 处理末尾的未闭合块
    if in_code_block and code_buffer:
        placeholder = generate_placeholder()
        code_content = "\n".join(code_buffer)
        placeholder_map[placeholder] = code_content
        translatable_content.append(placeholder)
    
    if in_table and current_block:
        placeholder = generate_placeholder()
        block_content = "\n".join(current_block)
        placeholder_map[placeholder] = block_content
        translatable_content.append(placeholder)
    
    # 组合成待翻译文本
    translatable_text = "\n".join(translatable_content)
    
    return translatable_text, placeholder_map

async def restore_translation(translated_text, placeholder_map):
    """恢复翻译后的文本，将占位符替换回原始内容"""
    # 先按行处理，确保换行符保留
    translated_lines = translated_text.splitlines()
    restored_lines = []
    
    for line in translated_lines:
        restored_line = line
        # 按占位符长度降序排序，避免占位符前缀冲突
        placeholders = sorted(placeholder_map.keys(), key=len, reverse=True)
        for placeholder in placeholders:
            if placeholder in restored_line:
                restored_line = restored_line.replace(placeholder, placeholder_map[placeholder])
        restored_lines.append(restored_line)
    
    return "\n".join(restored_lines)

async def process_file(file_path, semaphore):
    """处理单个文件的翻译流程"""
    async with semaphore:
        try:
            # 读取文件内容
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            # 检查是否为中文内容
            if is_chinese(content):
                print(f"🔍 跳过中文文件: {file_path}")
                return

            # 预处理文档，提取需要翻译的部分
            translatable_text, placeholder_map = await process_markdown_for_translation(content)
            
            # 翻译文本
            print(f"🔄 正在翻译: {file_path}")
            translated_text = await translate_text(translatable_text)
            
            # 恢复占位符
            final_translated = await restore_translation(translated_text, placeholder_map)
            
            # 保存翻译结果
            # 创建备份
            backup_path = file_path + ".bak"
            async with aiofiles.open(backup_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
            # 保存翻译后的内容
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(final_translated)
                
            print(f"✅ 翻译完成: {file_path}")
            
        except Exception as e:
            print(f"❌ 处理失败: {file_path}，错误: {str(e)}")
            import traceback
            traceback.print_exc()

def find_md_files():
    """查找当前目录及子目录中的所有 .mdx 和 .md 文件，排除 ./docs/ref 目录"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excluded_dir = os.path.join(current_dir, 'docs', 'ref')
    matched_files = []

    for root, _, files in os.walk(current_dir):
        # 排除 ./docs/ref 目录
        if os.path.commonpath([root, excluded_dir]) == excluded_dir:
            continue
        for file in files:
            if file.endswith(('.md', '.mdx')):
                matched_files.append(os.path.join(root, file))

    return matched_files

async def main():
    md_files = find_md_files()
    print(f"找到 {len(md_files)} 个 Markdown/MDX 文件")
    
    # 限制并发请求数量
    semaphore = asyncio.Semaphore(8)  # 减少并发数以提高稳定性
    tasks = [process_file(fp, semaphore) for fp in md_files]
    await asyncio.gather(*tasks)
    
    print("✅ 所有文件处理完成!")

if __name__ == "__main__":
    asyncio.run(main())