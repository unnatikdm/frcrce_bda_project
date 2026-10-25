# Datasets, Authenticity & Provenance

> Why InfluenceMatch uses 100% authentic, openly licensed research data and never generates fake influencer profiles.

---

## 1. The Core Data Philosophy: Zero Synthetic Data

Most online student or demo projects use scripts like `Faker` or random number generators to fabricate fake influencer profiles (such as making up usernames like `@travel_jane_99` with `50,000` followers). 

In InfluenceMatch, this is strictly forbidden. 

### Why No Fake Data?
1. **Academic Honesty**: Fake data does not reflect real-world social media dynamics (such as skewed follower power laws, missing values, and real audience engagement distributions).
2. **Predictable & Verifiable Evaluation**: When an algorithm is evaluated on fake data, the results mean nothing. When evaluated on real, peer-reviewed study data, the evaluation is scientifically meaningful.
3. **Transparent Limitations**: If a real dataset does not have creator country or pricing quotes, the software honestly reports: *"This information is unavailable in the dataset"* rather than inventing made-up prices.

---

## 2. The Three Real Datasets Used in This Project

InfluenceMatch integrates three authentic datasets, all published under open **Creative Commons Attribution 4.0 (CC-BY-4.0)** licenses:

### Dataset 1: RepOD Judge-Rated Nano- and Micro-Influencers (Primary Active Dataset)
- **Source**: RepOD (Interdisciplinary Centre for Mathematical and Computational Modelling, Poland).
- **Authors**: Paweł Korzyński & Olga Protsiuk (2026).
- **Persistent DOI**: [10.18150/KUW9CA](https://doi.org/10.18150/KUW9CA).
- **License**: Creative Commons Attribution 4.0 International (CC-BY-4.0).
- **What It Contains**:
  - 392 usable real Instagram creator profiles observed over a 3-month period.
  - Four explicit niche categories: `fitness`, `beauty`, `lifestyle`, and `travel`.
  - Actual follower counts, post counts, average likes, and average comments.
  - **Judge-Rated Psychological Constructs**: Two independent expert judges rated each influencer on standardized scientific multi-item scales:
    1. *Opinion Leadership* (6 items measuring ability to influence others)
    2. *Authenticity* (3 items measuring genuine presentation)
    3. *Inspiration* (3 items measuring thought stimulation)
    4. *Content Expertise* (3 items measuring subject-matter knowledge)
    5. *Intention to Recommend* (2 items measuring willingness to share)
- **Known Limitations**:
  - Does not contain user bios or post caption text.
  - Does not contain audience demographics (age/gender breakdown).
  - Exact observation dates are not disclosed.

---

### Dataset 2: Zenodo Educational Instagram Reels Dataset (Secondary Source)
- **Source**: Zenodo Open Repository.
- **Author**: Grigorii Tvorogov (2026).
- **Persistent DOI**: [10.5281/zenodo.23301344](https://doi.org/10.5281/zenodo.23301344).
- **License**: Creative Commons Attribution 4.0 International (CC-BY-4.0).
- **What It Contains**:
  - 300 individual educational Instagram Reels from 21 distinct public accounts.
  - Hand-coded educational topics, reel view counts, comment counts, and research quality scores.
  - Aggregated by the InfluenceMatch pipeline into account-level creator profiles.
- **Known Limitations**:
  - Focused specifically on educational content.
  - Does not include like counts (so traditional engagement rate cannot be calculated).

---

### Dataset 3: Cheerful Instagram Engagement Reference Benchmarks
- **Source**: Cheerful.ai Research.
- **License**: Creative Commons Attribution 4.0 International (CC-BY-4.0).
- **Measurement Window**: August 17, 2026 – September 6, 2026.
- **Sample Size**: 5,924 Instagram creator accounts with at least 1,000 followers.
- **What It Contains**:
  - Exact engagement rate quartile statistics (`25th percentile`, `median`, `75th percentile`) grouped by follower tiers:
    - 1,000 – 5,000 followers
    - 5,000 – 20,000 followers
    - 20,000 – 100,000 followers
    - 100,000 – 1,000,000 followers
    - 1,000,000+ followers
- **How We Use It**:
  - When viewing an influencer's engagement rate, we place them into their reference quartile band (e.g. *below 25th percentile*, *median to 75th percentile*).
  - **Crucial Rule**: This reference is used for descriptive comparison only; it does not change an influencer's recommendation score.

---

## 3. Cryptographic Provenance: How We Guarantee Integrity

Every dataset entering InfluenceMatch is accompanied by a **Provenance Manifest** (`dataset_manifest.json`).

### What is a Cryptographic Hash?
A hash function (like SHA-256) takes a file and calculates a unique digital fingerprint. If even a single letter, number, or space in the file is modified, the hash changes completely.

```
[ Raw Dataset File ]  ───►  SHA-256 Algorithm  ───►  94338a9aa29d7357f3c507d... (Digital Fingerprint)
```

### The Ingestion Verification Chain:
1. When data is imported, its **MD5** and **SHA-256** checksums are computed and stored in the manifest.
2. Before any API endpoint serves recommendations, it re-calculates the SHA-256 of the data file on disk.
3. If the hash does not match, the system **immediately halts with an error** and refuses to serve corrupted or tampered data.
4. The exact SHA-256 fingerprint is included in every API response and displayed on the web dashboard badge (`Provenance Verified · 392 Profiles`).
