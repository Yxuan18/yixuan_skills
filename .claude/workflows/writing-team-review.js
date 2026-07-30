export const meta = {
  name: 'writing-team-review',
  description: 'Multi-agent writing team reviews the blog post in parallel, Jerry consolidates',
  phases: [
    { title: 'Parallel Review', detail: 'Bonnie/structure, Wayne/prose, Blair/market, Alan/domain' },
    { title: 'Jerry Consolidates', detail: 'Decision log: Go / Conditional Go / No-Go' },
  ],
}

const BLOG_PATH = 'C:\\SEC\\yixuan_skills\\docs\\my-skills-journey.md'

// Updated review criteria (新标准)
const CRITERIA = `
Article must satisfy ALL of the following for Go:
1. Audience: high school students+ — accessible vocabulary, no unexplained jargon
2. Emotional value: does the reader feel something? Is there empathy, tension, or payoff?
3. Suspense hook: does the opening create curiosity that pulls the reader forward?
4. No AI-flavor: no "不是...而是...", "更好的方式是", "把流程固化", "从而", "因此", "综上所述"
   Also avoid: "复制 ≠ 粘贴" (too formulaic), "第一个洞见", "第二个洞见" as headers (kill the voice)
5. Domestic analogies: any analogy must use Chinese/local context
6. Layered insights: the blog should surface 2+ layers of insight (surface trick → underlying principle → meta-level)
7. Ending question: is there a simple, personal question that makes today's reader pause and reflect?
8. Length: 2000+ Chinese characters
9. Universal启发: can a non-technical person find at least one takeaway?
10. Micro-action: is there one small, doable action the reader could start today?
`

const REVIEWS_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          type: { type: 'string' },
          location: { type: 'string' },
          issue: { type: 'string' },
          suggestion: { type: 'string' },
        },
        required: ['type', 'issue', 'suggestion'],
      },
    },
    evidence_grade: { type: 'string' },
    open_questions: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'string' } },
    handoff: { type: 'string' },
  },
  required: ['verdict', 'findings'],
}

phase('Parallel Review')

