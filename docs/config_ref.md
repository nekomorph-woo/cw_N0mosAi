# nOmOsAi 配置参考

## 配置文件概览

| 文件 | 位置 | 用途 |
|------|------|------|
| settings.json | `.claude/settings.json` | Claude Code 设置 |
| languages.yml | `.claude/rules/languages.yml` | 多语言配置 |
| ignore.yml | `.claude/rules/ignore.yml` | 豁免规则配置 |
| layer3.yml | `.claude/rules/layer3.yml` | 第三层规则配置 |

## languages.yml

配置文件扩展名到编程语言的映射。

```yaml
version: "1.0"

extensions:
  ".py": python
  ".js": javascript
  ".ts": typescript

rulesets:
  python:
    linters:
      - name: ruff
        enabled: true
      - name: bandit
        enabled: true
```

## ignore.yml

配置三级豁免规则。

```yaml
version: "1.0"

exemptions:
  - rule_id: RF-L3-001
    reason: "遗留代码"
    files:
      - "src/legacy/*.py"

  - rule_id: RF-L3-002
    reason: "临时豁免"
    expires: "2026-04-01"
```

### 豁免级别

1. **行级豁免**: 在代码行末添加 `# noqa: RULE_ID`
2. **文件级豁免**: 在文件开头添加 `# nomos-ignore: RULE_ID`
3. **规则级豁免**: 在 ignore.yml 中配置

## 性能配置

### 缓存配置

缓存目录: `.claude/cache/`

清理过期缓存:
```python
from .claude.hooks.lib.performance import ResultCache
cache = ResultCache(Path(".claude/cache"))
cache.prune(max_age_days=7)
```

### 并行执行

默认工作线程数: 4

可通过环境变量调整:
```bash
export NOMOS_MAX_WORKERS=8
```

## 更多信息

参见 [API 文档](../doc-arch/agent-nomos-flow/05_API_Documentation.md) 了解详细接口。
