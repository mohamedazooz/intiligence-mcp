# OmniPulse MCP — المخطط الهندسي الشامل وخارطة الطريق (Seed → Trigger → Production)

> **التصنيف المعماري:** Universal Research, Engineering & Intelligence Orchestrator MCP  
> **الفلسفة التشغيلية:** Zero-Rewrite Assembly (تجميع 85–90% من مشاريع مفتوحة موثقة + ~400–500 سطر نواة ربط نظيفة بـ Python FastMCP v4)  
> **الهدف الرئيسي:** نقطة اتصال واحدة (`Streamable HTTP`) بـ **3 أدوات فقط** تخدم أي AI Agent في أي مجال (تأسيس مشاريع جديدة بأحدث المكتبات والـ Best Practices، بحث ويب ومنافسين، أوراق علمية وخوارزميات، واستخبارات OSINT/Dark Web اختيارية) مع توفير **90% إلى 96% من التوكنز** وصفر فشل صامت.

---

## 1. الملخص التنفيذي والفكرة الفريدة (Why OmniPulse?)

### 1.1 المشاكل الهيكلية التي يحلها المشروع
1. **انتحار نافذة السياق (Context Window Suicide):** ربط 10–15 سيرفر MCP تقليدي يكشف 250–350 أداة للـ LLM، مما يستهلك 35,000–50,000 توكن في كل طلب قبل كتابة السؤال، ويزيد احتمالية الهلوسة واختيار أدوات خاطئة.
2. **فجوة الواقع البرمجي (The Reality Split):** الحصول على التوثيق الرسمي وحده لا يكفي؛ المشاريع الحقيقية تحتاج مطابقة متزامنة بين **(التوثيق الرسمي + الكود المصدري الفعلي للمكتبة + مشاكل المجتمع على GitHub/Reddit + هيكل ريبو Production مرجعي)**.
3. **الجزر المعزولة وفقدان الذاكرة (Stateless Silos):** أدوات البرمجة معزولة عن السكرابينج المتخفي ومعزولة عن الـ OSINT، والنتائج تموت بمجرد إغلاق جلسة الشات.
4. **العمى الاستخباراتي (Silent Failure Blindness):** أغلب الأدوات تُعيد قائمة فارغة `[]` عند سقوط Tor أو انتهاء مفتاح API أو حظر Cloudflare، مما يخدع الـ Agent ويجعله يستنتج "لا توجد نتائج".

### 1.2 الفكرة الفريدة: النمط الهجين بنظام الخراطيش (Hybrid Cartridge Orchestrator)
* **90% تنفيذ حتمي مستقل داخل الـ MCP (0 LLM Tokens أثناء البحث والربط)** + **10% تفكير واستنتاج من الـ Agent**.
* **واجهة الـ 3 أدوات فقط (3-Tool Facade):** يرى أي Agent ثلاث أدوات عالية المستوى فقط (`research_mission`، `deep_drill`، `watch_pulse`)، بينما يختار **مصنّف النوايا الداخلي (Intent Router)** تلقائياً "الخرطوشة" المناسبة (`BUILD` | `WEB_MARKET` | `ALGO_PAPERS` | `OSINT_DARK`).
* **إيصال التغطية الجنائي (Forensic Coverage Ledger):** كل رد يصدر معه جدول صريح يُثبت المصادر التي نجحت، والمصادر التي تم تخطيها والسبب (API Key مفقود، Timeout، أو Profile مغلق).
* **الرادار ذاتي الإصلاح (Self-Healing Watchdog):** دمج `SQLite Background Poller` مع `Scrapling Smart Element Tracking` و `arXiv watch_topic` لمراقبة التحديثات (Breaking Changes، أوراق جديدة، تغييرات صفحات محمية، أو تسريبات) وإرسال **الدلتا فقط (Delta Alerts)** عبر Telegram/Webhook.

### 1.3 العلاقة مع مستودعاتك القائمة (Separation of Concerns)

| المستودع | الدور المعماري | علاقته بالمشروع الجديد |
|---|---|---|
| **`omnipulse-mcp` (جديد على نظافة)** | **النواة وبوابة الأدوات (Universal MCP Hub)** | يُبنى على نظافة بهيكل Python FastMCP v4 و Docker Profiles و Git History نظيف للـ Production. |
| **`intiligence-mcp` (قائم)** | **مخزن قطع غيار / Worker متخصص (Donor Repo)** | لا ندمج النواة داخله؛ نقتبس منه الـ Adapters المجربة (Dark Web / Captcha / Scrapling tweaks) ونركّبها داخل بروفايل `--profile osint-dark`. |
| **`MULTI-AGENTS-OPS` (قائم)** | **طبقة المستهلك (Client / Agent Fleet)** | يتصل بـ `omnipulse-mcp` عبر URL واحد (`Streamable HTTP` + Bearer Token) بدون أي Coupling في الكود. |

---

## 2. مصفوفة الاقتباس والتجميع (Zero-Rewrite Assembly Matrix)

نطبق قاعدة **عدم إعادة كتابة أي أداة قائمة** عبر 3 مستويات:
* **المستوى 1 (`Docker Plug & Play`):** سحب الصورة الرسمية وتوصيلها على الشبكة الداخلية `intel_net` (0 سطور كود).
* **المستوى 2 (`MCP-over-MCP`):** استدعاء السيرفر برمجياً من داخل النواة عبر `FastMCP Client` (يحافظ على التحديثات الرسمية تلقائياً).
* **المستوى 3 (`Pattern Cherry-Picking`):** اقتباس الفكرة المعمارية أو المنطق الصغير فقط داخل كود النواة (~400–500 سطر إجمالاً).

### 2.1 جدول الاقتباس الكامل من المشاريع المفتوحة

