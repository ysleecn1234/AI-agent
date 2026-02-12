# Chat 파이프라인 전체: LLM 올인 vs SLM+LLM 하이브리드

---

## 1-1. 비교 대상 두 전략

### 전략 A: LLM 단독

chat_routing / chat_research / chat_simple / chat_complex / chat_bulk / chat_synthesis / chat_guardrail

→ 전부 GPT-4o, Claude Sonnet, Gemini Pro 같은 상위 LLM으로 처리.

### 전략 B: SLM 여러 개 + 필요시 LLM

라우팅, 리서치, simple/bulk, synthesis, 1차 guardrail 등은 SLM/중형 모델로 처리.

→ complex, 고위험, 실패/불확실 케이스만 상위 LLM으로 escalate.

---

## 1-2. 비용·성능 관점 공식 근거

---

### (1) FrugalGPT: Cascade가 LLM 단독보다 싸고, 성능도 유지/향상

**논문:** "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance"

**링크(원문):** https://arxiv.org/pdf/2305.05176.pdf

**핵심 문장:**

> "Our experiments show that FrugalGPT can match the performance of the best individual LLM (e.g., GPT-4) with up to 98% cost reduction or improve the accuracy over GPT-4 by 4% with the same cost."
> 

**요약:**

- 작은/중간/큰 모델을 계단식(cascade)으로 조합하면,
- GPT-4 단독과 동일한 성능에 비용 1/50 수준까지 가능하고,
- 같은 비용이면 정확도가 GPT-4 단독보다 4% 더 높게 나오기도 했다.

**이 논문이 보여주는 건:**

- "LLM 단독" 전략보다,
- "SLM 여러 개 + 필요 시 LLM" 전략이 비용·성능 측면에서 우월할 수 있다는 실증 결과.

**정리:**

- Chat 파이프라인 전체를 GPT-4o/Claude Sonnet/Gemini Pro 같은 LLM 하나로 처리하는 것은,
- 비용 면에서 불필요하게 비싸고,
- 성능 면에서도 "항상 최선"이라는 보장이 없다는 것이 FrugalGPT 결과로 드러난다.
- **따라서 전략 B(하이브리드)를 기본 가정으로 삼는 것이 합리적이다.**

---

### (2) HYBRIDSERVE / C3PO / 기타 cascade 연구들: 작은 모델 + 큰 모델 조합이 일반적인 방향

**HYBRIDSERVE** (DNN/LLM 서빙, confidence-based cascade)

**링크:** https://ieeexplore.ieee.org/document/11262683/

**핵심 내용 요지:** 작은 모델과 큰 모델을 confidence 기반으로 조합해, 에너지/비용을 10~20배 줄이면서 동일 정확도 유지.

**C3PO** (Cost Controlled Cascaded Prediction Optimization)

**링크:** https://arxiv.org/abs/2511.07396

**핵심 내용 요지:** self-supervised cascade 최적화를 통해, reasoning 벤치마크에서 기존 cascade보다 더 좋은 cost–accuracy trade-off 달성.

→ 학계/산업계 양쪽 모두에서 **"작은 모델로 대부분 처리, 어려운 것만 LLM"** 방식이 표준 설계 패턴으로 자리잡고 있다는 근거.

---

### (3) SLM 서베이: SLM이 커버 가능한 영역이 넓고, 비용/지연 이득이 크다

**논문:** "Small Language Models: Survey, Measurements, and Insights"

**링크:** https://arxiv.org/html/2409.15790v1

**핵심 내용:**

- SLM(100M~5B 파라미터) 50여 개를 벤치마크한 결과,
- classification, summarization, simple QA, NLU 같은 태스크에서는 LLM 대비 성능 차이가 작고,
- 대신 추론 지연(latency)과 메모리 사용량이 현저히 작다고 분석.

**이건 Chat 파이프라인에서**

- chat_routing, chat_research, chat_simple, chat_bulk, chat_synthesis, chat_guardrail(1차 분류) 같은 단계가
- SLM으로 충분히 커버 가능한 영역이라는 걸 뒷받침한다.

---

### (4) Flash vs Pro: 경량 모델이 고볼륨/저지연 태스크용으로 설계됨

**Gemini 1.5 Flash vs Pro 비교**

**Google 블로그:** https://developers.googleblog.com/en/gemini-15-pro-and-15-flash-now-available/

**PromptLayer 분석:** https://blog.promptlayer.com/an-analysis-of-google-models-gemini-1-5-flash-vs-1-5-pro/

**핵심 문장:**

> "Gemini 1.5 Flash was purpose-built as our fastest, most cost-efficient model yet for high volume tasks…"
> 
- Flash의 blended price는 약 **$0.53 / 1M tokens**, Pro는 input $7 / 1M, output $21 / 1M 수준으로 약 **10~40배 비싸다.**
- **"Flash generates 163.6 tokens per second, faster than 1.5 Pro."**

**이건** chat_simple, chat_bulk, chat_routing, chat_synthesis 같은 고볼륨·저지연 단계는 **Flash 급 SLM이 주력이어야 한다**는 것을 함의한다.

---

### (5) GPT-4o mini: small 모델로도 높은 일반 성능 + 극단적 저비용

**OpenAI GPT-4o mini 블로그:** https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/

**핵심 문장:**

> "GPT-4o mini is our most cost-efficient small model."
> 
- 가격: input **$0.15 / 1M**, output **$0.60 / 1M** → GPT-4o 대비 **30~50배 저렴.**
- **"GPT-4o mini scores 82% on MMLU"** (GPT-3.5보다 높고, 이전 mini 계열보다 우수).

**LCFO 논문:** http://arxiv.org/pdf/2412.08268.pdf

**핵심 문장:**

> "GPT-4o-mini achieves best human scores among automatic systems in both summarization and summary expansion tasks, even surpassing human output on certain metrics."
> 

**이건** chat_simple, chat_synthesis, title, 간단 RAG 답변 등에서 **4o mini가 LLM을 충분히 대체 가능**하다는 강력한 근거.

---

### (6) Guardrail: SLM이 오히려 LLM보다 낫다는 근거

**SLM-Mod 논문:** https://arxiv.org/abs/2410.13155

