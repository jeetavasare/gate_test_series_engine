

// ==================== COPY QUESTION TO CLIPBOARD ====================



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




// ==================== BLUR UNBLUR ANSWER ====================




const answerContents = document.querySelectorAll(".ans-content");

// 2. Attach the toggle logic to each element
answerContents.forEach(element => {
    element.addEventListener("click", function () {
        // 'this' refers to the clicked element
        if (this.classList.contains("blurred")) {
            // Currently blurred -> Unblur it
            this.classList.remove("blurred");
            this.textContent = this.dataset.answer;
        } else {
            // Currently visible -> Blur it
            this.classList.add("blurred");
            this.textContent = "XX";
        }
    });
});

// 3. Global function: Blur all answers
function blurAllAnswers() {
    const allAnswers = document.querySelectorAll(".ans-content");
    allAnswers.forEach(element => {
        element.classList.add("blurred");
        element.textContent = "XX";
    });
}

// 4. Global function: Unblur all answers
function unblurAllAnswers() {
    const allAnswers = document.querySelectorAll(".ans-content");
    allAnswers.forEach(element => {
        element.classList.remove("blurred");
        element.textContent = element.dataset.answer;
    });
}





// =========== QUESTION COPY LINK AND COPY TEXT EASY WAY ===========



function initHeaderCopyListeners(container) {
    if (!container) return;

    container.addEventListener('click', (e) => {
        // 1. Check if clicked within the Left Zone (Reference Copy)
        const refZone = e.target.closest('.zone-copy-ref');
        if (refZone) {
            // Do not intercept if user specifically clicked the anchor tag
            if (e.target.closest('a')) {
                return;
            }
            copyQuestionReference(refZone);
            return;
        }

        // 2. Check if clicked within the Right Zone (Question Text Copy)
        const textZone = e.target.closest('.zone-copy-text');
        if (textZone) {
            // If clicking the button directly, let its default listener run normally
            if (e.target.closest('.copy-btn')) {
                return;
            }
            triggerQuestionCopy(textZone);
        }
    });
}

// Hook it to the main container holding all question
// delegation way so that if dynamically loaded any content the evenlistner Applies to that as well
const questionsWrapper = document.querySelector('.question-list-wrapper');
initHeaderCopyListeners(questionsWrapper);
/**
 * Function 1: Builds the formatted reference string and copies both rich HTML and Markdown.
 * Maps 'Numerical', 'Multiple Choice', 'Multiple Select' to 'NAT', 'MCQ', 'MSQ'.
 */
function copyQuestionReference(refElement) {
    const qid = refElement.dataset.qid || '';
    const category = refElement.dataset.category || '';
    const rawType = (refElement.dataset.type || '').trim();
    const marks = Math.trunc(Number(refElement.dataset.marks || 0));;
    const relativeUrl = refElement.dataset.url || '';
    const fullUrl = new URL(relativeUrl, window.location.origin).href;

    const typeMapping = {
        'Numerical': 'NAT',
        'Multiple Choice': 'MCQ',
        'Multiple Select': 'MSQ'
    };
    const mappedType = typeMapping[rawType] || rawType;

    // Output: QID: Subject Name(NAT) 2m
    const formattedTitle = `Q${qid}: ${category}(${mappedType}) ${marks}m`;
    const html = `<a href="${fullUrl}">${formattedTitle}</a>`;

    const listener = (e) => {
        e.clipboardData.setData('text/html', html);
        e.clipboardData.setData('text/plain', fullUrl);
        e.preventDefault();
    };

    document.addEventListener('copy', listener);
    document.execCommand('copy');
    document.removeEventListener('copy', listener);
}

/**
 * Function 2: Finds and triggers the native click event of the copy button inside the container.
 */
function triggerQuestionCopy(zoneElement) {
    const copyBtn = zoneElement.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.click();
    }
}
