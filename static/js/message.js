var show_message = function(message, type) {
	if (!type)
		type = "success";

	$('.top-right').notify({
		"type" : type,
		message : {
			"text" : message
		},
		fadeOut : {
			enabled : true,
			delay : 5000
		}
	}).show();
};