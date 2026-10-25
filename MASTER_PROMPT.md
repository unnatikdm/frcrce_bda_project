# InfluenceMatch — Master Project Goal and Instructions

## Project goal

Design and develop a completely free, locally runnable, Big Data-driven Instagram influencer recommendation system. It should help businesses identify, evaluate, and rank creators for marketing campaigns using real, legally accessible data.

The intended system uses open-source technologies and, where justified by the actual workload and available data, Apache Spark, distributed processing, data lakes, batch or streaming pipelines, SQL analytics, natural language processing, machine learning, and recommendation algorithms. Recommendations should be explainable and based only on campaign requirements and creator attributes that are genuinely available in the selected data, such as campaign objective, industry, geography, language, budget, engagement quality, and content relevance.

The project should demonstrate reproducible data processing, reliable pipelines, meaningful evaluation, measured performance, and a practical user interface. This is a target, not a claim that every component is currently implemented. Clearly identify implemented, partial, and unimplemented features.

## Non-negotiable data integrity rules

1. **Never present synthetic records as real Instagram data.** Do not fabricate influencer profiles, Instagram posts, follower counts, engagement metrics, campaign outcomes, or datasets.
2. **Do not disguise incomplete features.** No hardcoded recommendation results, placeholder statistics, invented API responses, simulated creators, or mock services in user-facing functionality.
3. **Use only verifiable, permitted data.** Data must come from appropriately licensed datasets, authorized providers, or official APIs used within their permissions. Record the source, license or terms, collection/observation date when known, and relevant limitations.
4. **Treat declared provenance honestly.** A manifest or checksum can document and verify a file's identity and declared source; it does not, by itself, prove authenticity, ownership, or legal reuse rights. Do not claim independent verification unless it was performed.
5. **Compute all displayed results from actual inputs.** Recommendation scores, engagement calculations, evaluations, benchmarks, and dashboard statistics must be produced by executed computations over the stated data. Never invent results to make a demo appear complete.
6. **Label test data.** Small fixtures are allowed for automated tests only when clearly identified as test fixtures and never exposed or described as real-world data, live Instagram data, or project evaluation evidence.
7. **Fail transparently when data is unavailable.** Explain the limitation and stop the affected workflow. Do not silently substitute synthetic data, invented values, stale data as current data, or mocked API responses.
8. **Respect platform terms, privacy, and law.** Do not bypass authentication, access controls, rate limits, or private-account restrictions. Public visibility alone does not establish permission to collect or reuse personal data.
9. **Keep the project free and open-source.** Do not make paid APIs, commercial datasets, subscriptions, cloud services, or cloud credits mandatory. Document any optional service and its cost or access conditions.
10. **Report limitations precisely.** Separate observed facts, estimates computed from observations, unavailable fields, and unimplemented features. Never claim that a method ran unless it was executed and verified.

## Current data context

Read the current data-source documentation and manifests before changing ingestion, matching, evaluation, benchmarks, or dashboard behavior. The checked-in project documentation describes a historical RepOD research dataset, a narrowly scoped educational Reels dataset, and aggregate engagement reference benchmarks. These sources are not interchangeable and must not be described as a live, comprehensive Instagram creator catalog or as campaign-outcome data. Preserve each source's own scope, attribution, license, observation period, missing fields, and measurement limitations.

Do not assume source files or prior benchmark outputs are valid evidence simply because they exist in the workspace. Verify their manifests, provenance, record counts, and execution path before relying on them or updating reported results. Do not replace, merge, or relabel distinct datasets without documenting and validating the change.

## Engineering and reporting instructions

- Inspect the existing implementation and reuse its established ingestion, provenance, validation, and reporting patterns.
- Keep changes end-to-end: wire any new data or feature through validation, processing, API/UI surfaces, documentation, and relevant tests.
- Make ranking explanations traceable to observed fields and explicit formulas. Exclude or clearly mark records when required information is missing; do not silently impute values.
- Measure Big Data performance using repeatable commands against identified real input data. Report the dataset, machine/runtime configuration, command, timing method, and limitations; distinguish local smoke timings from production-scale claims.
- Profile before optimizing. Improve end-to-end runtime without removing or weakening provenance, checksum, schema, row-count, uniqueness, or relationship checks. Re-run the same benchmark on the same authentic inputs and report the comparison method and results.
- Describe scale accurately. Do not call a small dataset or local-mode smoke run evidence of big-data-scale performance. If no sufficiently large, legally usable real dataset is available, state that limitation and report measured scalability as unverified; never enlarge a dataset with synthetic records to claim scale.
- Evaluate against valid observed labels or outcomes available in the source. If no suitable ground truth exists, state that evaluation is descriptive or unavailable rather than implying recommendation effectiveness.
- Add tests for behavior and data-integrity guarantees. Keep fixture-only assertions distinct from real-data evaluations and performance results.
- Update user-facing documentation when behavior, data availability, setup, or limitations change. Provide reproducible setup, import, validation, evaluation, and benchmark commands where supported.
- Prefer local, free, open-source infrastructure and make optional components explicit. Do not add dependencies, cloud integrations, or collection methods without a demonstrated need and documented permission.

## Definition of success

The long-term goal is for a business to submit a campaign brief and receive a ranked list of eligible creators based on authentic, available data, with traceable score calculations, understandable explanations, documented limitations, and independently reproducible evaluation.

Only claim this outcome for a specific workflow when the real data actually contains the required information and the end-to-end workflow has been run and verified. If the available lawful data is insufficient, report that limitation clearly rather than manufacturing records or results to complete a demonstration.
