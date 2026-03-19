document.querySelectorAll('.format-date').forEach(el => {
    const raw = el.dataset.date;
    const date = new Date(raw);

    if (!isNaN(date)) {
        const adjustedDate = new Date(date.getTime());

        el.textContent = adjustedDate.toLocaleString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    }
});

document.querySelectorAll('.get-exam-start-time').forEach(el => {
    const rawDate = el.dataset.base;
    const mins = parseInt(el.dataset.mins) || 0; // Handle empty/null
    
    const dateObj = new Date(rawDate);
    
    if (!isNaN(dateObj)) {
        // Subtract minutes (converted to milliseconds)
        const adjustedDate = new Date(dateObj.getTime() - (mins * 60000));
        
        el.textContent = adjustedDate.toLocaleString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    }
});