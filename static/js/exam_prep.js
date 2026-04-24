// Toggle time inputs based on mode
document.querySelectorAll('input[name="examMode"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const timeControls = document.getElementById('simulationTimeControls');
        const startBtn = document.getElementById('startExamBtn');
        
        if (this.value === 'simulation') {
            timeControls.classList.remove('d-none');
            startBtn.textContent = 'Start Exam Session';
        } else {
            timeControls.classList.add('d-none');
            startBtn.textContent = 'Start Exam';
        }
    });
});

document.getElementById('examConfigForm').addEventListener('submit', function (e) {
    e.preventDefault();
    
    const mode = document.querySelector('input[name="examMode"]:checked').value; 
    const behavior = document.querySelector('input[name="interfaceBehavior"]:checked').value; 
    const exam_id = document.getElementById('startExamBtn').getAttribute('data-exam-id');
    const csrf_token = document.querySelector('input[name="csrfmiddlewaretoken"]').value; 
    
    let session_start = null;
    let exam_start = null;

    if (mode === 'simulation') {
        session_start = document.getElementById('sessionStartTime').value;
        exam_start = document.getElementById('examStartTime').value;
        
        if (!session_start || !exam_start) {
            alert("Please set both Session and Exam start times for Simulation mode.");
            return;
        }
    }
    
    const payload = { exam_id, mode, behavior, session_start, exam_start, tz_offset: new Date().getTimezoneOffset() };
    
    async function sendData() {
        try {
            const response = await fetch("/api/exam_interface/init/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrf_token,
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            
            const data = await response.json();

            if (data.success) {
                let url = mode === "simulation" ? "login/" : "quiz/";
                window.location.assign(`/gate/${url}`);
            } else {
                console.log("Request failed:", data);
            }

        } catch (error) {
            console.error("Error occurred:", error);
        }
    }

    sendData();
});

// Update button text based on mode selection
document.querySelectorAll('input[name="examMode"]').forEach(radio => {
    radio.addEventListener('change', function () {
        const btn = document.getElementById('startExamBtn');
        btn.textContent = this.value === 'test' ? 'Start Exam' : 'Start Exam Session';
    });
});