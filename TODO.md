# Improvement Patterns (Future Work)

Collected from research on meta-agent harnesses (Superpowers, GSD, Hyperpowers, ClaudeKit).

## Context Management
- [ ] **Just-in-time loading** - Store paths not content, Read only when needed
- [ ] **Subagent output filtering** - Agents return summaries (1-2k tokens), not raw output
- [ ] **Phase-based compaction** - `/compact` between investigation and implementation

## Session Handoff
- [ ] **HANDOFF.md skill** - 4-dimension handoff (context, files, decisions, next steps)
- [ ] **WORKING.md** - Live state document updated during work

## Quality Enforcement
- [ ] **Red flag language detection** - "should work", "probably fixed" = hasn't verified
- [ ] **User signal recognition** - Map frustration phrases to corrective actions
- [ ] **Spirit-vs-letter closure** - "Finding a technicality IS skipping the step"

## Prompt Engineering
- [x] **Contrastive examples** - Good/bad pairs beat abstract rules *(in progress)*
- [ ] **Mode transitions** - "=== ENTERING PHASE 2 ===" prevents context drift
- [ ] **Keyword saturation** - Include error messages/symptoms in descriptions

## Hook-Based Enforcement
- [ ] **PostToolUse(Write|Edit)** - Auto-format
- [ ] **Stop hook** - Verify completion claims
- [ ] **Checkpoint-before-risk** - Auto-checkpoint before large changes

## Sources

- [Anthropic - Effective Context Engineering](https://anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Superpowers](https://github.com/obra/superpowers)
- [GSD](https://github.com/glittercowboy/get-shit-done)
- [Hyperpowers](https://github.com/withzombies/hyperpowers)
- [ClaudeKit (carlrannaberg)](https://github.com/carlrannaberg/claudekit)
- [ClaudeKit (duthaho)](https://github.com/duthaho/claudekit)
- [HumanLayer - CLAUDE.md Best Practices](https://humanlayer.dev/blog/writing-a-good-claude-md)
