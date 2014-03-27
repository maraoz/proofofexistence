from webapp2_extras import i18n
from webapp2_extras.i18n import gettext as _

known_locales = ["en_US", "es"]

def get_preferred_locale(request):
	preferred_locale = "en_US"
	if request.get("lang"):
		preferred_locale = request.get("lang")
	elif request.cookies.has_key("language"):
		preferred_locale = request.cookies["language"]
	elif request.headers.get("accept_language"):
		preferred_locale = request.headers.get("accept_language")
	if preferred_locale not in known_locales:
		if preferred_locale.split("_")[0] not in known_locales:
			# this locale has no known match
			preferred_locale = "en_US"
		else:
			# this locale has a similar match
			preferred_locale = preferred_locale.split("_")[0]
	return preferred_locale

def get_client_side_translations():
	return {
    	"disclaimer": _("disclaimer"),
        "Error!": _("Error!"),
		"We couldn't find that document": _("We couldn't find that document"),
		"Registered in our servers since:": _("Registered in our servers since:"),
		"Registered in the bitcoin blockchain since:": _("Registered in the bitcoin blockchain since:"),
		"transaction timestamp": _("transaction timestamp"),
		"Document proof embedded in the Bitcoin blockchain!": _("Document proof embedded in the Bitcoin blockchain!"),
		"Document proof not yet embedded in the bitcoin blockchain.": _("Document proof not yet embedded in the bitcoin blockchain."),
		"Payment being processed. Please wait while the bitcoin transaction is confirmed by the network.": _("Payment being processed. Please wait while the bitcoin transaction is confirmed by the network."),
		"Transaction": _("Transaction"),
		"Must select a file to upload": _("Must select a file to upload"),
		"File already exists in the system since %s. Redirecting...": _("File already exists in the system since %s. Redirecting..."),
		"File successfully added to system. Redirecting...": _("File successfully added to system. Redirecting..."),
		"Document Digest": _("Document Digest"),
		"Document Hash": _("Document hash: "),
		"Timestamp": _("Timestamp"),
		"Initializing": _("Initializing"),
		"Now hashing... ": _("Now hashing... "),
		"Loading document...": _("Loading document..."),
		"Preparing to hash ": _("Preparing to hash "),
		" bytes, last modified: ": _(" bytes, last modified: "),
		"n/a": _("n/a")
	}