$(document).ready(function() {

	var digest = $('#digest');
	var timestamp = $('#timestamp');
	var blockchain_message = $('#blockchain_message');
	var icon = $('#icon');
	var certify_message = $('#certify_message');
	var coinbase_button = $('#coinbase-button');
	var confirmed_message = $('#confirmed_message');
	var confirming_message = $('#confirming_message');
	var ladd1 = $('#ladd1');
	var radd1 = $('#radd1');
	var ladd2 = $('#ladd2');
	var radd2 = $('#radd2');
	var tx = $('#tx');
	
	var pathname = window.location.pathname;
	var uuid = pathname.split("/")[2];

	var postData = {
		"d" : uuid
	};

	var onFail = function() {
		digest.html(translate("Error!"));
		timestamp.html(translate("We couldn't find that document"));
	};
	
	var onSuccess = function(data) {
		if (data.success == true) {
			data = data.doc;
			confirming_message.hide();
			blockchain_message.show();
			digest.html(data.digest);
			var times = translate("Registered in our servers since:") + " <strong>"+data.timestamp+"</strong><br /><br />";
			if (data.blockstamp) {
				times += translate("Registered in the bitcoin blockchain since:") + " <strong>"+data.blockstamp+"</strong> (" + translate("transaction timestamp") + ")<br /><br />";
			}
			timestamp.html(times);
			var msg = "";
			var clz = "";
			var in_blockchain = data.tx != null;
			var has_addresses = data.ladd != null && data.radd != null;
			var img_src = "";
			if (in_blockchain) {
				msg = translate('Document proof embedded in the Bitcoin blockchain!');
				clz = "alert-success";
				img_src = "check.png";
				tx.html('<a href="https://blockchain.info/tx/'+data.tx+'"> ' + translate('Transaction') + ' '+data.tx+'</a>');
				ladd2.html('<a href="https://blockchain.info/address/'+data.ladd+'">'+data.ladd+'</a>');
				radd2.html('<a href="https://blockchain.info/address/'+data.radd+'">'+data.radd+'</a>');
				confirmed_message.show();
			} else if (has_addresses) {
				msg = translate('Payment being processed. Please wait while the bitcoin transaction is confirmed by the network.');
				clz = "alert-warn";
				img_src = "wait.png";
				ladd1.html('<a href="https://blockchain.info/address/'+data.ladd+'">'+data.ladd+'</a>');
				radd1.html('<a href="https://blockchain.info/address/'+data.radd+'">'+data.radd+'</a>');
				confirming_message.show();
				$.post('/api/document/check', postData, onCheckSuccess, "json");
			} else {
				msg = translate('Document proof not yet embedded in the bitcoin blockchain.');
				clz = "alert-danger";
				img_src = "warn.png";
				coinbase_button.attr('data-custom', data.digest);
				$.getScript("https://coinbase.com/assets/button.js");
				certify_message.show();
			}
			blockchain_message.html(msg);
			blockchain_message.addClass(clz);
			icon.html('<img src="/static/img/'+img_src+'" />');
		} else {
			onFail();
		}
	};
	
	var onCheckSuccess = function(data) {
		if (data.success == true) {
			askDetails();
		} else {
		}
	};

	var askDetails = function() {
		$.post('/api/document/get', postData, onSuccess, "json").fail(onFail);
	}

	askDetails();
	
	

});