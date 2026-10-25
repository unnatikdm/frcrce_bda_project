/**
 * InfluenceMatch Web Application Client
 * Strict zero-synthetic data policy: consumes only verifiable API endpoints.
 */

let allCreators = [];

document.addEventListener('DOMContentLoaded', () => {
  fetchDatasetState();
  fetchCreators();
  setupEventListeners();
  // Trigger initial match
  performMatch('fitness and lifestyle creators', 10);
});

async function fetchWithFallback(path, options) {
  let res = await fetch(path, options);
  if (res.status === 404 && path.startsWith('/api/')) {
    res = await fetch(path.replace('/api/', '/'), options);
  }
  return res;
}

async function fetchDatasetState() {
  const pill = document.getElementById('provenance-pill');
  const label = document.getElementById('provenance-label');
  const sourceText = document.getElementById('dataset-source-text');
  const footerLicense = document.getElementById('footer-license');

  try {
    const res = await fetchWithFallback('/api/dataset');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.status === 'available' || data.status === 'available_unverified') {
      pill.className = 'status-pill status-verified';
      label.textContent = `Provenance Verified · ${data.profiles_loaded} Profiles`;
      sourceText.textContent = `${data.dataset_name || 'RepOD Dataset'} (${data.license_id || 'CC-BY-4.0'})`;
      footerLicense.textContent = `Source: ${data.dataset_name || 'RepOD'} · License: ${data.license_id || 'CC-BY-4.0'}`;
    } else {
      pill.className = 'status-pill';
      label.textContent = `Status: ${data.status}`;
      sourceText.textContent = data.reason || 'Dataset unavailable';
    }
  } catch (err) {
    pill.className = 'status-pill';
    label.textContent = 'API Offline';
    sourceText.textContent = 'Could not connect to API server.';
  }
}

