document.addEventListener('DOMContentLoaded', async () => {
    const data = await examContextHandler();

    $('#candidate-name').text(data.candidate_name);

    $('#candidate-image').attr("src", data.candidate_profile_image_full_link);


    $(".instruTimeCounter").show();
    $("#checkBoxEnableMessage").show();
    document.getElementById("disclaimer").disabled = "disabled";

    function updateCountdown() {
        const now = Date.now();
        const examStartTime = new Date(data.exam_start_time);
        const diffInMs = examStartTime - now;
        let time = ""
        if (diffInMs <= 0) {
            time = "Time: 00:00";
            $(".checkBoxEnableMessage").hide();
            document.getElementById("disclaimer").removeAttribute("disabled", 0);
        }

        else {
            const totalSeconds = Math.floor(diffInMs / 1000);
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            time = `Time: ${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
            document.getElementById("disclaimer").disabled = "disabled";
        }


        $(".instruTimeCounter").text(time);
        $("#checkBoxEnableTime").text(time)

    }

    setInterval(() => {
        updateCountdown();
    }, 1000);

    const readyToBeginButton = document.getElementById("readylink")
    readyToBeginButton.addEventListener("click", ()=> {
        
        async function attemptStartExam() {
            try{
                const response = await fetch("/api/exam_interface/start/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });
                const data = await response.json()
                if(!data.success){
                    document.getElementById("errorMessageBox").style.visibility = 'visible'
                    document.getElementById("errorMessageBox").innerText = data.error
                }
                else{
                    window.location.assign("/gate/quiz")
                }
            }
            catch{
            }
        }

        attemptStartExam();
        
    });


});