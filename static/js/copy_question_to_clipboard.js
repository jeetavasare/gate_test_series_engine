document.addEventListener('DOMContentLoaded', function() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const qId = this.getAttribute('data-qid');
            const user_answer = this.getAttribute('data-user-answer');
            const originalText = this.innerText;
            
            try {
                const response = await fetch(`/api/get-question-text/${qId}/`);
                const data = await response.json();
                
                if (data.success) {
                    const safeHtml = data.html.replace(/<img[^>]*>/gi, '');
                    const correct_answer = data.correct_answer;
                    
                    const tempDiv = document.createElement("div");
                    tempDiv.innerHTML = safeHtml;
                    
                    // Find all ordered lists and dismantle them to prevent Markdown auto-numbering
                    const orderedLists = tempDiv.querySelectorAll('ol');
                    orderedLists.forEach(ol => {
                        const listWrapper = document.createElement('div');
                        const items = ol.querySelectorAll('li');
                        
                        items.forEach((li, index) => {
                            const letter = String.fromCharCode(65 + index); 
                            const paragraph = document.createElement('p');
                            
                            // Inject structural lettering directly without list item syntax
                            paragraph.innerHTML = `<strong>${letter}.</strong> ` + li.innerHTML;
                            listWrapper.appendChild(paragraph);
                        });
                        
                        // Replace the original <ol> with the clean <div> structure
                        ol.parentNode.replaceChild(listWrapper, ol);
                    });
                    
                    const metaContainer = document.createElement("div");
                    metaContainer.innerHTML = `<br><p><strong>Correct Answer:</strong> ${correct_answer}</p>` + 
                        (user_answer ? `<p><strong>Your Answer:</strong> ${user_answer}</p>` : '');
                    tempDiv.appendChild(metaContainer);

                    const htmlText = tempDiv.innerHTML;
                    const plainText = tempDiv.innerText || tempDiv.textContent || "";
                    
                    const blobHtml = new Blob([htmlText], { type: 'text/html' });
                    const blobText = new Blob([plainText], { type: 'text/plain' });
                    
                    const item = new ClipboardItem({
                        'text/html': blobHtml,
                        'text/plain': blobText
                    });
                    
                    await navigator.clipboard.write([item]);
                    
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
                this.innerText = originalText;
                this.classList.remove('btn-outline-success');
                this.classList.add('btn-outline-secondary');
            }, 2000);
        });
    });
});