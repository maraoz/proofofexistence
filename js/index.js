$(document).ready(function() {

	var message = {
		"format" : "Must select a file to upload",
		"existing" : "File already exists in the system since %s. Proof code: %s",
		"added" : "File successfully added to system. Proof code: %s"
	}

	var refreshLatest = function() {
		var latest = $('#latest');
		$.getJSON('api/latest', function(data) {
			var items = [];

			items.push('<thead><tr><th>Document Digest</th><th>Timestamp</th></tr></thead>');
			$.each(data, function(index, obj) {
				items.push('<tr><td><a href="/detail/' + obj.digest+'">'+obj.digest + '</a></td><td> ' + obj.timestamp + '</td></tr>');
			});

			latest.empty();
			$('<div/>', {
				'class' : 'unstyled',
				html : items.join('<br />')
			}).appendTo(latest);
		});
	}

	// upload form
	var bar = $('.bar');
	var error = $(".slidingDiv");

	$("#upload_submit").click(function(event) {
		$('#upload_form').ajaxForm({
			dataType : 'json',
			beforeSubmit : function() {
				var percentVal = '0%';
				bar.removeClass('bar-danger');
				bar.removeClass('bar-warning');
				bar.removeClass('bar-success');
				bar.addClass('bar-info');
				bar.width(percentVal)
			},
			uploadProgress : function(event, position, total, percentComplete) {
				var percentVal = percentComplete + '%';
				bar.width(percentVal)
			},
			success : function(json) {
				e = error.clone();
				if (json.success) {
					bar.removeClass('bar-info');
					bar.addClass('bar-success');
					e.text(vsprintf(message["added"], [json.digest]));
				} else {
					bar.removeClass('bar-info');
					if (json.args) {
						bar.addClass('bar-warning');
						e.text(vsprintf(message[json.reason], json.args));
					} else {
						bar.addClass('bar-danger');
						e.text(message[json.reason]);
					}
					
				}
				error.after(e);
				e.slideToggle().delay(10000).slideToggle();
				if (json.digest) {
					window.setTimeout(function() {
						window.location.replace("/detail/"+json.digest);
					}, 5000);
				}
			}
		});

	});

	// latest list
	refreshLatest();

});