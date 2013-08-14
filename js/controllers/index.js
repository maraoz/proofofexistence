$(document).ready(function() {

	var message = {
		"format" : "Must select a file to upload",
		"existing" : "File already exists in the system since %s. <strong>Redirecting...</strong>",
		"added" : "File successfully added to system. <strong>Redirecting...</strong>"
	}
	
	var bar = $('.bar');
	var error = $(".slidingDiv");
	var upload_submit = $("#upload_submit");
	var upload_form = $('#upload_form');
	var latest = $('#latest');
	var latest_confirmed = $('#latest_confirmed');
	var explain = $('#explain');

	// uncomment this to try non-HTML support:
	//window.File = window.FileReader = window.FileList = window.Blob = null;
	
	var html5 = window.File && window.FileReader && window.FileList && window.Blob; 
	if (!html5) {
		explain.html("<strong>Important: </strong>Your browser does not support HTML5, so your document will need to be uploaded." +
				" The cryptographic digest will be calculated on our servers but the document will be" +
				" discarded immediately, without being stored, logged, or otherwise accessed. " +
				"Please contact us if you have further questions.");
		upload_submit.show();
	}

	// latest documents
	var refreshLatest = function(confirmed, table) {
		$.getJSON('api/latest?confirmed='+confirmed, function(data) {
			var items = [];

			items.push('<thead><tr><th></th><th>Document Digest</th><th>Timestamp</th></tr></thead>');
			$.each(data, function(index, obj) {
				badge = "";
				if (obj.tx) {
					badge = '<span class="label label-success">✔</span>';
				}
				items.push('<tr><td>'+badge+'</td><td><a href="/detail/' + obj.digest+'">'+obj.digest +
						'</a></td><td> ' + obj.timestamp + '</td></tr>');
			});

			table.empty();
			$('<div/>', {
				'class' : 'unstyled',
				html : items.join('<br />')
			}).appendTo(table);
		});
	}
	refreshLatest("false", latest);
	refreshLatest("true", latest_confirmed);

	// client-side hash
	var onRegisterSuccess = function(json) {
		e = error.clone();
		if (json.success) {
			bar.removeClass('bar-info');
			bar.addClass('bar-success');
			e.html(vsprintf(message["added"], []));
		} else {
			bar.removeClass('bar-info');
			if (json.args) {
				bar.addClass('bar-warning');
				e.html(vsprintf(message[json.reason], json.args));
			} else {
				bar.addClass('bar-danger');
				e.html(message[json.reason]);
			}
			
		}
		error.after(e);
		e.show();
		if (json.digest) {
			window.setTimeout(function() {
				window.location.replace("/detail/"+json.digest);
			}, 5000);
		}
	}
	
	var crypto_callback = function(p) {
		var w = ((p*100).toFixed(0));
		bar.width( w+"%");
		explain.html("Now hashing... "+(w)+"%");
	}
	
	var crypto_finish = function(hash) {
		bar.width(100 + "%");
		explain.html("Document hash: "+hash);
		$.getJSON('api/register?d='+hash, onRegisterSuccess);
	}
	
	function handleFileSelect(evt) {
		if (!html5) {
			return;
		}
		explain.html("Loading document...");
	    var files = evt.target.files;
	    var output = "";
	    for (var i = 0, f; f = files[i]; i++) {
	      output = '<strong>' + escape(f.name)
			+ '</strong> (' + (f.type || 'n/a') + ') - '
			+ f.size + ' bytes, last modified: '
			+ (f.lastModifiedDate ? f.lastModifiedDate
			.toLocaleDateString() : 'n/a' )+ '';
	      break;
	    }
	    var reader = new FileReader();
		reader.onload = function(e) {
			var data = e.target.result;
			bar.width(0+"%");
			bar.addClass('bar-success');
			explain.html("Now hashing... Initializing");
			setTimeout(function() {
				CryptoJS.SHA256("Hi there n00bs"/*data*/,crypto_callback,crypto_finish);
			}, 200);
			
		};
		reader.onprogress = function(evt) {
		    if (evt.lengthComputable) {
		    	var w = (((evt.loaded / evt.total)*100).toFixed(2));
				bar.width( w+"%");
		    }
		  }
        reader.readAsBinaryString(f);
	    error.html('<ul>' + output + '</ul>');
	    error.show();
	  }

	  document.getElementById('file').addEventListener('change', handleFileSelect, false);
	
	
	// upload form (for non-html5 clients)
	upload_submit.click(function(event) {
		upload_form.ajaxForm({
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
			success : onRegisterSuccess
		});

	});



});