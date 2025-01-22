window.addEventListener('load', function(){
      const body = document.querySelector("body");
       const error = body.getAttribute("data-error");
       if(error){
          alert("Error: " + error);
       }
    });