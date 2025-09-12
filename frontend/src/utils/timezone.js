// Timezone utility functions
// NO EMOJIS

/**
 * Parse a datetime string from the backend as Pacific time
 * Backend sends naive datetime strings that are already in Pacific time
 * @param {string} dateTimeString - ISO datetime string from backend
 * @returns {Date} - JavaScript Date object
 */
export const parsePacificTime = (dateTimeString) => {
  if (!dateTimeString) return null;
  
  // Backend stores times in Pacific time as naive datetime strings
  // Parse them directly without timezone conversion
  return new Date(dateTimeString);
};

/**
 * Format a datetime string from the backend for display
 * @param {string} dateTimeString - ISO datetime string from backend
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted time string
 */
export const formatPacificTime = (dateTimeString, options = { hour: 'numeric', minute: '2-digit' }) => {
  const date = parsePacificTime(dateTimeString);
  return date ? date.toLocaleTimeString('en-US', options) : '';
};

/**
 * Check if two datetime strings represent the same day in Pacific time
 * @param {string} dateTime1 
 * @param {string} dateTime2 
 * @returns {boolean}
 */
export const isSameDayPacific = (dateTime1, dateTime2) => {
  const date1 = parsePacificTime(dateTime1);
  const date2 = parsePacificTime(dateTime2);
  
  if (!date1 || !date2) return false;
  
  return date1.toDateString() === date2.toDateString();
};

/**
 * Check if a datetime string represents today in Pacific time
 * @param {string} dateTimeString 
 * @returns {boolean}
 */
export const isTodayPacific = (dateTimeString) => {
  const date = parsePacificTime(dateTimeString);
  const today = new Date();
  
  if (!date) return false;
  
  return date.toDateString() === today.toDateString();
};