/**
 * historyManager.js - Session Management & Local History Caching for AyurEval.
 *
 * Persists audits, inquiries, dual-evaluations, and safety reports to localStorage
 * with timestamps, status tags, and quick-reload capability.
 */

const HISTORY_STORAGE_KEY = 'ayureval_audit_history_v1';
const MAX_HISTORY_ITEMS = 35;

/**
 * Retrieves all stored history items, sorted from newest to oldest.
 * @returns {Array<Object>} List of history entries
 */
export function getHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.error('Failed to read AyurEval history from localStorage:', err);
    return [];
  }
}

/**
 * Saves a completed report session into localStorage.
 *
 * @param {string} type - 'ask' | 'verify' | 'dual' | 'safety' | 'batch'
 * @param {string} queryOrText - The prompt, question, or text that was audited
 * @param {Object} report - The full report object returned by backend
 * @returns {Array<Object>} Updated history list
 */
export function saveReportToHistory(type, queryOrText, report) {
  if (!report) return getHistory();

  try {
    const current = getHistory();
    const cleanText = (queryOrText || '').trim();
    const title = cleanText.length > 90 ? cleanText.slice(0, 87) + '...' : cleanText;

    // Generate brief display summary based on report type
    let displaySummary = '';
    let badge = '';

    if (type === 'ask' || type === 'verify') {
      const claimsCount = report.claims?.length || 0;
      displaySummary = report.overall_summary || `${claimsCount} claim(s) audited.`;
      badge = type === 'ask' ? 'Inquiry' : 'Verification';
    } else if (type === 'dual') {
      const claimsCount = report.claims?.length || 0;
      const grades = report.grade_summary || {};
      const gradeStr = Object.entries(grades).map(([g, c]) => `${c} ${g}`).join(', ');
      displaySummary = gradeStr || report.executive_summary || `${claimsCount} claim(s) dual-audited.`;
      badge = 'Dual Audit';
    } else if (type === 'safety') {
      const isSafe = report.is_safe;
      const herbCount = report.detected_herbs?.length || 0;
      displaySummary = report.summary || (isSafe ? 'Classical clearance passed.' : 'Hazard flagged.');
      badge = isSafe ? 'Safety Safe' : 'Safety Hazard';
    } else if (type === 'batch') {
      const count = report.analytics?.total_claims || 0;
      const supported = report.analytics?.supported || 0;
      const safetyFlags = report.analytics?.total_safety_flags || 0;
      displaySummary = `${count} claims: ${supported} supported, ${safetyFlags} safety flag(s).`;
      badge = 'Batch Audit';
    }

    const newItem = {
      id: `session_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      type,
      badge,
      title: title || 'Untitled Ayurvedic Inquiry',
      queryOrText: cleanText,
      timestamp: Date.now(),
      displayDate: new Date().toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }),
      displaySummary,
      report,
    };

    // Prepend and enforce max items limit
    const updated = [newItem, ...current.filter((item) => item.queryOrText !== cleanText)].slice(
      0,
      MAX_HISTORY_ITEMS
    );

    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
    return updated;
  } catch (err) {
    console.error('Failed to save AyurEval session to localStorage:', err);
    return getHistory();
  }
}

/**
 * Removes a specific history item by ID.
 * @param {string} id
 * @returns {Array<Object>} Updated history list
 */
export function deleteHistoryItem(id) {
  try {
    const current = getHistory();
    const updated = current.filter((item) => item.id !== id);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
    return updated;
  } catch (err) {
    console.error('Failed to delete history item:', err);
    return getHistory();
  }
}

/**
 * Clears all saved AyurEval history.
 */
export function clearAllHistory() {
  try {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    return [];
  } catch (err) {
    console.error('Failed to clear AyurEval history:', err);
    return [];
  }
}