**핵심 문장:**

> "SLMs (<15B) outperform zero-shot LLMs at content moderation — 11.5% higher accuracy and 25.7% higher recall on average across all communities."
> 

**Chat Guardrail 1차 필터(안전/모더레이션)는 LLM 단독보다 SLM 특화 모델들이 더 낫다**는 것을 명시적으로 보여준다.

---

# 2. Chat 전체에서 "LLM 단독 vs SLM+LLM 조합" 결론

위 근거를 기반으로, 이미지에 나온 전체 Chat 파이프라인 (chat_routing / chat_research / chat_simple / chat_complex / chat_bulk / chat_synthesis / chat_guardrail)에 대해 정리하면:

---

## 2-1. LLM 단독 전략의 문제점

### 비용

- Flash vs Pro, 4o mini vs 4o 수치에서 보이듯, **LLM은 small-tier 대비 10~50배 이상 비싸다.**
- Chat 전체를 LLM 하나로 처리하면, 단순/간단/대량 단계에서도 이 비용을 그대로 지불해야 한다.

### 지연

- Flash, Haiku 같은 SLM은 지연 시간이 매우 짧고, RPM 한도도 높게 잡혀 있음.
- **LLM 단독은 고부하 상황에서 latency·동시처리 면에서 불리.**

### 정확도

- FrugalGPT/SLM-Mod/SLM 서베이 결과에서 보듯,
- **간단·분류·모더레이션·요약 영역에서는 SLM/경량 모델이 LLM과 동급 혹은 더 나은 성능을 내기도 한다.**
- 따라서 LLM 올인 전략은 **"항상 정확도도 더 좋다"는 보장도 없다.**

---

## 2-2. SLM 여러 개 + 필요시 LLM 조합 전략의 장점

### 비용

- **FrugalGPT: GPT-4 단독 대비 최대 98% 비용 절감.**
- Flash/4o mini/Haiku 등 small-tier를 라우팅, 간단 질의, bulk, synthesis에 쓰면, Chat 전체 비용의 대부분을 small-tier 가격으로 끌어내릴 수 있다.

### 정확도

- **FrugalGPT:** 같은 비용에서 GPT-4보다 4% 정확도 향상 가능.
- **Guardrail 모더레이션:** SLM이 LLM보다 정확도/재현율 모두 우위.
- **LCFO:** 요약/확장 쪽은 GPT-4o mini가 이미 최고 수준.

### 지연/처리량

- Flash/Haiku/SLM 계열은 **high-volume, low-latency 태스크를 위해 설계됨.**
- Flash-8B는 1000RPM 이상, 토큰/초 속도도 Pro보다 빠르다고 보고.

---

## 2-3. Chat 파이프라인별 적용 방향 요약

이걸 "Chat 파이프라인 전체에 대한 방향성"으로 요약하면:

---

### chat_routing / chat_research / chat_simple / chat_bulk / chat_synthesis / chat_guardrail(1차)

**SLM/경량 모델이 비용/지연/정확도에서 LLM 대비 우위 또는 충분하므로,**

→ 기본 전략은 **SLM 여러 개로 역할 분리 + 필요시 LLM escalation**이 합리적이다.

→ 즉, 여기서 **LLM 단독은 비효율.**

---

### chat_complex (복잡 RAG Reasoning / Doc Chat 등)

GeoBenchX·의료 RAG·복합 reasoning 벤치마크에서 **상위 LLM이 여전히 SLM보다 확실히 우위.**

→ 따라서 이 구간(고난도/고위험)은 **상위 LLM을 primary로 두고,**

→ 단순 케이스만 SLM 경로로 일부 분리하는 식의 **"partial 하이브리드"가 맞다.**

# 각 파트별 분석

---

## 1. chat_routing

### 1-1. 단순/복잡/고위험 케이스

**단순**

- 짧은 질문, 의도가 명확 ("비밀번호 초기화 방법", "날씨 알려줘").
- 필요 능력: 키워드 기반 의도 분류.

**복잡**

- 여러 의도가 섞이거나, "문서 요약 + 추가 검색 + 코드 실행" 같은 복합 워크플로로 이어질 수 있는 질문.
- 필요 능력: 문맥 이해 + 대략적인 난이도 판단.

**고위험**

- 거의 없음. 고위험(법률/의료/재무)는 보통 Routing 이후 단계에서 관리.

---

### 1-2. SLM/LLM 방향성

### SLM이 적합한 근거

**① SLM 서베이** 📊

- **링크:** https://arxiv.org/html/2409.15790v1
- **핵심 내용:** 100M~수십억 파라미터 SLM들이 classification, summarization, simple QA, NLU에서는 LLM에 비해 성능 차이가 작고, latency·자원 사용은 훨씬 낮다고 보고.
- Chat Routing은 텍스트 분류+간단 NLU에 해당하므로, SLM이 충분하다는 근거.

**② Gemini 1.5 Flash** 📊

- **링크:** https://developers.googleblog.com/en/gemini-15-pro-and-15-flash-now-available/
- **핵심 문장:** "Gemini 1.5 Flash was purpose-built as our fastest, most cost-efficient model yet for high volume tasks."
- Routing은 모든 요청이 지나가는 high-volume 단계이므로, Flash 같은 경량 SLM이 타깃으로 설계된 영역.

**③ GPT-4o mini** 📊

- **링크:** https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/
- **핵심 문장:** "GPT-4o mini is our most cost-efficient small model … priced at $0.15 per million input tokens and $0.60 per million output tokens … it scores 82% on MMLU."
- MMLU 82%는 의도 분류에 충분한 일반 지식·이해 능력.

### LLM이 불필요한 이유

- 위 서베이·모델 카드들에서 보듯, Routing 수준 태스크에서 LLM이 제공하는 성능 이득은 작고, 비용·지연은 크게 증가한다.
- FrugalGPT는 간단 태스크를 작은 모델이 처리하고, 어려운 태스크만 LLM에 보내는 전략으로 GPT-4 단독 대비 최대 98% 비용 절감을 보고한다. 📊
    - **링크:** https://arxiv.org/abs/2305.05176

---

### 1-3. 성능·비용 마지노선

**비용** 📊

