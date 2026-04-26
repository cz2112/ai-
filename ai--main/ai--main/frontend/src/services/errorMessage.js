function fromDetail(detail) {
  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim();
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item.trim();
        if (item && typeof item.msg === 'string') return item.msg.trim();
        if (item && typeof item.message === 'string') return item.message.trim();
        return '';
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join('; ');
    }
  }

  if (detail && typeof detail === 'object') {
    if (typeof detail.msg === 'string' && detail.msg.trim()) {
      return detail.msg.trim();
    }
    if (typeof detail.message === 'string' && detail.message.trim()) {
      return detail.message.trim();
    }
  }

  return '';
}

export default function getApiErrorMessage(error, fallback = 'Something went wrong') {
  const responseData = error?.response?.data;

  const detailMessage = fromDetail(responseData?.detail);
  if (detailMessage) {
    return detailMessage;
  }

  const message = fromDetail(responseData?.message);
  if (message) {
    return message;
  }

  if (typeof error?.message === 'string' && error.message.trim()) {
    return error.message.trim();
  }

  return fallback;
}
