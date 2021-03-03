/**

  * NS-Lib version 1.0.0
  *
  * Written by Nicholas M. Anand
  * www.nmoleosoftware.com

**/


/**
  * GetParams
  * Gets the page URL (which should have a structure like "localhost:00000/index.html?var1=5;var2=6") and returns a dictionary of keys and values
**/

function getParams() {
	//Get the location and remove the URL (ex. nmoleosoftware.com)
	var paramsStr = window.location.toString().replace(window.location.origin.toString(), "")

	//Removes 'index.html?' or the name of the page from the paramaters
	paramsStr = paramsStr.replace(window.location.pathname + "?", "");

	//Removes any stray slashes from the paramaters
	paramsStr = paramsStr.replace("/", "");

	//Split the params into an array
	paramsArr = paramsStr.split('&');

	var params_string = "{";
	for (i = 0; i < paramsArr.length; i++) {
		var comma = ", ";
		if (i == (paramsArr.length - 1)) {
			comma = "";
		}
		params_string += "\"" + decodeURIComponent(paramsArr[i].replace(/=.*/, "")) + "\": \"" + decodeURIComponent(paramsArr[i].replace(/.*=/, "")) + "\"" + comma;
	}
	params_string += "}";

	return JSON.parse(params_string);
}