- LLM(GPT-4o) 가격대(약 input $5/1M, output $15/1M)보다 최소 10배 이상 저렴한 small-tier를 사용.
- GPT-4o mini: input $0.15, output $0.60 / 1M.
- Flash: 최신 가격 인하로 비슷한 small-tier 구간.

**정확도**

- 내부 Intent 라우팅 Eval에서 기존 GPT-3.5 대비 Accuracy/F1 손실 ≤ 2~3%p.

---

### 1-4. Primary / 장애 Fallback 후보

**Primary 후보 (SLM)** 📊

- **Gemini 1.5 Flash**
    - high-volume, high-frequency, low-latency 태스크용으로 설계.
- **GPT-4o mini**
    - 비용 효율적 small 모델, MMLU 82%로 분류에 충분.

**장애 Fallback 후보 (SLM, 벤더 다변화)** 📊

- **Claude 3 Haiku / 3.5 Haiku**
    - Anthropic: "Claude 3 Haiku는 우리의 가장 빠르고 가장 저렴한 모델로, 거의 즉각적인 응답성을 위해 설계되었습니다."
    - **링크:** https://www.anthropic.com/news/claude-3-haiku

---

---

## 2. chat_research

### 2-1. 단순/복잡/고위험 케이스

**단순**

- FAQ, 헬프센터 수준 검색: 질의에서 핵심 키워드 몇 개만 뽑으면 되는 경우.

**복잡**

- "서비스=A, 기간=B, 에러코드=C"처럼 구조화된 JSON/쿼리가 필요한 경우.

**고위험**

- 의료/법률/금융 도메인에서, 잘못된 검색 쿼리가 잘못된 문서를 불러와 이후 위험한 추론으로 이어질 수 있는 케이스.

---

### 2-2. SLM/LLM 방향성

### SLM이 적합한 근거

**① GPT-4o mini의 요약/재구성 능력** 📊

- **LCFO 논문**
- **링크:** http://arxiv.org/pdf/2412.08268.pdf
- **핵심 문장:** "GPT-4o-mini achieves best human scores among automatic systems in both summarization and summary expansion tasks, even surpassing human output on certain metrics."
- 검색 쿼리 생성은 질문 요약 + 키워드 재구성 작업이므로, 이 정도 성능이면 충분.

**② SLM 서베이** 📊

- **링크:** https://arxiv.org/html/2409.15790v1
- classification·summarization·simple QA·NLU 작업에서 SLM과 LLM의 성능 차이는 작고, latency·cost 이득이 크다는 분석.
- Chat Research는 요약+구조화 작업이므로, SLM으로 커버 가능.

### LLM이 필요한 경우

- 매우 복잡한 도메인(Text2SQL, 복잡한 금융 질의)에서는 LLM이 개입할 수 있다.
- 예: FinStat2SQL은 large+small 모델을 결합해 금융 질의→SQL 파이프라인을 구성하며, small(7B) 모델이 GPT-4o-mini보다 좋은 결과를 내기도 한다.
    - **링크:** https://arxiv.org/abs/2506.23273
- 그러나 이런 케이스는 chat_complex/RAG Reasoning 쪽에서 처리하는 것이 설계상 더 자연스럽다.

---

### 2-3. 성능·비용 마지노선

**비용** 📊

- Routing과 동일하게 small-tier (≤약 $1/1M) 기준.
- GPT-4o mini 가격: input $0.15, output $0.60 / 1M.

**품질**

- JSON 스키마 검증에서 오류율 < 0.5~1%.
- 기존 GPT-3.5 기반 검색 파이프라인 대비 검색 hit-rate/recall 동등 이상.
- GPT-4o-mini를 RAG에 적용한 연구에서도 practical한 성능 보고.
    - **링크:** https://ieeexplore.ieee.org/document/11255653/

---

### 2-4. Primary / 장애 Fallback 후보

**Primary 후보 (SLM)** 📊

- **GPT-4o mini**
    - summarization/재구성이 강하고, 구조적 출력에 적합.

**장애 Fallback 후보 (SLM)**

- **Gemini 1.5 Flash**
    - 고속 요약·데이터 추출·JSON 전처리에 적합.
- **Claude 3 Haiku**
    - 빠른 응답성과 적당한 reasoning을 가진 경량 모델.

---

---

## 3. chat_simple

> chat_simple: RAG 거의 없이, 일반 Q&A/간단 설명/짧은 코드/요약 등 상대적으로 단순한 대화
> 

### 3-1. 단순/복잡/고위험 케이스

**단순**

- 일상 Q&A ("OAuth가 뭐야?", "이 문단 요약해줘"), 간단 코드 설명.

**복잡**

- 두세 단계 reasoning이 필요하지만, 긴 문맥·다수 문서 통합은 필요 없는 케이스.

**고위험**

- 법률/의료/재무 등 고위험은 chat_complex나 doc_chat로 보내는 것이 바람직.

---

### 3-2. SLM/LLM 방향성

### SLM 적합 근거

**① "Are Small Language Models Ready to Compete…?"** 📊

- **링크:** https://arxiv.org/html/2406.11402
- **핵심 내용:** 적절히 선택·튜닝된 SLM들이 일부 practical 애플리케이션에서 GPT-4o, Gemini 1.5 Pro 같은 상위 LLM과 경쟁 가능한 품질을 제공한다고 분석.
- 특히 일반 Q&A/간단 설명보다 복잡하지 않은 작업에서 SLM이 충분히 실용적.

**② GPT-4o mini의 전반 성능** 📊

- **리뷰/블로그:** https://dev.to/soorajsuresh/announcing-gpt-4o-mini-openais-most-cost-efficient-small-model-2j9m
- **핵심 요약:**
    - MMLU 82%, MGSM 87, HumanEval 87.2 등 small-tier 중 상위권.
    - "Offers performance close to GPT-4o in many everyday tasks at a fraction of the cost."
- simple chat에서 요구되는 일반 지식/간단 reasoning은 4o mini로 충분.

### LLM 필요 케이스

- long-form reasoning, 도메인 전문성을 요구하는 질문은 chat_complex로 라우팅해야 하고, 거기서 LLM을 사용.
- simple 경로에서까지 LLM을 쓰는 것은 비용·지연 측면에서 비효율.

