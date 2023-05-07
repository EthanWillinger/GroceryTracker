function toggleAutofill(element)
 {
  document.getElementById("autofill-selected").value = element.value;
  document.getElementById("grocery_list").submit();
 }

 function UpdateNotif(element)
 {
     document.getElementById("notifupdate").value = element.value;
     document.getElementById("updateNotifs").submit();
 }