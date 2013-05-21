$(document).ready(function() {

	var digest = $('#digest');
	var timestamp = $('#timestamp');
	var blockchain_message = $('#blockchain_message');
	var icon = $('#icon');
	var certify_message = $('#certify_message');
	var coinbase_button = $('#coinbase-button');
	
	var pathname = window.location.pathname;
	var uuid = pathname.split("/")[2];

	var postData = {
		"d" : uuid
	};

	var onFail = function() {
		digest.html("Error!");
		timestamp.html("We couldn't find that document");
	};

	$.post('/api/detail', postData, function(data) {
		if (data.success == true) {
			blockchain_message.show();
			digest.html(data.digest);
			timestamp.html("Registered in our servers since: <strong>"+data.timestamp+"</strong>");
			var msg = "";
			if (data.in_blockchain) {
				msg = 'Document proof embedded in the Bitcoin blockchain! It is uncentralizedly certified.'
			} else {
				msg = 'Document proof not embedded in the bitcoin blockchain.';
				coinbase_button.attr('data-custom', data.digest);
				$.getScript("https://coinbase.com/assets/button.js");
				certify_message.show();
			}
			blockchain_message.html(msg);
			var img_src = data.in_blockchain? "check.png" : "warn.png";
			icon.prepend('<img src="/images/'+img_src+'" />');
		} else {
			onFail();
		}
	}, "json").fail(onFail);

});