---

### 3-3. 성능·비용 마지노선

**비용**

- small-tier (≤$1/1M), 가능하면 GPT-4o mini 가격 수준.

**품질** 📊

- 내부 human eval에서 GPT-3.5 이상 만족.
- 외부 벤치마크에서 4o mini는 small-tier 중 top-tier → 이 기준에 부합.

---

### 3-4. Primary / 장애 Fallback 후보

**Primary 후보**

- **GPT-4o mini**
    - simple chat에 필요한 범용성과 비용 효율성을 동시에 만족.

**장애 Fallback 후보**

- **Gemini 1.5 Flash**
    - low-latency, low-cost chat 용.
- **Claude 3 Haiku**
    - fastest, affordable simple chat 모델.

---

---

## 4. chat_complex

> chat_complex: 복잡 RAG Reasoning, multi-step 추론, 긴 문맥, 고위험 도메인 질문 등
> 

### 4-1. 단순/복잡/고위험 케이스

**단순**

- 짧은 문서 하나를 기반으로 한 조금 더 깊은 설명 정도 (사실상 chat_simple/RAG 경로로 보내도 됨).

**복잡**

- 여러 문서/규정/코드 조각을 통합해야 하는 multi-step reasoning.

**고위험**

- 의료, 법률, 재무, 보안 등 잘못된 답변이 큰 피해로 이어질 수 있는 도메인.

---

### 4-2. SLM/LLM 방향성

### LLM이 필요한 근거

**① SLM 서베이** 📊

- **링크:** https://arxiv.org/html/2409.15790v1
- **핵심 문장:**
    - SLM들은 classification·summarization에서는 경쟁력이 있으나,
    - multi-hop reasoning, long-context QA, complex reasoning에서는 여전히 LLM과 상당한 성능 격차가 있다고 명시.
- chat_complex가 바로 이 범주에 해당.

**② GeoBenchX (multistep geospatial tasks)** 📊

- **링크:** http://arxiv.org/pdf/2503.18129.pdf
- **핵심 내용:**
    - GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro 같은 상위 LLM들이 multistep geospatial reasoning에서 상위권 성능.
    - 작은 모델/중형 모델들은 복합 reasoning에서 큰 격차.

**③ 의료 RAG 연구** 📊

- **링크:** https://www.nature.com/articles/s41746-025-01802-z
- **핵심 내용:**
    - radiology contrast media consultation에서 local LLM(작은 모델)보다 상업 LLM을 활용한 RAG 시스템이 더 높은 품질의 답변을 제공.
    - 고위험 도메인에서는 상위 LLM이 필요하다는 실증.

→ **chat_complex는 LLM을 Primary로 사용하는 것이 합리적이고, SLM만으로 대체하려는 전략은 품질·위험 측면에서 부적절하다.**

---

### 4-3. 성능·비용 마지노선

**성능**

- 내부 복합 QA/RAG Eval에서 GPT-4o 기준 대비 정답률 ≥ 90%.
- 환각률, "모르겠다" 응답 비율이 GPT-4o/Claude Sonnet과 유사.

**비용**

- 전체 트래픽에서 비중이 상대적으로 낮은 고난도 경로이므로, 비용보다는 품질 우선.
- GPT-4o / Claude 3.5 Sonnet / Gemini 1.5 Pro 같은 LLM 가격대를 허용.

---

### 4-4. Primary / 장애 Fallback 후보

**Primary 후보 (LLM)** 📊

- **Claude 3.5 Sonnet**
    - **Anthropic 모델 카드 Addendum**
    - **링크:** https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf
    - **핵심 요약:** Claude 3.5 Sonnet는 이전 Sonnet/Opus 대비 복합 문제 해결률이 크게 향상(예: 64%→78%)했고, 다양한 reasoning 벤치마크에서 GPT-4 계열과 상위권 경쟁.
    - 복합 reasoning·code·장문 이해에서 매우 강력 → chat_complex용 주축 LLM에 적합.

**장애 Fallback 후보 (LLM)** 📊

- **GPT-4o**
    - **GPT-4o 시스템 카드**
    - **링크:** http://arxiv.org/pdf/2410.21276.pdf
    - **핵심 내용:** GPT-4 대비 latency·비용은 낮추면서, reasoning·코딩·멀티모달에서 SOTA급 성능 유지.
- **Gemini 1.5 Pro** 📊
    - **링크:** https://developers.googleblog.com/en/gemini-15-pro-and-15-flash-now-available/
    - **핵심:** 수백만 토큰 컨텍스트에서 강력한 long-context reasoning, 코드·멀티모달 작업에 특화.

---

## 5. chat_bulk

> chat_bulk: 같은 유형의 요청을 다량으로 처리하는 배치/대량 채팅 – 예: N개 질의에 대해 간단 요약/답변 생성
> 

### 5-1. 단순/복잡/고위험 케이스

**단순**

- 짧은 질문·간단 답변을 매우 많이 처리하는 케이스 (FAQ, 간단 설명).

**복잡**

- 단순 질문이지만, 내부적으로 짧은 RAG가 붙는 경우.

**고위험**

- 법률/의료/재무 도메인 배치 처리처럼, 잘못된 답변이 위험한 경우 (이건 chat_complex 경로나 별도 고위험 파이프라인으로 보내는 게 바람직).

---

### 5-2. SLM/LLM 방향성

### SLM이 적합한 근거

**① high-volume 태스크용 설계** 📊

- **Gemini 1.5 Flash**
- **링크:** https://developers.googleblog.com/en/gemini-15-pro-and-15-flash-now-available/
- **핵심 문장:** "Gemini 1.5 Flash was purpose-built as our fastest, most cost-efficient model yet for high volume tasks."
- chat_bulk는 전형적인 high-volume 작업 → Flash 같은 SLM이 촛점.

**② SLM의 practical 성능** 📊

- **"Are Small Language Models Ready to Compete with LLMs for Practical Applications?"**
- **링크:** https://arxiv.org/html/2406.11402
- **핵심 내용:** 적절히 선택된 SLM들이 일부 실제 애플리케이션(FAQ, 간단 Q&A, 요약 등)에서 GPT-4o, Gemini-1.5-Pro 급 LLM과 경쟁 가능한 품질을 보여준다고 평가.
- chat_bulk의 대부분은 이 수준의 작업.

