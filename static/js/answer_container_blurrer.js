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