| # | المشروع المفتوح المصدر | الخرطوشة المستهدفة | مستوى الدمج | الجوهرة التي سنقتبسها بالضبط | ما سنستبعده (لتقليل الثقل والتكرار) |
|---|---|---|---|---|---|
| 1 | **`PrefectHQ/fastmcp` (v4.2+)** | Core Kernel | Library | نواة السيرفر، `FastMCP Client` للتجميع، `task=True` للمهام الطويلة (SEP-2663)، Cache Hints، و Streamable HTTP. | لا نكشف أدوات السيرفرات الخلفية مباشرة للـ Agent. |
| 2 | **`metatool-ai/metamcp`** | Gateway | المستوى 1 (Docker) | بوابة التجميع، الـ Namespaces، عزل الصلاحيات (PKCE/Bearer)، و Middleware فلترة الأدوات. | لا نستخدمه لإظهار 300 أداة؛ نعرض الـ 3 أدوات الموحدة فقط. |
| 3 | **`upstash/context7` (v4.7+)** | `BUILD` | المستوى 2 (MCP Client) | سحب التوثيق حسب الإصدار (`query-docs`)، البحث في الكود المصدري (`query-code`)، ودليل الترقية (`get-upgrade-guide`). | لا نعتمد عليه وحده بدون فحص مشاكل المجتمع الحية. |
| 4 | **`yamadashy/repomix`** | `BUILD` / `ALGO` | المستوى 2 (MCP/CLI) | ضغط مستودعات GitHub عن بُعد بـ **Tree-sitter** (توفير ~70% توكنز) واستخراج الهيكلة مع `Secretlint`. | لا نسحب ملفات الـ Lockfiles أو الأصول الثنائية أو الاختبارات الضخمة افتراضياً. |
| 5 | **`searxng/searxng` + `mcp-searxng`** | كل الخراطيش | المستوى 1 (Docker) | محرك بحث ميتا ذاتي الاستضافة (Google/GitHub/Reddit/HN/SO) ببحث متعدد متوازي وتصنيف (`it`, `science`, `social_media`). | لا نستخدمه كبديل للسكرابينج؛ يكتفي بجلب الروابط والملخصات الأولية. |
| 6 | **`unclecode/crawl4ai` (v0.9.6)** | `WEB_MARKET` / `BUILD` | المستوى 1 (Docker) | تحويل صفحات الويب والتوثيق إلى `fit_markdown` مضغوط عبر Browser Pool محمي. | لا نستخدمه للمواقع المحمية بـ Cloudflare Turnstile الثقيلة (نُصعّد لـ Scrapling). |
| 7 | **`D4Vinci/Scrapling`** | `WEB_MARKET` / `OSINT` | المستوى 1 (Docker) | تخطي Cloudflare و TLS/HTTP3 Spoofing، `browser_fetch_once` مع DoH، و **Smart Element Tracking** للرادار ذاتي الإصلاح. | لا نشغله على الصفحات العادية؛ يعمل بآلية التصعيد التدريجي فقط توفيراً للـ RAM. |
| 8 | **`blazickjp/arxiv-mcp-server` (v0.8.2)** | `ALGO_PAPERS` | المستوى 2 (MCP Client) | البحث في الأوراق العلمية، قراءة أقسام **LaTeX** انتقائياً، وميزة `watch_topic` للمراقبة الدورية. | لا نفرّغ الـ PDF بالكامل داخل السياق. |
| 9 | **`badchars/darknet-mcp-server`** | `OSINT_DARK` | المستوى 2 (MCP Client) | محولات HIBP و IntelX و Ransomware.live و RansomLook و Ahmia.fi وفحص Tor SOCKS5 (`--check-tor`). | لا نشغله كسيرفر stdio مستقل مكشوف للـ LLM. |
| 10 | **`badchars/osint-mcp-server`** | `OSINT_DARK` | المستوى 2 + 3 | الاستطلاع السلبي (crt.sh، Wayback Machine، BGP، تدقيق SPF/DMARC/DKIM) ونمط التحقق الصارم بالـ Schemas. | لا نسمح للـ Agent باستدعاء الـ 37 أداة يدوياً. |
| 11 | **`Vinaysati/Darknet-Mcp`** | Core + `OSINT_DARK` | المستوى 3 (Pattern) | فلسفتان جوهريتان: **(1) Auto Target Classifier** و **(2) Explicit Coverage Ledger** لمنع الفشل الصامت + محول `ChainAbuse` و `Hudson Rock`. | نستغني عن التكرار مع `badchars` وعن الواجهة المستقلة في المرحلة الأولى. |
| 12 | **`pete-builds/mcp-threatintel`** | Core Memory | المستوى 3 (Pattern) | نمط **SQLite Local Cache + Background Poller** وفحص التسريبات بـ `k-anonymity`. | نطوّر الـ SQLite من مجرد IOCs إلى Entity Graph شامل لكل أنواع الأبحاث. |
| 13 | **`Hackerobi/pentest-osint-mcp-server`** | `OSINT_DARK` | المستوى 1 (Docker Profile) | حاوية Docker المعزولة لأدوات الـ CLI الثقيلة (`Maigret`, `Holehe`, `dnstwist`, `theHarvester`). | يعمل كـ On-Demand Worker بحدود RAM و Timeout صارمة فقط. |
| 14 | **`seszele64/scrapling-mcp`** | Core Guard | المستوى 3 (Pattern) | منطق **حماية SSRF** (حظر الشبكات الخاصة و Metadata IPs) وتدرج مستويات التخفي الـ 3 + دعم `Camoufox`. | لا نستخدم الـ Wrapper كحاوية إضافية لأن `Scrapling` الرسمي يضم MCP مدمج. |
| 15 | **`0x4m4/hexstrike-ai`** | Core + `deep_drill` | المستوى 3 + جراحي | فكرة **LRU Result Caching**، وإتاحة أدوات جراحية محددة فقط مثل `nuclei` عند الطلب عبر `deep_drill`. | **نرمي باقي الـ 250 أداة** لتجنب استنزاف الـ RAM والسياق. |

---

## 3. النمذجة المعمارية بنموذج C4 (Full C4 Architecture)

### 3.1 Level 1 — System Context Diagram (سياق النظام)
يوضح كيف يتعامل المستخدم ووكلاء الذكاء الاصطناعي (`MULTI-AGENTS-OPS` أو الـ IDEs) مع **OmniPulse MCP** كصندوق أسود ذكي واحد، دون التعرض لتعقيد عشرات المصادر الخارجية.