### LLM이 필요한 경우

- 고위험 도메인·복잡 reasoning이 필요하면 chat_complex나 별도 파이프라인으로 라우팅하는 것이 좋고, bulk 경로 자체는 SLM 중심이 타당하다.

---

### 5-3. 성능·비용 마지노선

**비용** 📊

- bulk는 토큰 소비량이 크므로, 가능한 한 최저가 small-tier를 사용해야 한다.
- GPT-4o mini: input $0.15, output $0.60 / 1M 토큰
- Gemini Flash/Flash-8B: "faster, cheaper AI model for high-volume tasks"로 소개되며, 가격 인하로 small-tier 중 최저 수준.

**품질**

- 내부 human eval에서 GPT-3.5 수준 이상의 이해도·유창성.
- 도메인 리스크가 낮은 bulk 작업으로 한정하는 것을 전제로 함.

---

### 5-4. Primary / 장애 Fallback 후보

**Primary 후보 (SLM)** 📊

- **Gemini 1.5 Flash / Flash-8B**
    - high-volume 태스크용, low-latency, low-cost, 토큰/초 속도가 Pro보다 빠름.

**장애 Fallback 후보 (SLM)**

- **GPT-4o mini**
    - 전반적인 성능·비용 밸런스가 뛰어난 small 모델, simple Q&A·요약에 충분한 품질.
- **Claude 3 Haiku**
    - fastest & most affordable 모델, real-time UX용.

---

---

## 6. chat_synthesis

> chat_synthesis: RAG/Reasoning 결과를 받아 Markdown 포맷팅, 구조화, 톤 조정, 언어 변환 등을 수행하는 단계
> 

### 6-1. 단순/복잡/고위험 케이스

**단순**

- 섹션/리스트 구조화, 간단 톤 조정, 요약 길이 조정.

**복잡**

- 두 언어 버전 동시 생성, 특정 스타일(보고서/프레젠테이션/메일)에 맞춘 재구성.

**고위험**

- 콘텐츠 자체는 이미 앞 단계에서 검증됐고, synthesis는 표현·구조만 바꾸므로 상대적 위험은 낮음.

---

### 6-2. SLM/LLM 방향성

### SLM이 적합한 근거

**① GPT-4o mini의 요약/포맷 성능** 📊

- **LCFO 논문**
- **링크:** http://arxiv.org/pdf/2412.08268.pdf
- **핵심 문장:** "GPT-4o-mini achieves best human scores among automatic systems in both summarization and summary expansion tasks, even surpassing human output on certain metrics."
- 요약/확장에서 4o mini가 SOTA급이므로, "결과를 정제하는 단계"에는 충분.

**② SLM 서베이**

- **링크:** https://arxiv.org/html/2409.15790v1
- 요약/분류/간단 변환 태스크에서 SLM과 LLM 성능 차이가 작고, latency·비용 이득이 크다고 분석.
- chat_synthesis는 정확히 이 영역.

### LLM이 불필요한 이유

- 핵심 reasoning·정확도는 이전 단계(chat_complex/RAG)에서 이미 결정됐으며,
- synthesis 단계에서 LLM을 써도 내용 정확도는 크게 향상되지 않고, 비용만 증가한다.

---

### 6-3. 성능·비용 마지노선

**비용** 📊

- 전체 파이프라인에서 synthesis는 거의 모든 요청에서 실행되므로, 최저가 small-tier를 쓰는 것이 중요.
- GPT-4o mini 가격(입력 $0.15, 출력 $0.60 / 1M)를 기준으로 삼는 것이 합리적.

**품질**

- 내부 형식 검증에서 Markdown 구조/포맷 오류율 < 1%.
- human eval에서 "가독성·구조·톤" 만족도 GPT-3.5 이상.

---

### 6-4. Primary / 장애 Fallback 후보

**Primary 후보 (SLM)** 📊

- **GPT-4o mini**
    - summarization/formatting에서 최고의 성능을 보이고, 비용이 매우 낮다.

**장애 Fallback 후보 (SLM)**

- **Gemini 1.5 Flash**
    - 요약·데이터 추출·형식 변환에 최적화된 경량 모델.
- **Claude 3 Haiku**
    - 빠른 응답과 준수한 요약 능력을 가진 simple chat/polish 용 모델.

---

---

## 7. chat_guardrail

> chat_guardrail: 최종 답변에 대해 안전/정책/PII/모더레이션/기본 팩트 일관성 등을 검사하는 단계
> 

### 7-1. 단순/복잡/고위험 케이스

**단순**

- 욕설/혐오발언/성인 콘텐츠 탐지, PII(전화번호/이메일) 검출.

**복잡**

- 맥락 의존적인 혐오 표현, 허위 정보·선동성 콘텐츠 판단.

**고위험**

- 의료/법률/자해·폭력 권유 등 safety 정책 위반을 놓치면 큰 리스크가 있는 케이스.

---

### 7-2. SLM/LLM 방향성

### 1차 Guardrail: SLM이 더 적합하다는 근거

**① SLM-Mod 논문** 📊

- **링크:** https://arxiv.org/abs/2410.13155
- **핵심 문장:**
    - "Using 150K comments from 15 popular Reddit communities, we find that SLMs (<15B) outperform zero-shot LLMs at content moderation—11.5% higher accuracy and 25.7% higher recall on average across all communities."
- 이는 컨텐츠 모더레이션에서는 잘 튜닝된 SLM이 LLM보다 더 정확하고, 민감 사례도 더 잘 잡는다는 직접적인 근거.

**② SLM 서베이**

- **링크:** https://arxiv.org/html/2409.15790v1
- 좁은 도메인 태스크(분류/필터링)에서는 작은 모델을 특화시키는 것이 효율적이라는 관찰.
- → chat_guardrail의 1차 필터(모더레이션/PII/정책 태그)는 SLM/특화 모델이 LLM보다 더 적합하다.

### 2차 High-risk 판단: LLM을 보조적으로 사용할 수 있는 근거

