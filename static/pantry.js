function toggleAutofill(element)
 {
    var form = document.getElementById("grocery_list");
    form.addEventListener('submit', function () {
        console.log('invoked');
        
        return false;
      });
      
      // form.submit();
      form.dispatchEvent(new Event('submit'));
 }