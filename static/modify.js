// Code based on an example by W3 Schools "How to create a collapsible"
let toggles = document.getElementsByClassName("toggle");

for(let i = 0; i < toggles.length; i++){
    toggles[i].addEventListener("click", function(){
        this.classList.toggle("active");
        let content = this.nextElementSibling;
        if (content.style.maxHeight){
            content.style.maxHeight = null;
        } else {
            content.style.maxHeight = content.scrollHeight + "px";
        }
    });
}