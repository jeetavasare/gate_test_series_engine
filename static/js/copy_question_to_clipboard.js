document.addEventListener('DOMContentLoaded', function() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const qId = this.getAttribute('data-qid');
            const originalText = this.innerText;
            
            try {
                const response = await fetch(`/api/get-question-text/${qId}/`);
                const data = await response.json();
                
                if (data.success) {
                    // 1. Strip ALL image tags using regex before DOM parsing to prevent 404s
                    const safeHtml = data.html.replace(/<img[^>]*>/gi, '');
                    
                    // 2. Parse the safe HTML
                    const tempDiv = document.createElement("div");
                    tempDiv.innerHTML = safeHtml;
                    
                    // Add spaces between block elements so words don't mash together
                    const plainText = tempDiv.innerText || tempDiv.textContent || "";
                    
                    // 3. Write actual text to clipboard (not the raw JSON response)
                    await navigator.clipboard.writeText(plainText.trim());
                    
                    this.innerText = 'Copied';
                    this.classList.replace('btn-outline-secondary', 'btn-outline-success');
                } else {
                    this.innerText = 'Failed!';
                }
            } catch (err) {
                console.error('Failed to copy text: ', err);
                this.innerText = 'Error!';
            }
            
            setTimeout(() => {
                // this.innerText = "Copied";
                this.classList.remove('btn-outline-success');
                this.classList.add('btn-outline-secondary');
            }, 2000);
        });
    });
})