~~~mermaid
C4Context
    title Level 1: System Context — OmniPulse MCP

    Person(user, "المطور / المحلل", "يطلب بحثاً لمشروع جديد، تحليل سوق، ورقة علمية، أو فحص OSINT")

    System_Boundary(clients, "طبقة الوكلاء (Agent Layer)") {
        System(ide_agents, "AI Coding IDEs", "Cursor, Antigravity, Roo Code, Cline, Claude Desktop")
        System(multi_agents, "MULTI-AGENTS-OPS", "منصة الوكلاء الذاتية و Telegram Bots")
    }

    System(omnipulse, "OmniPulse MCP Platform", "بوابة البحث والاستخبارات الشاملة بـ 3 أدوات فقط، خراطيش تلقائية، ذاكرة Graph، ورادار ذاتي الإصلاح")

    System_Ext(dev_sources, "مصادر الهندسة والأبحاث", "Context7 Docs/Code, GitHub Repos, arXiv, Reddit, HN")
    System_Ext(web_sources, "الويب المفتوح والمحمي", "Search Engines عبر SearXNG, مواقع محمية بـ Cloudflare")
    System_Ext(dark_sources, "مصادر OSINT والدارك ويب (اختياري)", "Tor .onion, Ahmia, Ransomware.live, HIBP, ChainAbuse, crt.sh")
    System_Ext(notify_ext, "قنوات التنبيه", "Telegram Bot API / Custom Webhooks")

    Rel(user, ide_agents, "أوامر طبيعية بالعربي/الإنجليزي")
    Rel(user, multi_agents, "مهام آلية ومراقبة")
    Rel(ide_agents, omnipulse, "Streamable HTTP + Bearer Token (3 أدوات)")
    Rel(multi_agents, omnipulse, "Streamable HTTP + Bearer Token (3 أدوات)")

    Rel(omnipulse, dev_sources, "سحب توثيق، كود مضغوط، أوراق LaTeX")
    Rel(omnipulse, web_sources, "بحث متوازي + Crawl4AI + تصعيد Scrapling")
    Rel(omnipulse, dark_sources, "فحص عبر Tor SOCKS5 وبروفايل معزول")
    Rel(omnipulse, notify_ext, "تنبيهات الدلتا (Watchdog Delta Alerts)")
~~~

---

### 3.2 Level 2 — Container Diagram (مخطط الحاويات وبروفايلات Docker)
يوضح العزل الهندسي عبر **3 Docker Profiles** تسمح بتشغيل النواة الأساسية على VPS خفيف (4GB RAM) وتفعيل الحاويات الثقيلة فقط عند الحاجة.

~~~mermaid
C4Container
    title Level 2: Container Diagram — OmniPulse MCP & Docker Profiles

    System_Ext(agent, "AI Agent / MULTI-AGENTS-OPS", "يرى 3 أدوات فقط عبر Endpoint واحد")

    Container_Boundary(default_prof, "Profile: default (يعمل دائماً — أقل من 700MB RAM)") {
        Container(gateway, "MetaMCP Gateway", "TypeScript / Docker", "عزل Namespaces، مصادقة PKCE/Bearer، Rate Limiting")
        Container(core, "OmniPulse Core", "Python 3.12 / FastMCP v4", "الـ 3 أدوات، Intent Router، Pivot Engine، Watchdog، SSRF Guard")
        ContainerDb(sqlite, "Knowledge & Graph Store", "SQLite WAL + FTS5", "جداول Missions, Entities, Edges, Coverage Receipts, Watch Deltas")
        Container(searxng, "SearXNG Engine", "Python / Docker", "بحث ميتا غير محدود بدون API Keys")
        Container(dev_mcps, "Dev & Papers Sidecars", "Context7 + Repomix + arXiv", "توثيق وكود المكتبات، ضغط Tree-sitter، وأقسام LaTeX")
    }

    Container_Boundary(crawl_prof, "Profile: web-crawl (عند الحاجة — ~1.5GB RAM)") {
        Container(crawl4ai, "Crawl4AI Worker", "Docker v0.9.6", "Browser Pool لاستخراج fit_markdown النظيف")
        Container(scrapling, "Scrapling Stealth Worker", "Docker / Camoufox", "تخطي Cloudflare + TLS Spoofing + Smart Element Tracking")
    }

    Container_Boundary(osint_prof, "Profile: osint-dark (اختياري — ~1.2GB RAM)") {
        Container(tor, "Tor SOCKS5 Proxy", "Docker (Port 9050)", "عزل حركة الدارك ويب ومواقع .onion")
        Container(osint_workers, "OSINT & Darknet Workers", "badchars + Hackerobi + intiligence-mcp", "Maigret, Holehe, dnstwist, Ahmia, Ransomware.live, ChainAbuse")
    }

    Rel(agent, gateway, "HTTPS / Streamable HTTP")
    Rel(gateway, core, "Internal HTTP (intel_net)")
    Rel(core, sqlite, "aiosqlite (WAL Read/Write)")
    Rel(core, searxng, "JSON Search API")
    Rel(core, dev_mcps, "FastMCP Client (MCP-over-MCP)")
    Rel(core, crawl4ai, "HTTP API (fit_markdown)")
    Rel(core, scrapling, "MCP / HTTP (Stealth Escalation)")
    Rel(core, osint_workers, "MCP Client / Subprocess Queue")
    Rel(osint_workers, tor, "SOCKS5h (DNS via Tor)")
~~~

---

### 3.3 Level 3 — Component Diagram (التشريح الداخلي لنواة `omnipulse-core`)
هذه هي الوحدات البرمجية القليلة (~400–500 سطر Python) التي سنكتبها فعلياً لربط الإمبراطورية كلها.

