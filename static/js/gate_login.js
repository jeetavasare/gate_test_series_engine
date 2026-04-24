document.addEventListener('DOMContentLoaded', async () => {
    // fetch candidate info
    data = await examContextHandler();

    document.getElementById("candidate_name").innerText = data.candidate_name

    document.getElementById("mockSubName").innerText = data.exam_title

    document.getElementById("candidate_system_number").innerText = data.registration_number?.slice(-3)
    
    // auto fill data temporarily
    document.getElementById("candidate_reg_num").value = data.registration_number
    document.getElementById("candidate_dob").value = data.dob


    if(data.candidate_profile_image_full_link){
        document.getElementById("candidate_photo").src = data.candidate_profile_image_full_link 
    }



    const submitButton = document.getElementById("signInLabel");
    submitButton.addEventListener("click", (e) => {        
        const candidate_reg_num = document.getElementById("candidate_reg_num").value
        const candidate_dob = document.getElementById("candidate_dob").value
        if (!candidate_reg_num || !candidate_dob) {
            alert("Registration number and password is required")
            return;
        }
        const payload = {
            registration_number: candidate_reg_num,
            dob : candidate_dob,
        }
        async function attemptLogin() {
            try{
                const response = await fetch("/api/exam_interface/login/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });
                const data = await response.json()
                if(!data.success){
                    document.getElementById("errorMessageBox").style.visibility = 'visible'
                    document.getElementById("errorMessageBox").innerText = data.error
                }
                else{
                    window.location.assign("/gate/instructions")
                }
            }
            catch{
            }
        }

        attemptLogin()
    });
});