更新和维护 project-why.md 知识库。

## 执行步骤

### 1. 检测相似知识

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.why_first_engine import WhyFirstEngine

why_engine = WhyFirstEngine()

# 用户提供的新知识
new_knowledge = """
用户输入的新知识内容
"""

# 检测相似条目
similar_items = why_engine.detect_similar_knowledge(new_knowledge, threshold=0.7)

if similar_items:
    print(f"🔍 发现 {len(similar_items)} 个相似条目:\n")
    for item in similar_items:
        print(f"  - {item['title']} (相似度: {item['similarity']:.2%})")
        print(f"    {item['content'][:100]}...")
        print()
```

### 2. 建议操作

根据相似度提供建议：

```python
if similar_items:
    top_similar = similar_items[0]

    if top_similar['similarity'] > 0.8:
        print("💡 建议: 增强现有条目")
        print(f"   条目: {top_similar['title']}")
        print(f"   操作: 添加补充信息而不是创建新条目")

    elif top_similar['similarity'] > 0.6:
        print("💡 建议: 考虑合并")
        merge_suggestion = why_engine.suggest_merge(
            {'title': '新知识', 'content': new_knowledge},
            top_similar
        )
        print(f"   合并标题: {merge_suggestion['merged_title']}")
        print(f"   理由: {merge_suggestion['reason']}")

    else:
        print("💡 建议: 创建新条目")
        print("   相似度较低，建议创建独立条目")
else:
    print("✅ 未发现相似条目，可以直接添加")
```

### 3. 执行操作

根据用户选择执行操作：

**选项 A: 增强现有条目**

```python
success = why_engine.enhance_knowledge(
    title=top_similar['title'],
    additional_info=new_knowledge
)

if success:
    print(f"✅ 已增强条目: {top_similar['title']}")
else:
    print("❌ 增强失败")
```

**选项 B: 创建新条目**

```python
success = why_engine.add_knowledge(
    category="架构决策",  # 或其他分类
    title="新知识标题",
    content=new_knowledge
)

if success:
    print("✅ 已添加新条目")
else:
    print("❌ 添加失败")
```

### 4. 显示更新后的知识库

```python
recent = why_engine.get_recent_knowledge(limit=5)

print("\n📚 最近的知识条目:\n")
for item in recent:
    print(f"  - {item['title']} ({item['timestamp']})")
    print(f"    {item['content'][:80]}...")
    print()
```

## 知识相似度检测

使用 SequenceMatcher 计算文本相似度：
- 0.8+ : 高度相似，建议增强现有条目
- 0.6-0.8 : 中度相似，建议考虑合并
- 0.6- : 低相似度，建议创建新条目

## 使用场景

- 完成任务后总结经验教训
- 发现重要架构决策
- 记录失败原因和避免方法
- 更新项目核心理念

## 注意事项

- 避免重复添加相似内容
- 定期检查和合并相似条目
- 保持知识库的组织性
- 及时更新过时信息
