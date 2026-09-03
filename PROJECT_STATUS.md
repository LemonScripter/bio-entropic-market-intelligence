# Amazon Market Intelligence & Bio-Entropic Stealth Scraper — Projekt Státusz

**Dátum:** 2026-09-03  
**Verzió:** v1.0-STABLE (Production Ready)  
**Munkakönyvtár:** `C:\Users\lszok\Documents\_amazon`

---

## 1. Elért Mérföldkövek & Funkciók

### A. Bio-Entrópikus Lopakodó Motor (Bio-Entropy Stealth Layer)
- **Biológiai Telemetria:** 168 órás valós emlős aktigráfia adathalmaz (`actigraphy_168h.csv`), amely természetes cirkadián és ultradián görbékkel vezérli a lekérések gyakoriságát és a késleltetéseket (Poisson-eloszlású dwell-time).
- **Keményített Böngészőmotor:** Playwright Chromium headless környezet automatikus navigációs, WebGL/Canvas ujjlenyomat-védelemmel és CDP szivárgás-gátlással.
- **Viselkedési Állapotgép (FSM):** `IDLE` $\rightarrow$ `EXPLORING` $\rightarrow$ `SEARCHING` $\rightarrow$ `READING` $\rightarrow$ `ENTROPY_REST` állapotátmenetek emberi mikromozgásokkal és véletlenszerű görgetésekkel.

### B. Hitelesített Munkamenet-Kezelés (Session Persistence)
- **Bejelentkezési Modul (`login_helper.py`):** Létrehozva egy egyszeri, interaktív bejelentkező felület, amely a felhasználó hitelesített Amazon munkamenetét (cookie-k, `at-main`, `sess-at-main`, `session-token`, `ubid-main`) exportálja.
- **Perzisztens Állapot:** `data/sessions/session_state.json` — A headless motor minden indításkor automatikusan visszatölti, így a scraper hitelesített felhasználóként fut és elkerüli a bejelentkezési falakat (`/ap/signin`).

### C. Mély, Korlátlan Vélemény-Kinyerés (Infinite Review Harvester)
- **13-as Előnézeti Korlát Áttörése:** Feltörtük az Amazon dinamikus AJAX lapozó mechanizmusát (`#cm_cr-pagination_bar`, `Show 10 more reviews` gomb és a `customer_review-*` kártyák).
- **Empirikus Validáció:** Könyvenként tetszőleges számú vélemény (10, 50, 100, 500+) kinyerhető egymás után.
- **Kinyert Adatok:** Teljes, vágatlan szövegek (akár 17,585 karakter), 100%-os *Verified Purchase* arány, értékelő neve, csillagértékelés (1.0–5.0), pontos dátum és cím.

---

## 2. Adatbázis & Export Állapot

### Központi SQLite Adatbázis (`data/market_data.db`)
- **`products` tábla:** 10 legnépszerűbb bestseller könyv metaadatai (ASIN, valódi szerzők mint James Clear, Kristin Hannah, Bessel van der Kolk, Morgan Housel, Andy Weir; értékelések száma 8,000–420,000+, live árak).
- **`reviews` tábla:** **797 darab** teljes szövegű, strukturált vásárlói vélemény indexelve.
- **`price_history` tábla:** Ár- és elérhetőségi idősorok.

### Generált Master Exportok (`data/exports/`)
1. `empirical_proof_2_books.csv` (191 KB) — 200 mély vélemény az *Atomic Habits* és *The Nightingale* könyvekről (15 batch lapozási bizonyíték).
2. `reviews_intelligence_20260903_153348.csv` (1.04 MB) — A 10 bestseller könyv 797 db teljes véleményének aggregált mesterfájlja.
3. `market_intelligence_20260903_153348.csv` & `.json` (51 KB) — Teljes könyvpiaci termékriport.

**Teljes lemezhasználat:** Mindössze **3.19 MB**.

---

## 3. Kulcsfájlok és Használatuk

| Fájl | Leírás & Cél | Futtatás |
| :--- | :--- | :--- |
| `src/bio_engine.py` | Biológiai entrópia és cirkadián ritmus motor | Belső modul |
| `src/stealth_layer.py` | Playwright lopakodó réteg session-kezeléssel | Belső modul |
| `src/data_pipeline.py` | SQLite adatbázis és HTML elemző pipeline | Belső modul |
| `login_helper.py` | Interaktív bejelentkező Amazon session frissítéshez | `python login_helper.py` |
| `harvest_massive_reviews.py` | Teljes automatikus 10 könyves mély véleménygyűjtő | `python harvest_massive_reviews.py` |
| `prove_infinite_harvest.py` | 2 könyves célzott mélységi lapozási teszt/bizonyítás | `python prove_infinite_harvest.py` |
| `harvest_all_book_details.py` | Termék metaadat, ár és autor kinyerő | `python harvest_all_book_details.py` |

---

## 4. Folytatási Irányok (Következő Lépések)

1. **Új Termékkategóriák Pásztázása:** Elektronika, IT hardver, egészségügy vagy tetszőleges Amazon kategória bemeneti ASIN listájának automatikus pásztázása.
2. **Természetes Nyelvfeldolgozás (NLP) & Sentiment Analízis:** A begyűjtött ~800 vélemény szövegelemzése (pozitív/negatív kulcsszavak, vásárlói elégedettségi metrikák, termékhibák detektálása).
3. **Ütemezett Háttérfigyelés (Cron / Scheduler):** Ár- és készletváltozás figyelő riasztó modul integrálása.
