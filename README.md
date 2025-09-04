```
pip install --upgrade ibm-watsonx-orchestrate
```

```
pip install ibm-watsonx-orchestrate
```

```
orchestrate env add -n kit700 -u  ⁦https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/5e597dd0-5a5e-4b69-8327-a8943c728c6b⁩
```

```
orchestrate env activate kit700
```

enter the api key from the group chat

sample content uodated 04/09/2025
```
grad-agent/
├─ agent.yaml                          # Top-level entrypoint (includes all sub-files)
├─ .env                                # Environment variables (API/RAG endpoints etc.)
├─ .gitignore                          # Ignore node_modules, env, build artifacts
├─ README.md                           # How to start, deploy, and test

├─ connections/
│  ├─ http_connections.yaml            # apic_base: shared connection for /login,/me,/enrolments,/timetable
│  └─ discovery_connections.yaml       # discovery_base, outline_base: connections for RAG/Outline

├─ tools/
│  ├─ http_login.yaml                  # tool: api_login (POST /login, override default headers)
│  ├─ http_me.yaml                     # tool: api_me (GET /me)
│  ├─ http_enrolments.yaml             # tool: api_enrolments (GET /me/enrolments?semester=)
│  ├─ http_timetable.yaml              # tool: api_timetable (GET /me/timetable)
│  ├─ rag_discovery.yaml               # tool: rag_discovery (General QA / AskUs)
│  └─ outline_lookup.yaml              # tool: outline_lookup (course outline queries)

├─ classifiers/
│  ├─ intent_classifier.llm.yaml       # LLM-based intent classifier (scores, top_intent, explanation)
│  └─ slot_extractor.llm.yaml          # LLM-based slot extractor (unitCode, semester)

├─ workflows/
│  └─ main.yaml                        # Router + nodes: public_qa, outline, login_flow,
│                                      # personal_guard, me/enrol/timetable, intent_clarify

├─ prompts/                            # (Optional) store system/few-shot prompts
│  ├─ system_intent.md                 # system prompt text for intent classifier
│  └─ fewshot_intent.jsonl             # few-shot examples for intent classification

├─ scripts/                            # (Optional) helper scripts
│  ├─ validate-config.sh               # lint / validate yaml configs
│  └─ run-local.sh                     # start agent locally (adapt to your toolchain)

├─ test/                               # (Optional) evaluation data
│  ├─ intents_eval.csv                 # labeled samples: query,intent
│  ├─ slots_eval.csv                   # labeled samples: query,unitCode,semester
│  └─ README.md                        # explain how to run evaluation, tune thresholds

└─ docs/                               # (Optional) developer docs, diagrams
   ├─ architecture.png                 # diagram: ADK ↔ API Connect ↔ RAG/Outline
   └─ api_contracts.md                 # description of tool input/output contracts

```
