# Agent Prompt Templates

Full prompt templates for each research agent. All agents use `subagent_type: general-purpose`. Every agent must capture metadata for each source: URL, date, and source type.

## General Agent

**Spawn when:** Always

```
Search for information and guides on this topic.

Use WebSearch to search: {query_terms}
Also search: how to {goal_or_intent}

Focus on:
- Informative articles and guides
- Expert opinions and recommendations
- Practical advice and actionable steps

For each source, note:
- Source URL
- Publication date (look for date in article or URL)
- Source type: blog / guide / publication / news
- Author credibility if apparent (expert, journalist, content marketer, unknown)

Return a summary of findings with source metadata.
```

## Reddit Agent

**Spawn when:** Opinion/experience, comparison, consumer, or strategy queries

```
Search Reddit for real-world experiences and opinions on this topic.

Use WebSearch to search: site:reddit.com {keywords}

Focus on:
- Real-world experience reports ("I did X and here's what happened...")
- Warnings and gotchas that don't appear in official sources
- Candid opinions on trade-offs
- "Don't do this" advice from experience
- Specific product/service recommendations with reasoning

For the top 2-3 relevant threads:
1. Use WebFetch to read the thread
2. Focus on highly-upvoted comments, not just the original post

For each source, note:
- Thread URL
- Date
- Upvote count and comment count (>50 upvotes or >20 comments = high engagement)
- Source type: Reddit thread (>50 upvotes) = Medium authority, Reddit thread (<10 upvotes) = Very Low authority

Return a summary of real-world opinions and warnings with metadata.
```

## Authority Agent

**Spawn when:** Factual, regulatory, financial, or health queries

```
Search for authoritative and official sources on this topic.

Use WebSearch to search: {topic} site:gov.de OR site:europa.eu OR site:gov.uk (adjust domains to match the relevant region)
Also search: {topic} official guidelines
Also search: {topic} {established_institution} (e.g., Stiftung Warentest, Consumer Reports, BaFin, etc.)

Focus on:
- Government websites and official publications
- Established consumer testing organizations
- Central bank or financial authority guidance
- Professional association guidelines
- Academic or research institution findings

For each source, note:
- Source URL
- Publication date
- Source type: government / institution / professional body / academic
- Which institution published it

Return findings with source metadata. Prioritize official and institutional sources over commercial ones.
```

## Forum/Community Agent

**Spawn when:** Experience-based or niche queries

```
Search community forums and Q&A sites for experiences and advice on this topic.

Use WebSearch to search: {topic} forum experience
Also search: site:quora.com {keywords}
Also search: {topic} community advice {relevant_niche_terms}

Focus on:
- Detailed personal experiences
- Expert responses in specialized communities
- Practical tips not found in mainstream articles
- Niche community knowledge

For the top 2-3 relevant threads:
1. Use WebFetch to read the thread
2. Focus on well-reasoned, detailed responses

For each source, note:
- URL
- Date
- Platform and engagement level
- Source type: Quora / specialized forum / community
- Whether the response appears to come from an experienced person

Return a summary of community knowledge with metadata.
```

## Comparison Agent

**Spawn when:** Query contains "vs", "or", "compare", "which", "best"

```
Search for comparisons between the options or categories mentioned.

Use WebSearch to search: {option_A} vs {option_B} {context}
Also search: best {category} {criteria} {current_year}
Also search: {category} comparison {context}

Find:
- Direct comparison articles
- Pros and cons of each option
- Price/quality breakdowns if relevant
- Use case recommendations (when to choose which)
- Test results from independent testing organizations

IMPORTANT: Be wary of affiliate content. Note if a comparison source uses affiliate links or is from a "best X" listicle site.

For each source, note:
- Source URL
- Publication date (crucial for comparisons)
- Source type: comparison article / test report / discussion
- Whether it appears to be independent or affiliate-driven

Return a balanced summary of each option's strengths and weaknesses with source metadata.
```

## Regional Agent

**Spawn when:** Query mentions a country, city, or region-specific topic

```
Search for region-specific information on this topic.

Use WebSearch to search: {topic} {country/region}
Also search in the local language if applicable: {topic_in_local_language} {region}
Also search: {topic} {region} {current_year}

Focus on:
- Local regulations and legal requirements
- Region-specific options and availability
- Local pricing and market conditions
- Cultural norms and expectations
- Local institutions and resources

For each source, note:
- Source URL
- Date
- Language
- Source type: local government / local publication / regional guide / local community
- Whether it specifically covers the queried region

Return region-specific findings with metadata. Flag if a source covers a different region than requested.
```

## News Agent

**Spawn when:** Topic likely affected by recent events, policy changes, or market shifts

```
Search for recent news and developments on this topic.

Use WebSearch to search: {topic} {current_year}
Also search: {topic} latest news
Also search: {topic} recent changes {current_year}

Focus on:
- Policy or regulatory changes
- Market shifts or price changes
- New options or services that recently became available
- Recent events that affect the topic

For each source, note:
- Source URL
- Publication date (must be recent — within last 12 months)
- Source type: news article / press release / announcement
- Which publication

Return only genuinely recent and relevant developments with metadata. Do not pad with older news.
```
