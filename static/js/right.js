document.oncontextmenu = () => {
    alert("Dont try right click")
    return false
}

document.onkeydown = e => {

    if(e.shiftKey && e.metaKey && e.key.toLowerCase() == "s"){
        e.preventDefault()
        e.stopPropagation()
        return false
    }

    if(e.key == "F12"){
        alert("Dont try inspect element")
        return false
    }

    if( e.ctrlKey && e.key == "u"){
        alert("Dont try inspect element")
        return false
    }

    if( e.ctrlKey && e.key == "c"){
        alert("Dont try inspect element")
        return false
    }

    if( e.ctrlKey && e.key == "v"){
        alert("Dont try inspect element")
        return false
    }
}

