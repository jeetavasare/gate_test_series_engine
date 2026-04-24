function normalize(path) {
    if (!path) return "/";
    return path.endsWith("/") ? path.slice(0, -1) : path;
}

async function examContextHandler(){
    const response = await fetch("/api/exam_interface/context/")
    const data = await response.json();

    const currentPath = normalize(window.location.pathname);
    const targetPath = normalize(data.redirect_url);
    
    if(currentPath === targetPath){
        return data;
    }
    else{
        window.location.assign(data.redirect_url);
    }
}