document.addEventListener('DOMContentLoaded', async () => {
    try{
        const response = await fetch(`/api/exam_interface/active/`);
        const data = await response.json();
        if(data.active){
            // let ans = confirm("There is an active exam session. Do you wish to continue.\n(Clicking cancel will destroy the session!!)")
            let ans = confirm("There is an active exam session. Do you wish to continue the exam?")
            if(ans){
                if(window.location.href.includes(data.redirect_url)){
                    return;
                }
                window.location.assign(data.redirect_url);
            }
        }
    }
    catch(e){
        console.log(e);
    }
});