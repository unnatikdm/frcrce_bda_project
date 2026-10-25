# InfluenceMatch (local, INR 0)

A locally runnable Instagram creator recommendation project. **No profiles, posts, engagement figures, or campaign outcomes are fabricated.** An optional integration uses an openly licensed historical research dataset; it has no bios and no disclosed exact observation dates.

See [MASTER_PROMPT.md](./MASTER_PROMPT.md) for the project's goal and non-negotiable data-integrity requirements.

## Hardware and setup

Inspected environment: Windows 11 x64, 16 logical CPUs, 15.4 GB RAM, 82 GB free on C:, Python 3.13 and 3.14 installed, Java 25, Docker Compose 5.1.2. Docker Desktop was installed and its Linux engine was subsequently started for PostgreSQL verification. Use Python 3.13, Spark local mode `local[2]`, and the included PostgreSQL container capped at 1 GB. Spark uses a 2 GB driver. PySpark 4.2 ran on this machine with Java 25 and Python 3.13. If your Java version differs, use Spark-supported Java 17, 21, or 25; set `JAVA_HOME` only if it is not already configured. [Spark platform requirements](https://spark.apache.org/docs/latest/).

Docker Desktop currently lists education as a free use category; the license describes educational use for academic or research purposes in a classroom environment. Check the terms for your own circumstances. [Docker Desktop terms](https://docs.docker.com/subscription-billing/desktop-license/). PostgreSQL is under the PostgreSQL License. No paid API, cloud service, subscription, or API key is required. [PostgreSQL license](https://www.postgresql.org/about/licence/).

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[test,bigdata,repod]"
# This machine uses Java 25. Set JAVA_HOME only if Java is not already configured.
# $env:JAVA_HOME = "<path to OpenJDK 17, 21, or 25>"
# $env:Path = "$env:JAVA_HOME\bin;$env:Path"
# Start Docker Desktop first, then:
docker compose up -d --wait postgres
```

PySpark's current source archive is large (about 450 MB when checked). It is an optional `bigdata` extra; the educational Reels adapter also needs the optional `datasets` extra; omit both to run the API and data-import validation first. `docker compose up -d --wait postgres` is optional for the local API and Parquet flow.

## Data policy and current status

Only authentic source data may enter the pipeline. The optional RepOD adapter downloads one openly licensed research file with checksum verification; the project does not scrape Instagram or call platform APIs. Public visibility alone is not permission to reuse personal data. Before importing, verify provenance, terms, attribution, privacy requirements, and your permitted purpose. The import manifest records the operator-declared source and license but **does not independently verify authenticity or legal rights**. A dataset that cannot be verified should not be imported.

### Data-source screening (checked 2026-10-18)

| Candidate | What its source documents | Decision |
|---|---|---|
| [Judge-rated dataset of nano- and micro-influencers](https://repod.icm.edu.pl/dataset.xhtml?persistentId=doi%3A10.18150%2FKUW9CA) | RepOD records CC BY 4.0, 398 Instagram profiles assessed by two judges during a three-month period; ODS contains 393 observations, niche labels, follower counts, study ratings; one observation lacks a creator identifier, so 392 usable records are imported. No bios or exact observation dates. | Accepted as historical research benchmark only. Published ODS MD5 verified; TSV checksum mismatch means TSV is not used. |
| [Educational Instagram Reels: Coded Dataset of 300 Reels from 21 Accounts](https://doi.org/10.5281/zenodo.23301344) | Zenodo record is open CC BY 4.0; author reports 300 Reels from 21 public accounts, published 2026-02-04 through 2026-10-01 and coded 2026-09-02 through 2026-10-01. Workbook includes author, follower labels, topics, views, comments, Reel URLs, and single-researcher content ratings. No likes. | Accepted as a narrow educational-content dataset. Workbook checksum is verified; follower/view/comment labels are partly abbreviated. The source is not a general creator directory, and metrics are one-time historical observations. |
| [Kim et al. Instagram Influencer Dataset](https://sites.google.com/site/sbkimcv/dataset/instagram-influencer-dataset) | Researcher page describes 33,935 creators and 10,180,500 posts; metadata is about 37 GB and images about 189 GB. Files require a research-purpose request; no reuse license or commercial terms are stated on the page. | Not imported pending direct permission/license clarification. Full media also exceeds this machine’s current 82 GB free disk. |
| [Cheerful Instagram engagement benchmarks](https://www.cheerful.ai/research/instagram-engagement-benchmarks) | CC BY 4.0 aggregate quartiles for 5,924 Instagram accounts with at least 1,000 followers; measured 2026-08-17 to 2026-09-06, with sample counts and engagement-rate definition. | Accepted as a dated reference benchmark only, not creator-level recommendation data. Imported rates can be compared against follower-tier quartiles; the benchmark does not change ranking. |
| [Social Media influencers-Content Analysis](https://data.mendeley.com/datasets/5b4vpr4752/1) | CC BY 4.0 annotation spreadsheet for content from Snapchat and Instagram accounts of 23 Arab-world influencers; source says 7,400+ annotated items, while the original media are not included. | Screened but not integrated: the small, region-specific annotated sample is not a broad creator inventory and does not document campaign outcomes or current performance. File schema and identity linkage would need review before using it for recommendations. |
| [Luvs Creator Price Index](https://luvs.one/research) | CC BY 4.0 monthly aggregate prices for subscription pages on a curated creator catalogue; aggregates are explicitly not per-creator data or sponsorship fees. | Not used for Instagram campaign budget filtering; subscription prices are not campaign quotes. |
| [Sponsored and Unsponsored Posts on Instagram](https://zenodo.org/records/5082114) | Zenodo lists 29,425 sponsored and 28,779 unsponsored posts collected 2020-04-15 to 2020-05-15, with user IDs, follower counts, likes, comments; license field is blank. | Rejected pending explicit reuse terms; no creator niche, caption, or location fields are listed. |
| [Social Media Influencers Dataset](https://figshare.com/articles/dataset/_strong_Social_Media_Influencers_Dataset_strong_/23576037) | CC BY 4.0, 5 KB SPSS file described as consumer-behavior study data for beauty products in the US. | Rejected as a creator inventory; it is consumer study data, not influencer profile/post records. |
| [Instagram Posts from Academic Libraries Profiles](https://zenodo.org/records/11102526) | Zenodo describes captions, dates and interaction rates from 120 library accounts, but its public record leaves the license field blank; the accounts are institutional library profiles, not a general influencer directory. | Rejected for this project: no reuse license verified. |
| [Abertay Instagram influencer engagement data](https://rke.abertay.ac.uk/en/datasets/data-for-exploring-customer-engagement-with-instagram-influencers/) | CC BY; data produced 2022-11-05 to 2022-12-05; study files are consumer research/questionnaire material | Not a creator/profile inventory, so it cannot provide eligible influencer recommendations |
| [InSTA 150k](https://huggingface.co/datasets/data-for-agents/insta-150k-v3) | Dataset card identifies web-navigation instruction tasks, despite `insta` in its name | Not Instagram platform data |
| [Oliveira Instagram sponsored-content thesis](https://repositorio.ufmg.br/bitstreams/4185433e-5b95-483a-859a-01df3e2e5896/download) | Describes an Instagram web crawler for collecting public timelines; a permission chain and reusable dataset license were not established | Rejected: scraping is excluded by project policy and no reuse terms were verified |
| [CrowdTangle-based influencer study](https://github.com/thalesbertaglia/instagram-disclosure-trends) | Research repo documents a CrowdTangle token collection pipeline; Meta ended CrowdTangle availability on 2024-08-14 | Not a reproducible current acquisition path ([Meta notice](https://about.fb.com/news/2023/11/new-tools-to-support-independent-research/)) |
| [Dexfluence mirror](https://huggingface.co/datasets/Shikha180224/dexfluence-indian-creator-index) | Claims CC BY 4.0, but the card's described origin and publication instructions do not establish an independently traceable collection or rights chain | Not accepted or downloaded |
| [Instagram Influencer and Brand Dataset](https://huggingface.co/datasets/AzrilFahmiardi/instagram_influencer_and_brand/tree/ab0e29bb9464481e83f62b54199c2c868269609e) | Repository revision `ab0e29bb9464481e83f62b54199c2c868269609e` (updated 2025-07-10): card metadata declares MIT, while README restricts use to research/non-commercial and gives no collection method/date or verification of profile/rate fields. | Rejected pending license clarification and authentic-source provenance; not imported. |

RepOD and the Zenodo educational Reels file are the accepted creator sources; each is narrow. Cheerful contributes only an aggregate engagement reference, not creator recommendations. Its repository license is verified; the software cannot certify every legal interpretation or profile accuracy. An official Meta API connector is also not implemented: Meta's official API collection describes access for professional accounts and linked Page setup, and the existing workspace has no authorized token or reviewed app. The Instagram API with Facebook Login cannot access consumer accounts. [Meta Instagram API documentation](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api).

The RepOD adapter accepts only its ODS artifact after verifying the published MD5. It imports creator identifier, follower count, four study niche labels (fitness, beauty, lifestyle, travel), available judge ratings, and source metrics for AQS, average likes/comments per post, engagement rate, compensation, and post count. Missing and formula-error cells are counted in the manifest without fabricated replacements. Source engagement-rate units and compensation currency are unspecified, so those values are retained verbatim as source metrics but are not normalized, filtered, or matched to campaign budgets. The adapter does not infer bios, countries, language, profile URLs, or observation dates. A brief containing a supported niche ranks overlapping profiles using the mean of observed items in the study’s six-item judge-rated opinion-leadership construct. Each result includes the score, matched niche, observed rating-item count, observed source item values, numerator, denominator, and calculation; profiles with no score are excluded rather than assigned zero. This historical research measure is not campaign success or a current platform metric. Other properly sourced CSV/JSONL data can use general TF-IDF bio/topic matching. Creator-country, language, follower, and engagement-rate eligibility filters apply only to values present in the source. Engagement and follower filters do not contribute to ranking scores; creator country does not represent audience geography. A conditional budget-filter path is available only when a permitted imported record has an exact per-deliverable `rate_amount`, `rate_currency`, and `rate_deliverable`; it requires the campaign currency and deliverable to match exactly and applies no exchange-rate conversion. No accepted source currently supplies real per-creator quotes, so a successful budget-filtered recommendation has not been demonstrated. Missing rates are excluded when a budget cap is used. RepOD has no usable per-creator quote, so budget filtering is unavailable for it. Audience composition and campaign outcomes are not supported.

Use the optional RepOD research dataset with this checksum-verifying adapter (no key required):

```powershell
pip install -e ".[test,repod]"
python -m influencematch.repod_import
```

It reads the verified local ODS cache if present; otherwise it downloads from RepOD over HTTPS. It refuses any content whose MD5 differs from repository metadata. Cite Korzyński and Protsiuk (2026), *Judge-rated dataset of nano- and micro-influencers*, RepOD, DOI [10.18150/KUW9CA](https://doi.org/10.18150/KUW9CA), CC BY 4.0. The dataset release date is not represented as collection date. Data are saved under git-ignored `data/active`.

Use the second openly licensed source when you want the educational Reels sample active (this replaces the one active dataset; it does not merge independent sources):

```powershell
pip install -e ".[datasets,bigdata,test]"
python -m influencematch.tvorog_import
python -m influencematch.pipeline --master "local[2]"
python -m influencematch.db
```

The adapter verifies the Zenodo workbook MD5, records the source date window, and aggregates 300 observed Reels into 21 account profiles. It retains each Reel in `reels.jsonl`, writes creator and Reel Parquet tables, and loads both tables into PostgreSQL. Matching uses only source-coded Reel topic labels. Views, comments, and one-researcher quality ratings are descriptive evidence, not ranking inputs or campaign outcomes. No likes are supplied, so the project does not calculate an engagement rate. Source follower, view, and comment labels may be abbreviated; their converted values are marked approximate. Attribute Grigorii Tvorogov (2026), *Educational Instagram Reels: Coded Dataset of 300 Reels from 21 Accounts*, Zenodo, DOI [10.5281/zenodo.23301344](https://doi.org/10.5281/zenodo.23301344), CC BY 4.0.

For other source files, import only after confirming that their license and terms permit this use. Optional input fields include `engagement_rate` as a fraction from 0 to 1, and a complete creator quote triple: `rate_amount`, `rate_currency` (three-letter code), and `rate_deliverable` (for example, the source’s exact deliverable label). Partial quote triples and invalid numeric rates are rejected. Budget filtering compares the campaign cap against `rate_amount × deliverable_count` in the same currency and deliverable; it never guesses missing rates or converts currency. Supply its recorded collection/snapshot date, URL, and license identifier. The explicit rights flag is an operator attestation, not a software verification or legal determination:

```powershell
python -m influencematch.import_data C:\path\to\permitted-creators.csv `
  --destination data/active `
  --source-name "Source title" `
  --source-url "https://source.example/dataset" `
  --license "CC-BY-4.0" `
  --source-date 2025-01-31 `
  --rights-confirmed
```

Imported files and the source data are local and git-ignored. The manifest records source name/URL/license, collection date, retrieval time, file hashes, record count, and an explicit `not independently verified` status. Do not use the sample values in the command as actual source metadata.

## Run

After selecting a brief and finding matches, use **Download ranked results and score traces (JSON)** to save the displayed recommendation records. The export includes the query, source attribution and license, source hashes, limitations, the original ranking evidence, and engagement-reference status. It is generated locally and contains only the imported records already used by the matcher.

```powershell
# Without imported data, these endpoints report unavailable; no fallback data is shown.
uvicorn influencematch.api:app --reload
streamlit run src/influencematch/dashboard.py --server.address 127.0.0.1
```

API docs: `http://127.0.0.1:8000/docs`; dashboard: `http://localhost:8501`. After importing, the verified Spark pipeline writes creator Parquet files and, when the source supplies post records, a post-level Reel Parquet table; it also copies the provenance manifest. By default the lake is stored outside OneDrive in `%LOCALAPPDATA%\InfluenceMatch\data-lake` on Windows. Spark overwrite failed inside this workspace’s OneDrive folder, so set `--lake` to a normal local-disk path if needed:

```powershell
python -m influencematch.pipeline --master "local[2]"
python -m influencematch.db
```

PostgreSQL needs the Compose service running. The container maps to host port 55432 because a separate local PostgreSQL process owns port 5432. File-backed API/dashboard mode is the default and works on low-resource setups. To serve recommendations from the PostgreSQL snapshot instead, load the selected source and run:

```powershell
python -m influencematch.db
$env:INFLUENCEMATCH_DATA_BACKEND = "postgres"
$env:DATABASE_URL = "postgresql://influence:influence@localhost:55432/influence"
# Terminal A:
uvicorn influencematch.api:app --reload
# Terminal B: set both environment variables above in this terminal too, then run:
streamlit run src/influencematch/dashboard.py --server.address 127.0.0.1
```

The loader stores each full imported source record and its provenance manifest in PostgreSQL in a single transaction. PostgreSQL-backed API reads verify the source row counts and a canonical digest before making recommendations. `/match` responses carry source collection/retrieval metadata and imported creator/Reel file hashes; PostgreSQL results also carry the canonical database snapshot SHA-256. With PostgreSQL mode selected, `GET http://127.0.0.1:8000/analytics/summary` runs descriptive SQL for follower distributions, niche counts, source-metric coverage, and post topics/views/comments when Reel rows exist. The response includes the data source and marks approximate Reel metrics. The dashboard exposes the same SQL-backed summary in a collapsed panel when PostgreSQL mode is enabled; it compares the verified snapshot SHA-256 returned with recommendations to the summary query digest before displaying it. Summary queries are unavailable in file mode rather than returning simulated or stale statistics. Integration tests exercise actual RepOD or educational Reel rows, whichever source is selected in `data/active`.

## Implemented and not implemented

| Feature | State |
|---|---|
| Rights-attested CSV/JSONL importer with manifest and hashes | Implemented; source truth and permissions remain operator-declared |
| API and UI unavailable-data state | Implemented; verified in tests |
| TF-IDF/cosine ranking and present-field filters | Implemented for permitted bio/topic inputs; quality is unevaluated |
| Recommendation score explanations | Implemented; TF-IDF results include per-term cosine contributions whose sum is checked against the score; RepOD includes observed judge-rating items, numerator, denominator, and mean, and excludes profiles without a score |
| Download ranked results and score traces | Implemented; dashboard exports JSON with the actual query, dataset attribution/license and hashes, limitations, ranking evidence, and engagement reference; tested on both imported source datasets |
| Zenodo educational Reels workbook importer with checksum-verified 300-post records | Implemented; actual 21-account, 300-Reel dataset, limited to education, no live metrics or likes |
| RepOD checksum-verified ODS integration and niche match | Implemented; historical research benchmark with explicit limits |
| Per-creator budget eligibility | Conditional importer/matcher path exists for complete source quotes, but no accepted real dataset supplies them; current datasets reject budget requests and success is not demonstrated with authentic quote data |
| Engagement reference comparison | Implemented using the published CC BY quartiles in `data/reference/cheerful_engagement_benchmarks.json`; only compares source-provided normalized rates and follower counts, never imputes missing data or changes ranking |
| PySpark creator and post-level Reel Parquet pipeline | Implemented; verifies provenance hashes, row counts, nonempty/unique IDs, and Reel-to-creator references before writing; verified on the 300 source Reel rows and 21 aggregated accounts, alongside the RepOD creator flow |
| PostgreSQL creator and Reel loader plus API/dashboard backend | Implemented; replaces the prior active snapshot transactionally, checks source row counts and snapshot digest, and serves recommendations from actual database records |
| PostgreSQL SQL analytics summary endpoint and dashboard panel | Implemented for loaded, provenance-verified snapshots; source-specific counts and distributions only, with approximate Reel metrics marked and no imputed values |
| Post-level source ingestion and campaign outcomes | Implemented for the 300 licensed historical educational Reels only; no general/live Instagram ingestion or campaign-outcome data |
| Evaluation and performance | RepOD descriptive rating association, same-sample NDCG@10, deterministic five-fold candidate-ranking stability diagnostic, Zenodo leave-one-Reel-out topic retrieval proxy, and repeatable local Spark timing are implemented; none is campaign-outcome validation |
| Kafka, Airflow, MLflow, graph analytics | Optional/not implemented |
| Meta/Instagram API integration | Not implemented; no credentials, reviewed app, scraping, or access-control bypass |

## Tests and reproducibility

```powershell
python -m pytest
# Optional PostgreSQL integration test, after Compose reports the service healthy:
$env:DATABASE_URL = "postgresql://influence:influence@localhost:55432/influence"
python -m pytest tests/test_db.py -q
```

Tests cover API/dashboard unavailable behavior, provenance rejection, generic importer refusal without rights attestation, ETL refusal without provenance, RepOD checksum/schema import, Zenodo workbook checksum/schema and account aggregation, real API/dashboard matching on both licensed sources, budget-unavailable rejection on real datasets, multi-item source-rating evaluation, NDCG@10 same-sample ranking proxy, licensed engagement benchmark thresholds, Spark creator/Reel Parquet writes with integrity checks, and PostgreSQL creator/Reel loading, SQL summaries, plus database-backed recommendations on real source rows. The executed 321-row Zenodo Spark benchmark is in [zenodo_educational_reels_spark_benchmark.json](reports/zenodo_educational_reels_spark_benchmark.json). The optional PostgreSQL integration test is skipped unless `DATABASE_URL` is set; it checks loaded creator/Reel row counts, source null values, SQL summaries, and real recommendations from the configured database snapshot through both the API and Streamlit dashboard. Engagement context uses the source-published 2026 observation window, account counts, quartiles, definition, and CC BY 4.0 license; it is not treated as a predictive outcome or ranking feature. No fabricated influencer records are used. The Streamlit dashboard rendered and returned recommendations from the imported source in AppTest; it was also launched bound to `127.0.0.1`, where its health endpoint returned `ok` and its page returned HTTP 200. The importer stores source hashes and a provenance manifest; file-backed API state validates every declared creator and Reel artifact hash and row count, and Spark also validates source hashes and its ETL integrity checks before Parquet writes. Run `python -m influencematch.evaluate --data data/active --report reports/repod_evaluation.json` to reproduce the RepOD study-proxy analysis. For the educational Reel source, run `python -m influencematch.evaluate_tvorog --data data/active --report reports/zenodo_educational_reels_evaluation.json`. The verified report evaluates 300 held-out Reel topics against the same accounts remaining in the candidate set: TF-IDF retrieves the Reel author at Recall@5 0.867 and MRR 0.586, compared with follower-count baseline Recall@5 0.233 and MRR 0.175. This tests retrieval of one researcher's topic labels, not creator generalization or campaign effectiveness. Run `python -m influencematch.benchmark --repeat 2 --report reports/repod_spark_benchmark.json` to time Spark ETL on RepOD, or add `--raw data/active` after selecting the Zenodo dataset. On the current 392 records, Spearman rho between the six-item opinion-leadership composite and the two-item intention-to-recommend composite is 0.709 overall. Ranking quality is also reported as NDCG@10 against study intention-to-recommend ratings and compared with a follower-count baseline. The five-fold candidate-set diagnostic over the 257 profiles with all required ratings and follower counts produced mean NDCG@10 0.907 (population SD 0.113) for the opinion-leadership ranking and 0.380 (SD 0.078) for follower count. Folds are evaluation subsets only: no model is fitted, and both ranking signal and target are ratings from the same study. These are descriptive ranking-stability proxies, not independent validation, campaign prediction, or evidence of causality. Per-niche RepOD metrics and the exact input hash are in [repod_evaluation.json](reports/repod_evaluation.json); the educational Reel retrieval metrics are in [zenodo_educational_reels_evaluation.json](reports/zenodo_educational_reels_evaluation.json). No campaign outcomes are available.

## Costs and limits

Software licenses used are permissive/open-source according to their upstream package metadata (FastAPI MIT, Streamlit Apache-2.0, scikit-learn BSD-3-Clause, PySpark Apache-2.0). Review transitive dependency licenses before redistribution. Software and local execution require no paid tier; network access is needed to install packages and pull container images. RepOD provides real historical records for local use. Spark-to-Parquet and PostgreSQL loading both ran against the imported source; campaign outcomes remain unavailable; model ranking quality has only a same-sample research-proxy analysis and must not be treated as campaign validation. The 392-row Spark timing report is explicitly a small local smoke benchmark, not large-cluster throughput: the latest recorded runs were 31.02 and 2.33 seconds, with 16.68 seconds median including Spark startup. The 321-row educational Reels run took 31.08 and 3.87 seconds, with 17.48 seconds median including startup. Both are local smoke timings and vary between runs. These datasets are too small to establish big-data-scale throughput; Spark demonstrates an authentic local ETL path, while larger-scale performance remains unverified.
