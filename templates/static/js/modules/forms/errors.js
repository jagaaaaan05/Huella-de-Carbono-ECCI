export const extractErrorMessage = (errorResponse, fallback) => {
  if (!errorResponse) {
    return fallback;
  }
  if (typeof errorResponse === 'string') {
    return errorResponse;
  }
  if (Array.isArray(errorResponse)) {
    return errorResponse.join(' ');
  }
  if (typeof errorResponse === 'object') {
    return (
      Object.entries(errorResponse)
        .map(([key, value]) => `${key}: ${extractErrorMessage(value, '')}`)
        .join(' ')
        .trim() || fallback
    );
  }
  return fallback;
};
