window.MathJax = {
    tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']]
    }
};

var mj = document.createElement('script');
mj.id = 'MathJax-script';
mj.async = true;
mj.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
// some questions have rendering problem 2026 set 1 paper
// <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@4/tex-mml-chtml.js"></script>
// <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
// This is the JavaScript equivalent of your onerror="..."
mj.onerror = function() {
    console.warn("Offline. Injecting local fallback for MathJax...");
    
    // Remove the broken script tag
    this.remove(); 

    // Create a fresh element for the local file
    var localMj = document.createElement('script');
    localMj.id = 'MathJax-script';
    localMj.async = true;
    localMj.src = '/static/js/v3-tex-mml-chtml.js';
    
    document.head.appendChild(localMj);
};

document.head.appendChild(mj);