- 고위험 도메인(의료·법률)에서 답변의 안전성을 최종 판단할 때, 큰 LLM을 "판사(judge)"로 쓰는 패턴이 연구/서비스에서 많이 사용되고 있음.
- 예: radiology RAG 연구에서도 최종 권고의 안전성을 GPT-4 계열 judge가 평가하는 구조를 제안.

---

### 7-3. 성능·비용 마지노선

**1차 Guardrail (SLM)**

- **비용:** small/medium-tier (예: 7B~13B 정도) SLM, 자체 호스팅 또는 저렴한 API.
- **품질:**
    - 내부 모더레이션 Eval에서 zero-shot LLM(GPT-4o 등) 대비 Accuracy/F1이 동등 이상, 혹은 SLM-Mod 논문 수준(Accuracy +11.5%p, Recall +25.7%p)에 근접.

**2차 High-risk Judge (LLM) – 옵션**

- **비용:** LLM 호출은 high-risk 케이스 일부에만 적용.
- **품질:** 내부 safety Eval에서 false negative(위험 콘텐츠를 통과시키는 비율)를 최소화.

---

### 7-4. Primary / 장애 Fallback 후보

**Primary 후보 (SLM Guardrail 모델)** 📊

- **QwenGuard-8B, LlamaGuard, Granite-Guardian 등**
    - 각 모델 카드/논문에서 toxicity/hate/harassment/moderation 벤치마크를 제공하며, SLM-Mod 결과와 일관되게 작은 모델의 모더레이션 성능이 높게 보고된다.
    - **링크 예:**
        - Llama Guard: https://ai.meta.com/blog/llama-guard-safety-tools/
        - QwenGuard: https://qwenlm.github.io/blog/qwenguard/

**장애 Fallback / High-risk Judge 후보 (LLM)** 📊

- **Claude 3.5 Sonnet**
    - 복합 reasoning과 safety 판단에 강점, Anthropic가 안전성 중심 모델 연구를 많이 진행.
- **GPT-4o**
    - GPT-4o 시스템 카드에서 safety alignment·컨텐츠 필터링 메커니즘을 상세 설명.

---

## 8. agent_draft

> agent_draft: 에이전트 프롬프트/정책 Draft 생성
> 

### 8-1. 단순/복잡/고위험 케이스

**단순**

- 짧은 설명 기반으로 간단한 역할/톤 정도만 정의하는 에이전트.

**복잡**

- 긴 히스토리·도메인 문서·툴 설명을 읽고, 시스템 프롬프트, 툴 사용 규칙, 예시 대화, 실패 케이스까지 설계해야 하는 에이전트.

**고위험**

- 법률/의료/재무/보안 에이전트처럼, 프롬프트 설계 오류가 실제 리스크로 이어질 수 있는 경우.

---

### 8-2. SLM/LLM 방향성

### LLM이 적합한 근거

**① 복합 reasoning·코딩·문서 이해 능력** 📊

- **Claude 3.5 Sonnet 모델 카드 Addendum**
- **링크:** https://www-cdn.anthropic.com/fed9cc193a14b84131812372d8d5857f8f304c52/Model_Card_Claude_3_Addendum.pdf
- **핵심 문장:** "Claude 3.5 Sonnet sets new performance standards in evaluations of graduate-level science knowledge (GPQA), general reasoning (MMLU), and coding proficiency (HumanEval) … We saw large improvements in coding, documents, creative writing, and vision."
- 에이전트 프롬프트·정책 설계는 긴 문서 이해 + 규칙 추상화 + 코드/툴 사용까지 포함되므로, Sonnet급 LLM이 필요.

**② 실제 복잡 도메인 사례**

- FinEval 등 금융 벤치마크에서 Claude 3.5 Sonnet가 여러 금융 도메인 카테고리에서 highest weighted average score를 기록.
- **링크:** http://arxiv.org/pdf/2308.09975.pdf
- 금융·법률 등 정책이 복잡한 도메인에서 강한 성능을 보여, 해당 도메인 에이전트 Draft 설계에 적합.

→ **agent_draft는 고난도 추상화·플래닝/정책 설계가 핵심이므로 LLM을 Primary로 쓰는 것이 합리적이다.**

---

### 8-3. 성능·비용 마지노선

**성능**

- 내부 평가에서, LLM이 생성한 시스템 프롬프트/정책으로 만든 에이전트가 GPT-4o 기반 수작업 프롬프트 대비 태스크 성공률 ≥ 90% 수준.

**비용**

- Draft 생성은 상대적으로 호출 빈도가 낮고, 결과는 장기간 사용되므로, 비용보다는 품질 우선(LLM 가격 허용).

---

### 8-4. Primary / 장애 Fallback 후보

**Primary 후보 (LLM)** 📊

- **Claude 3.5 Sonnet**
    - 이유: 복합 reasoning·문서 이해·코딩에서 업계 상위권 성능.

**장애 Fallback 후보 (LLM)** 📊

- **GPT-4o**
    - GPT-4o 시스템 카드에서 reasoning·코딩·멀티모달 능력이 GPT-4와 동급 이상이며, latency·비용은 낮춘 것으로 설명.
    - **링크:** http://arxiv.org/pdf/2410.21276.pdf

---

---

## 9. agent_recommend

> agent_recommend: 에이전트 추천
> 

### 9-1. 단순/복잡/고위험 케이스

**단순**

- "문서 요약용 에이전트 vs 검색용 에이전트"처럼 간단 선택.

**복잡**

- 사용자의 프로필/히스토리/도메인/비용·지연 요구를 모두 고려해 최적 에이전트 조합을 추천.

**고위험**

- 규제 도메인(의료/법률)에서 잘못된 에이전트를 추천하면 위험한 경우.

---

### 9-2. SLM/LLM 방향성

### LLM이 적합한 근거

**① 다양한 기준을 종합하는 multi-criteria reasoning 필요**

**② Gemini 1.5 Pro의 long-context reasoning** 📊

- **Gemini 1.5 보고서**
- **링크:** https://arxiv.org/pdf/2403.05530.pdf
- **핵심 요약:**
    - Gemini 1.5 Pro는 multimodal long-context 모델로, millions of tokens 컨텍스트에서 정보를 recall·reason 할 수 있으며, 다양한 long-document QA·reasoning 벤치마크에서 state-of-the-art 성능.