const [bonnie, wayne, blair, alan] = await parallel([
  () => agent(`${CRITERIA}

You are Bonnie, Book Architect / Developmental Editor. Read the blog post at ${BLOG_PATH} and review STRUCTURE and RHYTHM.

Article review axes:
- Emotional arc: problems listed before results? Does the reader go from curious → understanding → moved?
- Progression: does each section build on the previous one? Is the insight layering working?
- Transitions: any section jump without a bridge sentence?
- Content density: code blocks / tables spaced for scan-friendly reading?
- Does the title create real curiosity?

Output a JSON object:
{
  "verdict": "Go" | "Conditional Go" | "No-Go",
  "findings": [{ "type": "arc"|"progression"|"transition"|"density"|"title", "location": "section or line range", "issue": "what's wrong or missing", "suggestion": "specific fix" }],
  "evidence_grade": "A-D",
  "open_questions": [],
  "risks": [],
  "handoff": "next reviewer"
}`, { label: 'Bonnie/structure', schema: REVIEWS_SCHEMA }),

  () => agent(`${CRITERIA}

You are Wayne, Narrative Lead / Co-writer. Read the blog post at ${BLOG_PATH} and review PROSE QUALITY.

Prose review axes:
- Voice: does this sound like a real person talking, or like an AI assistant writing a blog post?
- No AI-flavor: flag any phrases that feel templated: "不是...而是...", "更好的方式是", "把流程固化", "从而", "因此", "综上所述", "复制 ≠ 粘贴", "第一个洞见", "第二个洞见"
- Sentence rhythm: alternation between long and short sentences?
- Transitions: any paragraph jumps without a bridge sentence?
- Ending: does the last paragraph land emotionally or feel like a template?

Output a JSON object:
{
  "verdict": "Go" | "Conditional Go" | "No-Go",
  "findings": [{ "type": "voice"|"ai-flavor"|"rhythm"|"transition"|"ending", "location": "paragraph or line", "issue": "what's wrong", "suggestion": "how to fix" }],
  "evidence_grade": "A-D",
  "open_questions": [],
  "risks": [],
  "handoff": "next reviewer"
}`, { label: 'Wayne/prose', schema: REVIEWS_SCHEMA }),

  () => agent(`${CRITERIA}

You are Blair, Market Strategist. Read the blog post at ${BLOG_PATH} and review AUDIENCE POSITIONING and REACH.

Article review axes:
- Title: does it create real curiosity? Or is it generic?
- Opening hook: does it pull the reader in within first 3 sentences?
- Audience match: complexity appropriate for high school student+? Any jargon without explanation?
- Domestic analogy: any analogy uses Chinese/local context? No foreign examples unless necessary?
- Universal启发: can a non-technical reader find at least one takeaway?
- Micro-action: is there one small, doable action the reader could start today?
- SEO keywords: "Skill", "AI", "自动化", "重复" coverage
- Closing CTA: specific next step or vague "有问题欢迎留言" filler?

Output a JSON object:
{
  "verdict": "Go" | "Conditional Go" | "No-Go",
  "findings": [{ "type": "title"|"opening"|"audience"|"analogy"|"启发"|"action"|"seo"|"cta", "location": "section", "issue": "what's wrong", "suggestion": "how to fix" }],
  "evidence_grade": "A-D",
  "open_questions": [],
  "risks": [],
  "handoff": "next reviewer"
}`, { label: 'Blair/market', schema: REVIEWS_SCHEMA }),

  () => agent(`${CRITERIA}

You are Alan, Expert Reviewer. Read the blog post at ${BLOG_PATH} and review DOMAIN ACCURACY and INSIGHT LAYERING.

Domain frame: technical productivity / human-AI collaboration

Review axes:
- Insight layering: are there at least 2 layers of insight? (surface trick → underlying principle → meta-level)
- Accuracy: any claims about AI/Skills/workflow that are misleading or overclaimed?
- Domestic analogy: does the Meituan/ByteDance/Taobao analogy feel authentic and grounded?
- Ending question: does the final question create genuine pause, or is it a template?
- Emotional authenticity: does the "20 minutes a day for half a year" detail feel real or constructed?
- Claim depth: any claim that surfaces the next-level insight the user mentioned (模式提取, 隐性知识, AI as tool for human insight)?

Output a JSON object:
{
  "verdict": "Go" | "Conditional Go" | "No-Go",
  "findings": [{ "type": "insight"|"accuracy"|"analogy"|"ending"|"emotion"|"depth", "location": "section or line", "issue": "what's wrong or missing", "suggestion": "how to fix" }],
  "evidence_grade": "A-D",
  "open_questions": [],
  "risks": [],
  "handoff": "next reviewer"
}`, { label: 'Alan/domain', schema: REVIEWS_SCHEMA }),
])

log(`Bonnie: ${bonnie?.verdict ?? 'no result'} | Wayne: ${wayne?.verdict ?? 'no result'} | Blair: ${blair?.verdict ?? 'no result'} | Alan: ${alan?.verdict ?? 'no result'}`)

phase('Jerry Consolidates')

const reviews = [bonnie, wayne, blair, alan].filter(Boolean)
const goCount = reviews.filter(r => r.verdict === 'Go').length
const conditionalCount = reviews.filter(r => r.verdict === 'Conditional Go').length
const nogos = reviews.filter(r => r.verdict === 'No-Go')

const allFindings = reviews.flatMap(r => (r.findings || []).map(f => ({ reviewer: reviews.indexOf(r), ...f })))

const decision = nogos.length > 0 ? 'No-Go' : (conditionalCount > goCount ? 'Conditional Go' : 'Go')

const decisionLog = {
  decision,
  summary: {
    go: goCount,
    conditional: conditionalCount,
    no_go: nogos.length,
    total: reviews.length,
  },
  findings: allFindings,
  notes: `Decision: ${decision}. ${goCount} Go / ${conditionalCount} Conditional / ${nogos.length} No-Go out of ${reviews.length} reviewers.`,
}

log(`FINAL DECISION: ${decision}`)
return decisionLog