~~~mermaid
flowchart TB
    subgraph Core["OmniPulse Core (Python FastMCP v4)"]
        direction TB
        Facade["1. 3-Tool Facade (server.py)<br/>research_mission | deep_drill | watch_pulse"]
        Guard["2. Security & Policy Guard (guard.py)<br/>SSRF Blocklist + Token Cap + Rate/Depth Budget"]
        Router["3. Intent & Target Classifier (router.py)<br/>0 LLM Tokens — Regex/Heuristics -> Cartridge Selection"]
        Cache["4. Memory & Cache Layer (memory.py)<br/>LRU In-Memory + SQLite FTS5/WAL Entity Graph"]
        
        subgraph Cartridges["5. Pluggable Cartridges (cartridges/)"]
            C_Build["BUILD Cartridge<br/>Context7 + SearXNG + Repomix"]
            C_Web["WEB_MARKET Cartridge<br/>SearXNG -> Crawl4AI -> Scrapling"]
            C_Algo["ALGO_PAPERS Cartridge<br/>arXiv LaTeX + GitHub Match"]
            C_Osint["OSINT_DARK Cartridge<br/>Auto-Pivot + Tor + Darknet + CLI"]
        end

        Pool["6. Unified Client Pool (clients.py)<br/>FastMCP Client + httpx Async + Strict Timeouts"]
        Synth["7. Synthesizer & Coverage Ledger (ledger.py)<br/>Deduplication + Compression + Explicit Coverage Matrix"]
        Watch["8. Self-Healing Watchdog (watchdog.py)<br/>APScheduler + Delta Diff + Scrapling Adaptive + Telegram"]
    end

    Facade --> Guard --> Cache
    Cache -- "Cache Hit" --> Facade
    Cache -- "Cache Miss" --> Router
    Router --> C_Build & C_Web & C_Algo & C_Osint
    C_Build & C_Web & C_Algo & C_Osint --> Pool
    Pool --> Synth --> Cache
    Synth --> Facade
    Watch --> Router
    Watch --> Cache
~~~

---

### 3.4 Level 4 — Execution Sequence (دورة حياة الطلب + حل الـ Timeout + التصعيد التلقائي)

~~~mermaid
sequenceDiagram
    autonumber
    actor Agent as AI Agent (Cursor / MULTI-AGENTS-OPS)
    participant Core as OmniPulse Core (FastMCP v4)
    participant Cache as SQLite Graph & LRU
    participant Engines as Parallel Engines (Context7/SearXNG/Crawl4AI)
    participant Stealth as Scrapling (Cloudflare Bypass)
    participant TG as Telegram / Webhook

    Agent->>Core: research_mission(goal, mode="auto", depth="standard")
    Core->>Core: Guard Check (SSRF + Budget) + Intent Classify (0 Tokens)
    Core->>Cache: Check Freshness (LRU + SQLite FTS5)

    alt Cache Hit (صالح ولم تنتهِ صلاحيته)
        Cache-->>Core: Return Cached Brief + Coverage Receipt
        Core-->>Agent: Immediate Response (أقل من 1 ثانية)
    else Cache Miss (بحث حي)
        alt depth == "deep" (مهمة طويلة > 45 ثانية)
            Core-->>Agent: Return Async job_id فوراً (FastMCP Background Task)
            Note over Core,Engines: يستكمل التنفيذ في الخلفية بدون Timeout
        end

        par تنفيذ متوازي داخل الخرطوشة
            Core->>Engines: Query Docs/Code + SearXNG + Crawl4AI
            Core-->>Agent: MCP notifications/progress ("جاري فحص المصادر...")
        end

        alt واجه صفحة محمية بـ Cloudflare / 403
            Engines-->>Core: HTTP 403 / Challenge Detected
            Core->>Stealth: Auto-Escalate URL (Camoufox + TLS Spoof)
            Stealth-->>Core: Clean Markdown + Element Signature
        end

        Core->>Core: Build Entities/Edges + Explicit Coverage Ledger
        Core->>Cache: Persist Graph + Coverage Receipt
        Core-->>Agent: Compressed Brief (~1,500 Tokens) + Coverage Matrix

        opt إذا كان deep job أو Watchdog Delta
            Core->>TG: إرسال تنبيه بالنتيجة أو التغيير الجديد فقط
        end
    end
~~~

---

## 4. عقود الأدوات الثلاث (3-Tool Facade Specifications)

لتوفير أكثر من 90% من توكنز تعريف الأدوات، يتفاعل الـ Agent مع هذه العقود الصارمة فقط:

### 4.1 الأداة الأولى: `research_mission` (محرك البحث والربط الرئيسي)
~~~json
{
  "name": "research_mission",
  "description": "تنفيذ مهمة بحث شاملة ومستقلة عبر الخراطيش المتخصصة وإرجاع ملف مضغوط مع إيصال التغطية.",
  "inputSchema": {
    "type": "object",
    "required": ["goal"],
    "properties": {
      "goal": {
        "type": "string",
        "description": "الهدف البحثي أو البذرة (مثال: بناء نظام FastAPI+Rust بأحدث معايير 2026، أو دومين/هدف)"
      },
      "mode": {
        "type": "string",
        "enum": ["auto", "build", "web_market", "algo_papers", "osint_dark", "hybrid"],
        "default": "auto"
      },
      "depth": {
        "type": "string",
        "enum": ["quick", "standard", "deep"],
        "default": "standard",
        "description": "quick (<10s)، standard (15-40s مع progress)، deep (Async job_id بالخلفية)"
      },
      "force_refresh": {
        "type": "boolean",
        "default": false
      }
    }
  }
}
~~~

**هيكل المخرج الموحد (Compressed Mission Brief — الحد الأقصى الصارم 3,500 توكن):**
* `mission_id` و `status` (`completed` | `running_async`)
* `detected_cartridges`: الخراطيش التي اشتغلت فعلياً.
* `executive_findings`: الخلاصة المهيكلة (إصدارات مؤكدة، APIs حقيقية، مطبّات المجتمع، أو الكيانات والروابط المكتشفة).
* `drillable_refs`: قائمة معرفات قصيرة (`ref_id`) للريبوهات أو الأوراق أو العقد التي يمكن الغوص فيها بـ `deep_drill`.
* `coverage_receipt`: جدول صريح (`source` | `status: OK/SKIPPED/TIMEOUT/BLOCKED` | `latency_ms` | `reason`).