- 에이전트 추천은 긴 히스토리/설정을 보고 판단할 수 있어야 하므로 Pro급 LLM이 필요.

### SLM이 맞지 않는 이유

- SLM 서베이에서 multi-hop reasoning·복합 로직에서는 SLM이 LLM에 비해 성능 격차가 크다고 명시.
- agent_recommend는 "간단 분류" 수준을 넘어서는 복합 로직에 속함.

---

### 9-3. 성능·비용 마지노선

**성능**

- 내부 평가에서, 에이전트 추천이 "사람이 설계한 룰 기반 라우팅" 대비 정확도(적절한 에이전트 선택률) ≥ 90%.

**비용**

- 호출 빈도는 Routing/Research보다 낮고, 잘못된 추천이 전체 UX에 큰 영향 → LLM 비용 허용.

---

### 9-4. Primary / 장애 Fallback 후보

**Primary 후보 (LLM)** 📊

- **Gemini 1.5 Pro**
    - 긴 문맥·multimodal·복합 reasoning에 강함.

**장애 Fallback 후보 (SLM)**

- **GPT-4o mini**
    - 간단 추천/분류 수준은 small 모델로도 충분, 비용 효율적.

---

---

## 10. tagging

> tagging: 문서 태깅/분류
> 

### 10-1. 단순/복잡/고위험 케이스

**단순**

- 일반 문서(뉴스, 블로그, 내부 보고서)에 대해 토픽·키워드·문서 타입 태깅.

**복잡**

- 매우 긴 문서나 코드베이스, 멀티모달 문서(이미지+텍스트) 태깅.

**고위험**

- 법률/의료/규제 문서에서 잘못된 태깅이 검색·접근 제어에 영향을 주는 경우.

---

### 10-2. SLM/LLM 방향성

### SLM이 적합한 근거

**① SLM 서베이** 📊

- **링크:** https://arxiv.org/html/2409.15790v1
- classification·요약 태스크에서 SLM과 LLM의 성능 차이가 크지 않고, latency·비용 이득이 크다고 분석.
- 문서 태깅은 전형적인 classification 작업.

**② Gemini 1.5 Flash** 📊

- **Google 블로그**
- **링크:** https://developers.googleblog.com/en/gemini-15-pro-and-15-flash-now-available/
- **핵심 문장:** Flash는 high-volume tasks 및 데이터 추출·요약에 최적화된 경량 모델로, 긴 문서도 빠르게 처리.
- 태깅은 대량·고빈도이므로 Flash 같은 SLM이 적합.

### LLM이 필요한 경우

- 특수 도메인(법률/의료)에서 fine-grained 태깅이 필요할 때, 샘플링 검증용으로 LLM을 사용 가능.
- 하지만 메인 태깅 파이프라인은 SLM이 비용 구조상 맞다.

---

### 10-3. 성능·비용 마지노선

**비용**

- 문서 수가 많으므로, small-tier 가격(≤$1/1M tokens)을 목표.

**품질**

- 내부 라벨링 기준 F1 ≥ 0.9 수준(도메인별 조정).
- 대량 문서에 대해 처리량(throughput)이 충분해야 함.

---

### 10-4. Primary / 장애 Fallback 후보

**Primary 후보 (SLM)** 📊

- **Gemini 1.5 Flash**
    - high-volume, low-latency summarization/data extraction/분류에 특화.

**장애 Fallback 후보 (SLM)** 📊

- **GPT-4o mini**
    - 분류·요약·추출에 충분한 성능, very low cost.
- **Claude 3 Haiku**
    - 매우 빠른 처리 속도와 저비용으로, 대량 태깅 Fallback에 적합.

---

---

## 11. title_gen

> title_gen: 제목 자동 생성
> 

### 11-1. 단순/복잡/고위험 케이스

**단순**

- 문서/대화 내용을 한두 줄 제목·요약으로 압축.

**복잡**

- 특정 톤(마케팅, 테크니컬, 보고서 스타일)에 맞추거나, 다국어 제목 생성.

**고위험**

- 거의 없음. 내용 정확도는 앞 단계에서 보장된 상태에서 표현만 바꾸는 작업.

---

### 11-2. SLM/LLM 방향성

### SLM이 적합한 근거

**① GPT-4o mini의 요약·확장 성능** 📊

- **LCFO 논문**
- **링크:** http://arxiv.org/pdf/2412.08268.pdf
- **핵심 문장:** GPT-4o-mini가 summarization·summary expansion에서 자동 시스템 중 최고 점수를 기록, 일부 지표에서 인간을 초과.
- 제목 생성은 요약/압축·카피에 해당.

**② 비용·지연 측면** 📊

- 제목 생성은 모든 대화/문서에 대해 반복 호출되므로, small-tier 비용이 중요.
- 4o mini는 GPT-4o 대비 30~50배 저렴.

→ **title_gen에는 SLM이 자연스러운 선택이고, LLM을 쓸 이유가 별로 없다.**

---

### 11-3. 성능·비용 마지노선

**비용**

- small-tier (≤$1/1M), 4o mini 가격 수준 목표.

**품질**

- human eval에서 제목의 정보량·자연스러움·간결성이 GPT-3.5 이상.

---

### 11-4. Primary / 장애 Fallback 후보

**Primary 후보 (SLM)**

- **GPT-4o mini**
    - 요약·카피에서 SOTA급, 비용 효율적.

**장애 Fallback 후보 (SLM)** 📊

- **Claude 3 Haiku**
    - 빠른 요약/포맷에 적합한 경량 모델.
- **Gemini 1.5 Flash**
    - 대량 제목 생성/메타데이터 생성용으로 적합.

---

---

## 12. doc_chat

> doc_chat: 문서 기반 QA
> 

### 12-1. 단순/복잡/고위험 케이스

**단순**

- 짧은 문서/FAQ에서 간단 질문에 답하는 수준.

**복잡**

- 여러 문서·규정·코드 조각을 통합, cross-reference·조건 비교가 필요한 QA.

**고위험**

- 의료/법률/재무/안전 관련 문서에 기반한 QA (오답 리스크 큼).