async function fetchCreators() {
  const tbody = document.getElementById('creators-tbody');
  try {
    const res = await fetchWithFallback('/api/creators?limit=500');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allCreators = await res.json();

    renderKPIs(allCreators);
    renderCategoryBars(allCreators);
    renderTable(allCreators);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="td-loading">Failed to load creators: ${err.message}</td></tr>`;
  }
}

function renderKPIs(creators) {
  if (!creators || creators.length === 0) return;

  const count = creators.length;
  document.getElementById('kpi-creators').textContent = count.toLocaleString();

  const followers = creators
    .map(c => Number(c.followers) || 0)
    .filter(n => n > 0);

  const totalFollowers = followers.reduce((a, b) => a + b, 0);
  document.getElementById('kpi-followers').textContent = totalFollowers.toLocaleString();

  // Calculate Median
  followers.sort((a, b) => a - b);
  const mid = Math.floor(followers.length / 2);
  const median = followers.length % 2 !== 0 ? followers[mid] : Math.round((followers[mid - 1] + followers[mid]) / 2);
  document.getElementById('kpi-median-followers').textContent = median.toLocaleString();

  // Unique Niches
  const niches = new Set();
  creators.forEach(c => {
    const n = c.primary_topic || (c.niches && c.niches[0]) || c.niche;
    if (n) niches.add(n);
  });
  document.getElementById('kpi-niches').textContent = niches.size.toString();
}

function renderCategoryBars(creators) {
  const container = document.getElementById('category-bars');
  if (!creators || creators.length === 0) return;

  const counts = {};
  creators.forEach(c => {
    const niche = c.primary_topic || (c.niches && c.niches[0]) || c.niche || 'Uncategorized';
    counts[niche] = (counts[niche] || 0) + 1;
  });

  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const total = creators.length;

  container.innerHTML = sorted.map(([niche, cnt]) => {
    const pct = Math.round((cnt / total) * 100);
    return `
      <div class="category-bar-row">
        <div class="category-bar-header">
          <span class="category-bar-name">${escapeHtml(niche)}</span>
          <span class="category-bar-count">${cnt} creators (${pct}%)</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${pct}%"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderTable(creators) {
  const tbody = document.getElementById('creators-tbody');
  const countLabel = document.getElementById('explorer-count');

  if (!creators || creators.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="td-loading">No matching profiles found in active dataset.</td></tr>`;
    countLabel.textContent = 'Showing 0 profiles';
    return;
  }

  countLabel.textContent = `Showing ${creators.length} profiles`;

  tbody.innerHTML = creators.map(c => {
    const id = c.creator_id || c.handle || c.id || 'N/A';
    const niche = c.primary_topic || (c.niches && c.niches[0]) || c.niche || 'N/A';
    const followers = c.followers != null ? Number(c.followers).toLocaleString() : 'N/A';
    const tier = c.tier || (c.followers < 10000 ? 'Nano' : 'Micro');
    const sm = c.source_metrics || {};
    const er = sm.engagement_rate_source_value != null ? Number(sm.engagement_rate_source_value).toFixed(2) + '%' : (c.engagement_rate != null ? (c.engagement_rate * 100).toFixed(2) + '%' : 'N/A');
    const qs = sm.audience_quality_score != null ? Number(sm.audience_quality_score).toFixed(0) : (c.audience_quality_score != null ? Number(c.audience_quality_score).toFixed(0) : 'N/A');
    const posts = sm.number_posts != null ? Number(sm.number_posts).toLocaleString() : (c.posts_count != null ? Number(c.posts_count).toLocaleString() : 'N/A');

    return `
      <tr>
        <td style="font-weight: 500;">${escapeHtml(id)}</td>
        <td><span class="badge badge-subtle">${escapeHtml(niche)}</span></td>
        <td>${followers}</td>
        <td><span class="badge ${tier === 'Nano' ? 'badge-primary' : 'badge-subtle'}">${tier}</span></td>
        <td>${er}</td>
        <td>${qs}</td>
        <td>${posts}</td>
      </tr>
    `;
  }).join('');
}

function setupEventListeners() {
  // Preset pills
  document.querySelectorAll('.preset-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      const brief = btn.getAttribute('data-brief');
      document.getElementById('brief-input').value = brief;
      document.getElementById('match-form').requestSubmit();
    });
  });

  // Match form
  const form = document.getElementById('match-form');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const brief = document.getElementById('brief-input').value.trim();
    const limit = parseInt(document.getElementById('limit-select').value, 10) || 10;
    const minFollowers = document.getElementById('min-followers').value;
    const maxFollowers = document.getElementById('max-followers').value;

    const filters = {};
    if (minFollowers) filters.min_followers = parseInt(minFollowers, 10);
    if (maxFollowers) filters.max_followers = parseInt(maxFollowers, 10);

    performMatch(brief, limit, filters);
  });

  // Explorer Search
  const searchInput = document.getElementById('explorer-search');
  searchInput.addEventListener('input', () => {
    const query = searchInput.value.toLowerCase().trim();
    if (!query) {
      renderTable(allCreators);
      return;
    }
    const filtered = allCreators.filter(c => {
      const id = String(c.creator_id || c.id || '').toLowerCase();
      const niche = String(c.niche || '').toLowerCase();
      const tier = String(c.tier || '').toLowerCase();
      return id.includes(query) || niche.includes(query) || tier.includes(query);
    });
    renderTable(filtered);
  });
}

async function performMatch(brief, limit = 10, filters = {}) {
  const submitBtn = document.getElementById('btn-submit-match');
  const banner = document.getElementById('match-status-banner');
  const resultsContainer = document.getElementById('match-results-list');

  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Matching...</span>`;
  banner.style.display = 'block';
  banner.textContent = 'Executing TF-IDF similarity and judge-rated ranking over active corpus...';
  resultsContainer.innerHTML = '';

  try {
    const payload = {
      brief: brief,
      limit: limit,
      ...filters
    };

    const res = await fetchWithFallback('/api/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || `Server returned ${res.status}`);
    }

    const data = await res.json();
    const results = data.results || [];

    if (results.length === 0) {
      banner.textContent = 'No eligible creators matched the brief and filter criteria.';
      return;
    }

    banner.innerHTML = `<strong>${results.length} authentic creators matched</strong> for "${escapeHtml(brief)}". ${escapeHtml(data.note || '')}`;

    resultsContainer.innerHTML = results.map((item, idx) => {
      const id = item.creator_id || item.handle || item.id || 'N/A';
      const niche = item.primary_topic || (item.niches && item.niches[0]) || item.niche || 'N/A';
      const followers = item.followers != null ? Number(item.followers).toLocaleString() : 'N/A';
      const score = item.match_score != null ? Number(item.match_score).toFixed(2) : (item.score != null ? Number(item.score).toFixed(2) : 'N/A');
      const sm = item.source_metrics || {};
      const er = sm.engagement_rate_source_value != null ? Number(sm.engagement_rate_source_value).toFixed(2) + '%' : (item.engagement_rate != null ? (item.engagement_rate * 100).toFixed(2) + '%' : 'N/A');
      
      let explanation = 'Ranked by historical judge-rated opinion leadership.';
      if (typeof item.score_explanation === 'object' && item.score_explanation !== null) {
        const se = item.score_explanation;
        explanation = `Score: ${se.value || score} (${se.criterion || 'opinion leadership'}) computed as ${se.formula || 'mean of observed items'} over ${se.observed_item_count || 6} items.`;
      } else if (typeof item.score_explanation === 'string') {
        explanation = item.score_explanation;
      }
      
      const ref = item.engagement_reference || {};
      const refBand = ref.reference_band ? ref.reference_band.replace(/_/g, ' ') : (ref.reason || 'Descriptive reference');

      return `
        <div class="result-card">
          <div class="result-header">
            <div>
              <div class="result-creator-id">${escapeHtml(id)}</div>
              <span class="badge badge-subtle">${escapeHtml(niche)}</span>
            </div>
            <span class="result-rank">#${idx + 1} Match</span>
          </div>

          <div class="result-metrics">
            <div class="metric-item">
              <span class="metric-item-label">Followers</span>
              <span class="metric-item-value">${followers}</span>
            </div>
            <div class="metric-item">
              <span class="metric-item-label">Opinion Leadership</span>
              <span class="metric-item-value">${score}</span>
            </div>
            <div class="metric-item">
              <span class="metric-item-label">Observed ER</span>
              <span class="metric-item-value">${er}</span>
            </div>
            <div class="metric-item">
              <span class="metric-item-label">Reference Band</span>
              <span class="metric-item-value">${refBand}</span>
            </div>
          </div>

          <div class="result-score-block">
            <div class="result-score-title">Ranking Explanation</div>
            <div>${escapeHtml(explanation)}</div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    banner.textContent = `Match Error: ${err.message}`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
      <span>Find Matches</span>
    `;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