### 4.2 الأداة الثانية: `deep_drill` (المشرط الجراحي واستعلام المهام الخلفية)
~~~json
{
  "name": "deep_drill",
  "description": "التعمق الجراحي في مرجع محدد (ريبو، مكتبة، ورقة علمية، عقدة OSINT) أو جلب نتيجة job_id.",
  "inputSchema": {
    "type": "object",
    "required": ["ref_id", "action"],
    "properties": {
      "ref_id": {
        "type": "string",
        "description": "معرّف المرجع الناتج من research_mission أو job_id"
      },
      "action": {
        "type": "string",
        "enum": [
          "job_status",
          "upgrade_guide",
          "query_source_code",
          "pack_repo_tree",
          "read_paper_section",
          "stealth_scrape_url",
          "osint_cli_scan"
        ]
      },
      "params": {
        "type": "object",
        "description": "معاملات اختيارية مثل from_version/to_version أو section_name أو css_selector"
      }
    }
  }
}
~~~

### 4.3 الأداة الثالثة: `watch_pulse` (الرادار المستمر ذاتي الإصلاح)
~~~json
{
  "name": "watch_pulse",
  "description": "تفعيل أو إدارة مراقبة مستمرة لأي مكتبة أو موضوع بحثي أو صفحة ويب أو هدف استخباراتي مع تنبيه بالتغييرات فقط.",
  "inputSchema": {
    "type": "object",
    "required": ["operation"],
    "properties": {
      "operation": {
        "type": "string",
        "enum": ["arm", "list", "pause", "remove", "check_now"]
      },
      "target": {
        "type": "string",
        "description": "اسم مكتبة، موضوع arXiv، رابط صفحة منافس، أو معرّف كيان"
      },
      "watch_type": {
        "type": "string",
        "enum": ["library_release", "arxiv_topic", "stealth_page_diff", "osint_brand_leak"]
      },
      "cadence_hours": {
        "type": "integer",
        "default": 24,
        "minimum": 1
      }
    }
  }
}
~~~

---

## 5. شجرة الملفات الكاملة وشرح كل ملف (Repository Directory Tree)

~~~text
omnipulse-mcp/
├── README.md                         # دليل التثبيت السريع وربط الـ Agents في 3 دقائق
├── LICENSE                           # رخصة المشروع (MIT / Apache-2.0)
├── .gitignore                        # استبعاد .env و data/*.db و __pycache__
├── .env.example                      # قالب متغيرات البيئة والمفاتيح الاختيارية
├── docker-compose.yml                # المعمارية الكاملة بنظام Profiles (default, web-crawl, osint-dark)
├── Makefile                          # أوامر اختصار (make up, make up-crawl, make up-osint, make test)
│
├── config/                           # ملفات تهيئة الحاويات الجاهزة (بدون تعديل كودها)
│   ├── metamcp.json                  # تهيئة Namespaces وفلترة الأدوات على البوابة
│   ├── searxng/
│   │   └── settings.yml              # تفعيل صيغة JSON وتحديد المحركات (Google, GitHub, Reddit, arXiv)
│   └── limits.yaml                   # سقوف الموارد (Max Depth, Max Pivots, Timeouts, Max Output Tokens)
│
├── core/                             # ★ النواة الوحيدة التي نكتبها (~400-500 سطر Python)
│   ├── Dockerfile                    # حاوية Python 3.12-slim + uv سريعة وخفيفة
│   ├── pyproject.toml                # الاعتماديات: fastmcp>=4.2, httpx, aiosqlite, pydantic, apscheduler
│   ├── src/
│   │   └── omnipulse/
│   │       ├── __init__.py
│   │       ├── config.py             # قراءة الإعدادات و limits.yaml بـ Pydantic Settings
│   │       ├── server.py             # نقطة الدخول FastMCP v4 + تعريف الـ 3 أدوات + Auth Middleware
│   │       ├── router.py             # مصنّف النوايا والهدف (0 LLM Tokens) وتوجيه الخراطيش
│   │       ├── clients.py            # مجمع FastMCP Clients و httpx Async للاتصال بكل الحاويات
│   │       ├── guard.py              # حماية SSRF + DNS Validation + Token/Latency Circuit Breakers
│   │       ├── memory.py             # إدارة SQLite (WAL + FTS5) و LRU Cache و Entity Graph
│   │       ├── ledger.py             # بناء إيصال التغطية الصريح (Explicit Coverage Receipt)
│   │       ├── watchdog.py           # جدولة المراقبة المستمرة + Delta Diff Engine + Telegram Notifier
│   │       └── cartridges/           # الخراطيش الأربعة (كل خرطوشة ملف مستقل وقابل للتعطيل)
│   │           ├── base.py           # واجهة مجردة BaseCartridge (Interface موحد)
│   │           ├── build.py          # خرطوشة المشاريع الجديدة (Context7 + SearXNG + Repomix)
│   │           ├── web_market.py     # خرطوشة البحث العام والمنافسين (SearXNG + Crawl4AI + Scrapling)
│   │           ├── algo_papers.py    # خرطوشة الأبحاث العلمية (arXiv LaTeX + GitHub Code Match)
│   │           └── osint_dark.py     # خرطوشة الاستخبارات والدارك ويب (Auto-Pivot + Tor + Darknet)
│
├── workers/                          # عمال مخصصون يُبنون فقط عند الحاجة
│   └── osint-cli/
│       └── Dockerfile                # غلاف خفيف مبني فوق Hackerobi + أدوات مقتبسة من intiligence-mcp
│
├── scripts/                          # سكربتات تشغيل وصيانة
│   ├── healthcheck.py                # فحص حي لكل الحاويات النشطة و Tor SOCKS5
│   └── backup_sqlite.sh              # نسخ احتياطي آمن لقاعدة SQLite باستخدام VACUUM INTO
│
├── tests/                            # اختبارات حتمية (قبل كل نشر)
│   ├── test_guard_ssrf.py            # التحقق من حظر 127.0.0.1 و 169.254.169.254 والشبكات الخاصة
│   ├── test_router.py                # التحقق من دقة تصنيف النوايا والـ Auto Target Detection
│   ├── test_ledger_no_silent.py      # التحقق من تسجيل كل Timeout/Skip في إيصال التغطية
│   └── test_cartridge_build.py       # اختبار تكامل لخرطوشة BUILD وتأكد من سقف التوكنز
│
├── data/                             # مجلد التخزين الدائم (Mounted Volume — مستبعد من Git)
│   └── omnipulse.db                  # قاعدة SQLite (WAL Mode + FTS5)
│
└── docs/
    ├── OMNIPULSE_MCP_BLUEPRINT.md    # هذا الملف المرجعي
    └── AGENT_INTEGRATION.md          # أمثلة ربط Cursor و Antigravity و Roo Code و MULTI-AGENTS-OPS
