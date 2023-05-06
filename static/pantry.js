function toggleAutofill(element)
 {
  document.getElementById("autofill-selected").value = element.value;
  document.getElementById("grocery_list").submit();
 }