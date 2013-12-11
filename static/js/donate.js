if (typeof CoinWidget != 'object')
var CoinWidget = {
	version: 1.1,
	information: [],
	config: null,

	/** helpers */
	log: function(string){
		if (CoinWidget.config.debug === true) {
			console.log('[CoinWidget.com] ' + string);
		}
	},
	load_script: function(id,url,callback){
		if (!document.getElementById(id)) {
			var tag = document.createElement('script');
			tag.id = id;
			tag.onreadystatechange = function(){
				switch (this.readyState) {
					case 'complete':
					case 'loaded':
						callback();
						break;
				}
			};
			tag.onload = function(){
				callback();
			};
			tag.src = url;
			document.lastChild.firstChild.appendChild(tag);		
			CoinWidget.log('+resource: ' + url);
		}
	},
	load_css: function(id,url){	
		if (!$("#"+id).length) {
			var lnk = $('<link/>');
			$("head").append(lnk);
			lnk.attr({
				id: id,
				rel: 'stylesheet',
				type: 'text/css',
				href: url
			});
			CoinWidget.log('+resource: ' + url);
		}		
	},

	/** loaders */
	load_info:function(instance){
		if (CoinWidget.instance_config[instance].hide_numbers) return;
		var address = CoinWidget.instance_config[instance].address?CoinWidget.instance_config[instance].address:'';
		CoinWidget.log('Fetching address information ...');
		CoinWidget.load_script('COINWIDGET_INFORMATION_'+instance,'/api/widget.js',function(){
			CoinWidget.log('Address information loaded!');
		});
	},
	load_jquery: function(){
		CoinWidget.log('Unable to detect jQuery, attempting to fetch it from Google.');
		CoinWidget.load_script('COINWIDGET_JQUERY','//ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js',function(){
			CoinWidget.log('jQuery loaded!');			
			CoinWidget.init();	
		});
	},

	/** construct */
	instance_config:[],
	init: function(config){
		if (config) {
			CoinWidget.config = config;
			CoinWidget.log('Version: '+CoinWidget.version+' initializing ...');
			CoinWidget.instance_config[CoinWidgetInstance] = {};
			CoinWidget.instance_config[CoinWidgetInstance] = config;

		}
		if (!window.jQuery) {
			CoinWidget.load_jquery();
			return false;
		}
		
		CoinWidget.load_css('COINWIDGET_CSS','//d1e4zb60eak76i.cloudfront.net/widget.css');
		CoinWidget.build(false,CoinWidgetInstance);
		if (CoinWidget.instance_config[CoinWidgetInstance].counter != 'hide') {
			CoinWidget.load_info(CoinWidgetInstance);
		}
		

		
	},
	
	/** output */
	build:function(info,instance){
		if (!instance) return;

		if (typeof info === 'object') {
			CoinWidget.information[instance] = info;
			CoinWidget.log('Done (with info).');
		} else {
			CoinWidget.log('Done.');
		}
		
		CoinWidget.config = CoinWidget.instance_config[instance];		


		var text 	 = CoinWidget.instance_config[instance].text
					 ? CoinWidget.instance_config[instance].text
					 : 'Donate';

		$counter = CoinWidget.instance_config[instance].counter != 'hide' && typeof CoinWidget.information[instance] != 'undefined'
				 ? CoinWidget.counter(instance)
				 : '';

		var ext_html = CoinWidget.instance_config[instance].counter == 'hide'
					 ? ''
					 : ($counter != 'undefined'
					 	? '<span>'+ $counter+'</span>'
					 	: '<span><img src="//d1e4zb60eak76i.cloudfront.net/load.gif" width="12" height="12" /></span>'
					 );
		
		var $html = '<a href="#"><i></i>'+text+'</a>'+ext_html;

		setTimeout(function(){$(".COINWIDGET_BUTTON[data-instance="+instance+"]").html($html).unbind('click').click(function(e){
			e.preventDefault();
			CoinWidget.show(this);
		});},100);

	},

	counter: function(instance){
		if (CoinWidget.information[instance]) {
			switch (CoinWidget.instance_config[instance].counter) {
				default:
				case 'transactions':
					return CoinWidget.information[instance].counter;
					break;
				case 'amount':
					return CoinWidget.information[instance].amount.toFixed(5);
					break;
			}
		}		
	},

	build_window: function(instance){
	
	if ($("[data-coinwidget-window="+instance+"]").length) return;
		var text 	 = CoinWidget.instance_config[instance].text
					 ? CoinWidget.instance_config[instance].text
					 : 'Donate';
		var text_count = CoinWidget.instance_config[instance].text_count
						 ? CoinWidget.instance_config[instance].text_count
						 : 'donations';
		var text_btc = CoinWidget.instance_config[instance].text_btc
						 ? CoinWidget.instance_config[instance].text_btc
						 : 'BTC';
		var text_label = CoinWidget.instance_config[instance].text_label
					   ? CoinWidget.instance_config[instance].text_label
					   : 'My Bitcoin Address:';
		var ext_html = CoinWidget.instance_config[instance].counter == 'hide'
					 ? ''
					 : ('<span>'+CoinWidget.information[instance].counter+'<small>'+text_count+'</small></span><span>'+CoinWidget.information[instance].amount.toFixed(5)+'<small>'+text_btc+'</small></span><br/>');
		ext_html += '<a title="Open in Wallet (if available)" target="_blank" href="bitcoin:'+CoinWidget.instance_config[instance].address+'"><img width="16" height="16" class="COINWIDGET_URI" src="//d1e4zb60eak76i.cloudfront.net/uri.png" /></a>'
		if (!CoinWidget.instance_config[instance].hide_qr) {
			ext_html += '<img width="16" height="16" class="COINWIDGET_QR" src="//d1e4zb60eak76i.cloudfront.net/qr.png" /><img width="113" height="113" class="COINWIDGET_QR_LARGE" src="//d1e4zb60eak76i.cloudfront.net" />';
		}

		$window = $('<div id="COINWIDGET_WINDOW" data-coinwidget-window="'+instance+'"><a class="COINWIDGET_WINDOW_CLOSER" href="javascript:;" onclick="CoinWidget.hide('+instance+');">x</a><label>'+text_label+'</label><input title="Bitcoin Address" type="text" onclick="$(this).select();" value="'+CoinWidget.instance_config[instance].address+'"/>'+ext_html+'<a class="COINWIDGET_WINDOW_CREDITS" href="http://coinwidget.com/?widget" target="_blank">CoinWidget.com</a><br/></div>');
		$('body').append($window);
		if (!CoinWidget.instance_config[instance].hide_qr) {
			$("[data-coinwidget-window="+instance+"] .COINWIDGET_QR").hover(function(){
				if ($("[data-coinwidget-window="+instance+"] .COINWIDGET_QR_LARGE").attr('src') != 'http://coinwidget.com/qr/'+CoinWidget.instance_config[instance].address )
				$("[data-coinwidget-window="+instance+"] .COINWIDGET_QR_LARGE").attr('src','http://coinwidget.com/qr/'+CoinWidget.instance_config[instance].address);
				$("[data-coinwidget-window="+instance+"] .COINWIDGET_QR_LARGE").show();
			},function(){
				$("[data-coinwidget-window="+instance+"] .COINWIDGET_QR_LARGE").hide();
			});
		}
	},

	/** show dialog */
	show: function(launcher){
		$instance = $(launcher).attr('data-instance');
		CoinWidget.build_window($instance);		
		if ($("[data-coinwidget-window="+$instance+"]").is(':visible')) {
			CoinWidget.hide($instance);
			return;
		}	
		$obj = $(launcher);
		$pos = $obj.offset();
		$("[data-coinwidget-window="+$instance+"]").css({'top':$pos.top+$obj.outerHeight()+8,'left':$pos.left}).show();
		setTimeout(function(){$("[data-coinwidget-window="+$instance+"]:hidden").show();},150);

		
	},

	hide: function(instance) {
		$("[data-coinwidget-window="+instance+"]").hide();
	}

};
if (typeof CoinWidgetInstance !== 'number'){
	var CoinWidgetInstance = 1;
} else {
	CoinWidgetInstance++;
}

CoinWidget.init(CoinWidget_Config);
document.write('<span id="CoinWidgetButton_'+CoinWidgetInstance+'" data-instance="'+CoinWidgetInstance+'" class="COINWIDGET_BUTTON"></span>');