~~~

### شرح مسؤولية الملفات الجوهرية في `core/src/omnipulse/`:
* **`server.py`:** يبني مثيل `FastMCP("OmniPulse")`، يطبق التحقق من الـ `Bearer Token`، ويسجل الأدوات الثلاث فقط مع دعم `task=True` للمهام العميقة وإرسال `ctx.report_progress(...)`.
* **`router.py`:** يحتوي على مصفوفة قواعد حتمية (Regex + Keyword Scoring) تميز فوراً بين: طلب هندسي/برمجي (`build`)، طلب ورقة/خوارزمية (`algo_papers`)، كيان استخباراتي مثل دومين/إيميل/محفظة/`.onion` (`osint_dark`)، أو بحث ويب عام (`web_market`).
* **`clients.py`:** يطبق نمط **Circuit Breaker لكل مصدر** — إذا فشل `Crawl4AI` أو أعاد `403/Cloudflare`، ينقل الرابط تلقائياً إلى `Scrapling`. وإذا كان بروفايل `osint-dark` مطفأً، يبلغ `ledger.py` فوراً بحالة `SKIPPED_PROFILE_OFF` بدلاً من كسر الطلب.
* **`guard.py`:** ينفذ DNS Resolution قبل أي طلب HTTP/Scrape ويرفض أي IP ينتمي إلى `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `::1`, أو `fc00::/7`.
* **`memory.py` + `ledger.py`:** يحولان مخرجات كل الخراطيش إلى كيانات وعلاقات (`Entities & Edges`) مع بصمة `content_hash` لاكتشاف التغييرات في الـ Watchdog.

---

## 6. تصميم قاعدة البيانات المحلية (SQLite WAL + FTS5 Schema)

نستخدم **SQLite بوضع WAL** بدلاً من Postgres/Neo4j لأن حجم البيانات المعرفية لآلاف الأبحاث يظل صغيراً وسريعاً جداً (أقل من 50MB RAM) ويدعم البحث النصي الكامل (`FTS5`) محلياً بدون حاوية إضافية.

~~~sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. سجل المهام والـ Async Jobs
CREATE TABLE IF NOT EXISTS missions (
    mission_id      TEXT PRIMARY KEY,
    goal            TEXT NOT NULL,
    mode            TEXT NOT NULL,
    depth           TEXT NOT NULL,
    status          TEXT NOT NULL, -- queued | running | completed | partial | failed
    summary_json    TEXT,
    token_estimate  INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at      DATETIME
);

-- 2. الكيانات المكتشفة (مكتبة، ريبو، ورقة، دومين، إيميل، محفظة، صفحة)
CREATE TABLE IF NOT EXISTS entities (
    entity_id       TEXT PRIMARY KEY,
    entity_type     TEXT NOT NULL, -- library | repo | paper | url | domain | email | wallet | onion | leak
    canonical_value TEXT NOT NULL,
    metadata_json   TEXT,
    content_hash    TEXT,
    first_seen      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen       DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, canonical_value)
);

-- 3. العلاقات والقفزات بين الكيانات (Entity Graph)
CREATE TABLE IF NOT EXISTS edges (
    edge_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id      TEXT NOT NULL,
    source_id       TEXT NOT NULL,
    target_id       TEXT NOT NULL,
    relation_type   TEXT NOT NULL, -- uses_library | implements_paper | leaked_in | typosquat_of | mentions
    confidence      REAL DEFAULT 1.0,
    evidence_url    TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(mission_id) REFERENCES missions(mission_id),
    FOREIGN KEY(source_id)  REFERENCES entities(entity_id),
    FOREIGN KEY(target_id)  REFERENCES entities(entity_id)
);

-- 4. دفتر التغطية الجنائي (يمنع الفشل الصامت نهائياً)
CREATE TABLE IF NOT EXISTS coverage_receipts (
    receipt_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id      TEXT NOT NULL,
    adapter_name    TEXT NOT NULL,
    status          TEXT NOT NULL, -- OK | SKIPPED_NO_KEY | SKIPPED_PROFILE_OFF | TIMEOUT | BLOCKED | ERROR
    latency_ms      INTEGER DEFAULT 0,
    items_found     INTEGER DEFAULT 0,
    detail_note     TEXT,
    recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(mission_id) REFERENCES missions(mission_id)
);

-- 5. أهداف الرادار المستمر وسجل التغييرات (Watchdog & Delta Engine)
CREATE TABLE IF NOT EXISTS watch_targets (
    watch_id        TEXT PRIMARY KEY,
    target_value    TEXT NOT NULL,
    watch_type      TEXT NOT NULL,
    cadence_hours   INTEGER NOT NULL DEFAULT 24,
    last_hash       TEXT,
    selector_state  TEXT, -- يحفظ حالة Scrapling Smart Element Tracking
    is_active       INTEGER DEFAULT 1,
    last_checked_at DATETIME,
    next_check_at   DATETIME
);

CREATE TABLE IF NOT EXISTS watch_deltas (
    delta_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id        TEXT NOT NULL,
    diff_summary    TEXT NOT NULL,
    notified        INTEGER DEFAULT 0,
    detected_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(watch_id) REFERENCES watch_targets(watch_id)
);

-- 6. فهرس البحث النصي السريع (FTS5) لإعادة استخدام أبحاثك السابقة بـ 0 توكنز
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    entity_id UNINDEXED,
    entity_type,
    canonical_value,
    metadata_json
);
~~~

---

## 7. البنية التحتية وبروفايلات Docker وميزانية الموارد

### 7.1 ميزانية الموارد (مُحسّنة لتعمل بسلاسة على VPS بـ 2 vCPU / 4GB RAM)

| البروفايل | أمر التشغيل | الحاويات النشطة | استهلاك RAM المتوقع | الاستخدام |
|---|---|---|---|---|
| **الأساسي (`default`)** | `docker compose up -d` | `metamcp` + `omnipulse-core` + `searxng` + `context7/repomix/arxiv` | **~550–700 MB** | تشغيل 24/7 لجميع أبحاث الكود والـ Best Practices والأوراق العلمية والبحث العام. |
| **الويب العميق (`web-crawl`)** | `docker compose --profile web-crawl up -d` | يضيف `crawl4ai` + `scrapling-worker` | **+1.4–1.8 GB** | سحب المواقع الثقيلة وتخطي Cloudflare وتشغيل Watchdog لصفحات الويب. |
| **الاستخبارات (`osint-dark`)** | `docker compose --profile osint-dark up -d` | يضيف `tor-proxy` + `osint-cli-worker` | **+0.8–1.2 GB** | مهام الـ OSINT والدارك ويب فقط (يمكن إطفاؤه فور الانتهاء لتحرير الذاكرة). |

### 7.2 قالب `docker-compose.yml` الإنتاجي

~~~yaml
services:
  # ==================== DEFAULT PROFILE (24/7 Lightweight) ====================
  metamcp-gateway:
    image: ghcr.io/metatool-ai/metamcp:latest
    container_name: omnipulse-gateway
    restart: unless-stopped
    ports:
      - "127.0.0.1:12008:12008" # يُكشف عبر Nginx/Tailscale فقط وليس مباشرة على 0.0.0.0
    environment:
      - LOG_LEVEL=errors-only
    mem_limit: 256m
    networks:
      - intel_net

  omnipulse-core:
    build: ./core
    container_name: omnipulse-core
    restart: unless-stopped
    depends_on:
      - searxng
    env_file:
      - .env
    environment:
      - SEARXNG_URL=http://searxng:8080
      - CRAWL4AI_URL=http://crawl4ai:11235
      - SCRAPLING_URL=http://scrapling-worker:8000
      - TOR_SOCKS_URL=socks5h://tor-proxy:9050
      - SQLITE_PATH=/data/omnipulse.db
    volumes:
      - ./data:/data
      - ./config/limits.yaml:/app/config/limits.yaml:ro
    mem_limit: 384m
    networks:
      - intel_net

  searxng:
    image: docker.io/searxng/searxng:latest
    container_name: omnipulse-searxng
    restart: unless-stopped
    volumes:
      - ./config/searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://searxng:8080/
    mem_limit: 256m
    networks:
      - intel_net

  # ==================== WEB-CRAWL PROFILE (On-Demand) ====================
  crawl4ai:
    image: unclecode/crawl4ai:latest
    container_name: omnipulse-crawl4ai
    profiles: ["web-crawl", "full"]
    restart: unless-stopped
    shm_size: 1g
    mem_limit: 1200m
    networks:
      - intel_net

  scrapling-worker:
    image: pyd4vinci/scrapling:latest
    container_name: omnipulse-scrapling
    profiles: ["web-crawl", "osint-dark", "full"]
    restart: unless-stopped
    command: ["scrapling", "mcp", "--http", "--host", "0.0.0.0", "--port", "8000"]
    mem_limit: 1024m
    networks:
      - intel_net

  # ==================== OSINT-DARK PROFILE (On-Demand) ====================
  tor-proxy:
    image: dperson/torproxy:latest
    container_name: omnipulse-tor
    profiles: ["osint-dark", "full"]
    restart: unless-stopped
    mem_limit: 128m
    networks:
      - intel_net

  osint-cli-worker:
    build: ./workers/osint-cli
    container_name: omnipulse-osint-cli
    profiles: ["osint-dark", "full"]
    restart: unless-stopped
    depends_on:
      - tor-proxy
    environment:
      - TOR_SOCKS_HOST=tor-proxy
      - TOR_SOCKS_PORT=9050
    mem_limit: 1024m
    cpus: "1.0"
    networks:
      - intel_net

networks:
  intel_net:
    driver: bridge
~~~

### 7.3 كود الربط الموحد لأي Agent (Cursor / Antigravity / Roo Code / MULTI-AGENTS-OPS)
~~~json
{
  "mcpServers": {
    "omnipulse": {
      "url": "https://mcp.yourdomain.com/mcp",
      "headers": {
        "Authorization": "Bearer ${OMNIPULSE_API_TOKEN}"
      }
    }
  }
}
~~~

---

## 8. الأمان وضوابط الفشل الآمن (Security & Fail-Closed Guardrails)

1. **منع هجمات SSRF بالكامل (`guard.py`):** لا يُمرّر أي رابط إلى `Crawl4AI` أو `Scrapling` إلا بعد فحص البروتوكول (`http/https` فقط) وحل الـ DNS والتحقق من أن الـ IP عام (Public IP) وليس داخل شبكتك المحلية أو Docker Bridge أو Cloud Metadata (`169.254.169.254`).
2. **عزل شبكة الدارك ويب ومنع تسريب DNS:** كل طلبات `.onion` تمر حصراً عبر `socks5h://tor-proxy:9050` (حرف `h` يضمن حل الـ DNS داخل شبكة Tor وليس من الـ VPS)، مع تفعيل DNS-over-HTTPS في `Scrapling`.
3. **قواطع الدائرة (Circuit Breakers):**
   * `max_depth = 2` و `max_pivots = 15` كسقف افتراضي لمنع الحلقات اللانهائية.
   * `per_adapter_timeout = 18s` (في الوضع `standard`) حتى لا يعطل مصدر بطيء باقي المصادر المتوازية.
   * `max_response_tokens = 3500` لضغط المخرجات تلقائياً قبل إرجاعها للـ Agent.
