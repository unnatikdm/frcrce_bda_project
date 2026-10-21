# ANTIGRAVITY PROMPT: InfluenceIQ

```markdown
Build InfluenceIQ — Big Data Analytics Project
Build InfluenceIQ, an Instagram influencer recommendation system for businesses. This is a college-level Big Data Analytics project. It must be complete and functional, but small enough to implement, understand, run and demonstrate on a normal laptop.

Technology stack
Python
Apache Spark with PySpark
Spark SQL
Streamlit
Plotly
CSV and JSON for input data
Parquet for processed data
Pandas and NumPy for supporting tasks
pytest or unittest for testing
Run Spark in local mode using local[*]. Do not claim to have a multi-node cluster or HDFS deployment unless one is actually configured.

Core features
Load influencer records from CSV and optionally JSON.
Generate reproducible synthetic sample data so the project works without API keys or external services.
Clean missing values, duplicates, invalid numbers and inconsistent categories using PySpark.
Calculate engagement rates and additional recommendation features.
Use Spark SQL for niche, location, engagement and price analysis.
Save cleaned and transformed records to Parquet.
Provide a Streamlit dashboard where businesses can enter a campaign niche, budget in INR, minimum engagement rate, follower range and preferred location.
Filter unsuitable profiles and rank the remaining influencers using an explainable weighted scoring formula.
Show influencer profiles, engagement metrics, estimated prices, recommendation scores and reasons for each recommendation.
Allow users to compare selected influencers.
Add analytics charts for niche performance, engagement distribution, follower ranges and budget analysis.
Include data-quality checks, basic automated tests and a reproducible evaluation script.

Recommendation scoring
Start with configurable weights:
Niche relevance: 30%
Engagement quality: 25%
Budget fit: 20%
Audience/location match: 15%
Reach fit: 10%
Normalise factor scores before calculating the weighted sum. Document the formula, apply campaign eligibility filters first, and show why each influencer was recommended. Handle zero followers, missing values, invalid budgets and campaigns with no matches.

Big Data requirements
Demonstrate the following through actual code wherever appropriate:
Data ingestion and ETL
PySpark DataFrame transformations
Spark SQL queries
Aggregations and joins
Feature engineering
Partitioning and lazy evaluation
Parquet persistence
Caching when beneficial
Batch processing
Data-quality validation
Processing-time comparisons across dataset sizes
Recommendation evaluation
Discuss the 5 Vs of Big Data in the README. Explain that the project uses local Spark, not a real multi-node cluster. Do not claim live streaming; a repeatable batch-refresh simulation is sufficient.

Dashboard
Create five simple sections:
Overview
Find Influencers
Compare Influencers
Analytics
Data Quality and About
Keep the UI clean, modern and easy to navigate. Focus on functionality, correct metrics and understandable charts rather than animations or unnecessary design complexity.

Project structure
Use a simple structure containing:
app.py
requirements.txt
README.md
ANTIGRAVITY_PROMPT.md
data/raw/
data/processed/
src/data_ingestion.py
src/data_cleaning.py
src/feature_engineering.py
src/analytics.py
src/recommender.py
src/evaluation.py
scripts/generate_sample_data.py
tests/
Combine modules if necessary. Do not create unnecessary abstractions or unused files.

Data authenticity
Prefer an openly licensed dataset when a suitable source is available and document its origin and licence. Otherwise, use generated synthetic data, clearly labelled as synthetic. Never invent real influencer identities, claim estimated sponsorship prices are verified, or fabricate benchmark results.
Do not scrape private data, bypass platform controls, or require Instagram credentials for the demo.

Deliverables
Implement the actual code, not just a plan. Include installation instructions, exact run commands, dependency requirements, sample data, a data dictionary, testing instructions, architecture documentation, limitations and viva questions with answers.
Test the data generator, core Spark transformations, recommendation logic and application startup wherever possible. Fix errors you encounter and clearly state which checks were actually executed.
The project is complete when a new user can generate sample data, run the tests, launch the dashboard and receive ranked recommendations from campaign inputs.
Prioritise a small, reliable, authentic Big Data project over a large production-level platform. Do not add authentication, cloud infrastructure, microservices, paid APIs, Kafka or deep learning unless they are genuinely necessary.
```
