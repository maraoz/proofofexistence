
var disclaimer = "<strong>Important: </strong>Your browser does not support HTML5, so your document will need to be uploaded." +
	" The cryptographic digest will be calculated on our servers but the document will be" +
	" discarded immediately, without being stored, logged, or otherwise accessed. " +
	"Please contact us if you have any questions."

var messages = {};

// English
messages["en_US"] = {};
messages["en_US"][disclaimer] = "";

// Spanish (all locales)
messages["es"] = {
	"Error!": "",
	"We couldn't find that document": "",
	"Registered in our servers since:": "",
	"Registered in the bitcoin blockchain since:": "",
	"transaction timestamp": "timestamp de la transacción",
	"Document proof embedded in the Bitcoin blockchain!": "",
	"Document proof not yet embedded in the bitcoin blockchain.": "",
	"Payment being processed. Please wait while the bitcoin transaction is confirmed by the network.": "",
	"Transaction": "Transacción",
	"Must select a file to upload": "",
	"File already exists in the system since %s. Redirecting...": "",
	"File successfully added to system. Redirecting...": "",
	"Document Digest": "",
	"Timestamp": "Timestamp",
	"Initializing": "",
	"Now hashing... ": "",
	"Loading document...": "",
	"Preparing to hash ": "",
	" bytes, last modified: ": "",
	"n/a": ""
};
messages["es"][disclaimer] = "";

var translate = function(msg){
	var myLang = $(".language").val();
	return messages[myLang][msg] || msg;
};

var setLanguage = function(){
	var myLang = $(".language").val();
	var expiry = new Date(60 * 24 * 60 * 60 * 1000 + Date.now());
	document.cookie="language=" + myLang + "; expires=" + expiry;
	window.location.reload();
}