4. **إغلاق الثغرات السطحية (Zero Exposed Internals):** لا تُفتح أي منافذ لـ `SearXNG` أو `Crawl4AI` أو `Scrapling` أو `Tor` على الإنترنت العام؛ المنفذ الوحيد المرتبط بالـ Host هو `127.0.0.1:12008` ويُدار خلف Nginx/TLS أو شبكة **Tailscale** الخاصة مع `Bearer Token` قوي وملف `.env` بصلاحيات `chmod 600`.

---

## 9. خارطة الطريق التنفيذية (Seed → Trigger → Production)

### Phase 0 — التأسيس والهيكل النظيف (اليوم 1)
* إنشاء ريبو GitHub جديد `omnipulse-mcp` بهيكل الملفات المعتمد وملف `.env.example` و `config/limits.yaml`.
* رفع حاوية `SearXNG` وتفعيل مخرجات JSON في `settings.yml`.
* **بوابة التحقق (Verification Gate 0):** استعلام `curl "http://localhost:8080/search?q=fastmcp&format=json"` يعيد نتائج نظيفة خلال أقل من 2 ثانية.

### Phase 1 — البذرة: النواة + خرطوشة `BUILD` + الذاكرة (الأيام 2–4)
* كتابة `memory.py` (SQLite WAL + FTS5)، `guard.py` (اختبارات SSRF)، و `ledger.py` (إيصال التغطية).
* بناء `server.py` بـ `FastMCP v4` وتعريف `research_mission` و `deep_drill`.
* تفعيل خرطوشة `BUILD` بربط `Context7` (`query-docs`, `query-code`, `get-upgrade-guide`) + `SearXNG` + `Repomix` (Tree-sitter).
* **بوابة التحقق (Verification Gate 1):** ربط السيرفر بـ IDE واحد وطلب بحث عن تأسيس مشروع جديد -> استلام **Zero-Hallucination Tech Brief** خلال أقل من 30 ثانية وبأقل من 3,000 توكن ومعه إيصال تغطية مكتمل.

