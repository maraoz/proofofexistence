$(document).ready(function() {

	// submit form

	$("#upload_submit").click(function(event) {
		event.preventDefault();

		var data = new FormData();
		jQuery.each($('#file')[0].files, function(i, file) {
			data.append('d', file);
		});

		$.ajax({
			url : 'api/register',
			data : data,
			cache : false,
			contentType : false,
			processData : false,
			type : 'POST',
			success : function(data) {
				location.reload();
			}
		});
	});

	// latest list
	$.getJSON('api/latest', function(data) {
		var items = [];

		$.each(data, function(index, obj) {
			items.push('<a>' + obj.digest + ': ' + obj.timestamp + '</a>');
		});

		$('<div/>', {
			'class' : 'unstyled',
			html : items.join('<br />')
		}).appendTo($('#latest'));
	});

});