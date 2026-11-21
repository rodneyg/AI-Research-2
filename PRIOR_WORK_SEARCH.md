## Survivor: Slow Burn (time-spaced erosion)
Question: if the same slow escalation is spread over days instead of minutes (timestamps visible to the bot, as in Slack, Discord, email and memory agents), does the AI give in more often, and does a monitor catch it less often?

Exact searches and results:
- arXiv: "timestamps multi-turn jailbreak time gap" (0); "temporal spacing jailbreak messages days apart" (0); "message timestamps LLM safety conversation" (0); "slow jailbreak over days LLM agent memory timestamps" (0); "time-delayed multi-turn attack LLM" (1: Context-Fractured Decomposition Attacks, which splits work across sessions whose context resets; here the full history stays and only the visible time between turns changes).
- OpenAlex: same 5 queries. Top results were general multi-turn jailbreak papers (Crescendo, Foot-In-The-Door, JailbreaksOverTime which is about distribution shift over calendar time in attack datasets, memory poisoning). None varies the time gaps shown inside one conversation.
- GitHub repositories: "timestamp jailbreak" (0), "time gap jailbreak" (1, unrelated), "slow jailbreak days" (0), "temporal jailbreak timestamps" (0), "time-spaced escalation llm" (0), "multi-day jailbreak" (0).
- GitHub issues/PRs: same 6 queries. No issue measures or proposes time gaps as a safety variable (hits were unrelated: PyRIT kwargs bug, NeMo Guardrails ONNX false positive, daily arXiv digests).
- GitHub code: "\"time gap\" \"multi-turn\" jailbreak timestamps" (30 files, none an experiment on time gaps); "\"days apart\" jailbreak llm" (90 files; the closest, JinyanSu1/Agentic-AI-Scientist, uses "four days apart" about two papers, unrelated).
- Web: "multi-turn jailbreak spread over days timestamps in context time gap escalation detection LLM Slack agent": returned MultiTurnPSB, HoneyTrap, a Slack engineering post on context management and a TOCTOU agent paper. None tests time gaps.
Verdict: no prior work found. Closest neighbors: Crescendo / FITD (multi-turn escalation with no time variable) and Context-Fractured Decomposition (session splitting with context resets).