### Phase 2 — التوسع: خرطوشتا `WEB_MARKET` و `ALGO_PAPERS` (الأيام 5–8)
* تفعيل بروفايل `--profile web-crawl` (`Crawl4AI` + `Scrapling`).
* برمجة منطق التصعيد التلقائي (إذا أعاد `Crawl4AI` كود 403/Challenge ينتقل تلقائياً لـ `Scrapling`).
* ربط `arxiv-mcp-server` داخل `algo_papers.py` لقراءة أقسام LaTeX ومطابقتها بنتائج GitHub من `SearXNG`.
* **بوابة التحقق (Verification Gate 2):** اختبار رابط محمي بـ Cloudflare (يثبت التصعيد التلقائي في الـ Coverage Ledger) + اختبار ورقة arXiv (يعيد الخلاصة الخوارزمية وكودها المرجعي بدون تحميل PDF كامل).

### Phase 3 — المحفز (Trigger): الرادار ذاتي الإصلاح والمهام الخلفية (الأيام 9–12)
* تفعيل `task=True` (Async Job IDs) و `notifications/progress` للوضع `depth="deep"`.
* بناء `watchdog.py` فوق `APScheduler` وربطه بـ `watch_pulse` و Telegram Bot API.
* تفعيل حفظ بصمات العناصر (`Scrapling Smart Element Tracking`) ومقارنة الـ `content_hash` لإرسال الدلتا فقط.
* **بوابة التحقق (Verification Gate 3):** مراقبة صفحة متغيرة + موضوع arXiv لمدة 24 ساعة -> صفر False Positives ووصول تنبيه Telegram منسق عند أول تغيير فعلي فقط.

### Phase 4 — البروفايل المتخصص: خرطوشة `OSINT_DARK` ونقل المكونات (الأيام 13–16)
* بناء بروفايل `--profile osint-dark` (`Tor SOCKS5` + `badchars` adapters + حاوية `osint-cli`).
* نقل الـ Adapters المجربة فقط من مستودعك القديم `intiligence-mcp` (أدوات الـ Captcha/Dark Web الخاصة بك) إلى `workers/osint-cli`.
* تطبيق قواعد القفز الحتمي المحدود (`Domain -> Email/Handle -> Leak/Darknet -> Crypto ChainAbuse`).
* **بوابة التحقق (Verification Gate 4):** فحص هدف اختباري عام -> بناء Entity Graph مترابط في SQLite، مع التأكد من ظهور `SKIPPED_PROFILE_OFF` بوضوح عند إطفاء البروفايل.

### Phase 5 — الإطلاق الإنتاجي والربط الشامل (الأيام 17–21)
* وضع `MetaMCP Gateway` في الواجهة مع عزل الـ Namespaces والـ Rate Limiting، وربط Nginx/TLS أو Tailscale.
* ربط منظومة **`MULTI-AGENTS-OPS`** بـ `omnipulse-mcp` عبر الـ Endpoint الموحد.
* تفعيل سكربت `backup_sqlite.sh` اليومي وفحص `healthcheck.py` التلقائي.
* **بوابة التحقق النهائية (Production Readiness Gate):** تشغيل الاختبارات الآلية (`pytest tests/`) بنسبة نجاح 100%، واستهلاك RAM مستقر أقل من 750MB في الوضع الدائم على مدار 72 ساعة تشغيل متواصل.

---

## 10. مؤشرات الأداء وتجارب التحقق (KPIs & Benchmarks)

| المؤشر (KPI) | القيمة المستهدفة | طريقة القياس |
|---|---|---|
| **توفير التوكنز (Tool Definitions)** | **أكبر من 92%** (أقل من 1,500 توكن مقابل ~40,000) | مقارنة حجم `tools/list` JSON قبل وبعد الـ 3-Tool Facade. |
| **زمن الاستجابة (Standard Mode)** | **أقل من 35 ثانية** (و أقل من 1 ثانية للـ Cache Hit) | قياس `latency_ms` المسجل في `coverage_receipts`. |
| **معدل الفشل الصامت (Silent Failures)** | **0%** | كل خطأ/Timeout/حظر يظهر صراحة في `coverage_receipt`. |
| **دقة حماية SSRF** | **100% حظر** لكل IPs الداخلية | اجتياز `tests/test_guard_ssrf.py` (15 متجه هجوم). |
| **ثبات استهلاك الذاكرة (Default 24/7)** | **أقل من 750MB RAM** | مراقبة `docker stats` لمدة 72 ساعة. |