---

### 12-2. SLM/LLM 방향성

### LLM이 적합한 근거

**① 긴 문맥·복합 reasoning에서 LLM 우위** 📊

- **Gemini 1.5 Pro 논문**
- **링크:** https://arxiv.org/pdf/2403.05530.pdf
- **핵심 내용:** Gemini 1.5 Pro는 millions of tokens 컨텍스트에서 long-document QA, long-video QA, long-context ASR 등에서 경쟁 모델을 상회.
- doc_chat는 긴 문서 기반 QA이므로, 긴 컨텍스트 LLM이 필요.

**② LLM vs 작은 모델 RAG 품질 차이** 📊

- **Milvus 블로그(모델 사이즈 vs RAG 설계)**
- **링크:** https://milvus.io/ai-quick-reference/how-does-model-size-or-type-eg-gpt3-vs-smaller-opensource-models-affect-how-you-design-the-rag-pipeline
- **핵심 요약:** 큰 모델(GPT-4급)은 여러 문서를 넣어도 robust하게 통합 reasoning을 수행하지만, 작은 모델은 컨텍스트 한계·reasoning 약점 때문에 더 많은 전처리·튜닝이 필요하며 정확도도 낮은 경향.

**③ 실제 의료/임상 연구에서 LLM이 더 높은 QA 품질**

- 예: radiology contrast media consultation RAG 연구에서 GPT-4 계열이 local LLM보다 더 정확한 답변을 제공.

→ **doc_chat는 LLM을 Primary로 쓰는 것이 합리적이고, SLM으로는 복잡·고위험 QA에서 품질 보장이 어렵다.**

---

### 12-3. 성능·비용 마지노선

**성능**

- 내부 Doc QA Eval에서 GPT-4o를 기준으로 정답률 ≥ 90%, 환각률·"모르겠다" 처리율 유사 수준.

**비용**

- doc_chat 트래픽은 chat_simple보다 낮고, 다수 고위험 도메인 → 비용보다 품질 우선.

---

### 12-4. Primary / 장애 Fallback 후보

**Primary 후보 (LLM)** 📊

- **Claude 3.5 Sonnet**
    - 복잡 reasoning·문서 이해에서 상위권, 금융/법률/의료 사례 연구에서 강한 성능을 보여줌.

**장애 Fallback 후보 (LLM)** 📊

- **Gemini 1.5 Pro**
    - long-document QA·멀티모달 long-context reasoning에 특화.
- **GPT-4o**
    - 일반 long-context QA·코드/텍스트 혼합 도메인에서 강력한 LLM.

---

# Chat Pipeline 단계별 후보 조합

| **단계** | **Primary SLM/LLM 후보** | **장애 Fallback 후보** |
| --- | --- | --- |
| chat_routing | Gemini 1.5 Flash / Flash-8B (Google) ① ② · GPT-4o mini (OpenAI) ③ · Claude 3 / 3.5 Haiku (Anthropic) ④ | GPT-4o mini · Claude 3/3.5 Haiku · Gemini 1.5 Flash |
| chat_research | GPT-4o mini ③ ⑨ · Gemini 1.5 Flash ① ② · Claude 3/3.5 Haiku ④ | Gemini 1.5 Flash · Claude 3/3.5 Haiku · GPT-4o mini |
| chat_simple | GPT-4o mini ③ ⑩ · Gemini 1.5 Flash ① · Claude 3/3.5 Haiku ④ ⑪ | Gemini 1.5 Flash · Claude 3/3.5 Haiku · GPT-4o mini |
| chat_complex | Claude 3.5 Sonnet (Anthropic) ⑫ ⑤ · GPT-4o (OpenAI) ⑬ · Gemini 1.5 Pro (Google) ⑥ ⑦ | Claude 3.5 Sonnet ⇔ GPT-4o ⇔ Gemini 1.5 Pro 서로 교차 Fallback |
| chat_bulk | Gemini 1.5 Flash / Flash-8B ① ⑭ · GPT-4o mini ③ · Claude 3/3.5 Haiku ④ | GPT-4o mini · Claude 3/3.5 Haiku · Gemini 1.5 Flash |
| chat_synthesis | GPT-4o mini ⑨ ③ · Gemini 1.5 Flash ① ② · Claude 3/3.5 Haiku ④ | Gemini 1.5 Flash · Claude 3/3.5 Haiku · GPT-4o mini |
| chat_guardrail (1차 SLM) | Guardrail SLM (QwenGuard-8B, LlamaGuard, Granite-Guardian 등) ⑧ | Claude 3.5 Sonnet ⑤ · GPT-4o ⑬ (High-risk judge 또는 장애 시) |

---

# AI Hub / AI Drive 단계별 후보 조합
| **영역** | **단계** | **Primary 후보** | **장애 Fallback 후보** |
| --- | --- | --- | --- |
| AI Hub | agent_draft | Claude 3.5 Sonnet ⑫ ⑤ · GPT-4o ⑬ · Gemini 1.5 Pro ⑥ | GPT-4o · Gemini 1.5 Pro · Claude 3.5 Sonnet (서로 교차) |
| AI Hub | agent_recommend | Gemini 1.5 Pro ⑥ ⑦ · GPT-4o ⑬ · Claude 3.5 Sonnet ⑤ | GPT-4o mini ③ · Gemini 1.5 Flash ① |
| AI Drive | tagging | Gemini 1.5 Flash / Flash-8B ① ⑭ · GPT-4o mini ③ · Claude 3/3.5 Haiku ④ ⑪ | GPT-4o mini · Claude 3/3.5 Haiku · Gemini 1.5 Flash |
| AI Drive | title_gen | GPT-4o mini ⑨ ③ · Claude 3/3.5 Haiku ④ · Gemini 1.5 Flash ① | Claude 3/3.5 Haiku · Gemini 1.5 Flash · GPT-4o mini |
| AI Drive | doc_chat | Claude 3.5 Sonnet ⑫ ⑤ · GPT-4o ⑬ · Gemini 1.5 Pro ⑥ ⑦ | Claude 3.5 Sonnet ⇔ GPT-4o ⇔ Gemini 1.5 Pro 서로 교차 Fallback |