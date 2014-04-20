$(document).ready(function() {

  var digest = $('#digest');
  var timestamp = $('#timestamp');
  var blockchain_message = $('#blockchain_message');
  var icon = $('#icon');
  var certify_message = $('#certify_message');
  var confirmed_message = $('#confirmed_message');
  var confirming_message = $('#confirming_message');
  var ladd1 = $('#ladd1');
  var radd1 = $('#radd1');
  var ladd2 = $('#ladd2');
  var radd2 = $('#radd2');
  var tx = $('#tx');
  var padd = $('#payment_address');

  var pathname = window.location.pathname;
  var uuid = pathname.split('/')[2];

  var postData = {
    'd': uuid
  };

  var onFail = function() {
    digest.html(translate('Error!'));
    timestamp.html(translate('We couldn\'t find that document'));
  };

  var onSuccess = function(data) {
    if (data.success == true) {
      data = data.doc;
      confirming_message.hide();
      blockchain_message.show();
      digest.html(data.digest);
      var times = translate('Registered in our servers since:') + ' <strong>' + data.timestamp + '</strong><br /><br />';
      if (data.blockstamp) {
        times += translate('Registered in the bitcoin blockchain since:') + ' <strong>' + data.blockstamp + '</strong> (' + translate('transaction timestamp') + ')<br /><br />';
      }
      timestamp.html(times);
      var msg = '';
      var clz = '';
      var in_blockchain = !data.pending && data.tx && data.tx.length > 1;
      var img_src = '';
      if (in_blockchain) {
        msg = translate('Document proof embedded in the Bitcoin blockchain!');
        clz = 'alert-success';
        img_src = 'check.png';
        tx.html('<a href="https://blockchain.info/tx/' + data.tx + '"> ' + translate('Transaction') + ' ' + data.tx + '</a>');
        ladd2.html('<a href="https://blockchain.info/address/' + data.ladd + '">' + data.ladd + '</a>');
        radd2.html('<a href="https://blockchain.info/address/' + data.radd + '">' + data.radd + '</a>');
        confirmed_message.show();
      } else if (!data.pending) {
        msg = translate('Payment being processed. Please wait while ' + 
          'the bitcoin transaction is confirmed by the network.');
        clz = 'alert-warn';
        img_src = 'wait.png';
        ladd1.html('<a href="https://blockchain.info/address/' + data.ladd + '">' + data.ladd + '</a>');
        radd1.html('<a href="https://blockchain.info/address/' + data.radd + '">' + data.radd + '</a>');
        confirming_message.show();
        $.post('/api/document/check', postData, onCheckSuccess, 'json');
      } else {
        msg = translate('Document proof not yet embedded in the bitcoin blockchain.');
        clz = 'alert-danger';
        img_src = 'warn.png';
        var qrcode = new QRCode('qr', {
          text: data.payment_address,
          width: 256,
          height: 256,
          correctLevel : QRCode.CorrectLevel.H
        });
        askPaymentReceived();
        padd.text(data.payment_address);
        certify_message.show();
      }
      blockchain_message.html(msg);
      blockchain_message.addClass(clz);

      icon.html('<img src="/static/img/' + img_src + '" />');
    } else {
      onFail();
    }
  };

  var onCheckSuccess = function(data) {
    if (data.success == true) {
      askDetails();
    } else {}
  };
  
  var onPaymentSuccess = function(data) {
    if (data.success == true) {
      if (data.payment) {
        location.reload();
      } else {
        setTimeout(askPaymentReceived, 10000);
      }
    } else {
      onFail();
    }
  };

  var askDetails = function() {
    $.post('/api/document/get', postData, onSuccess, 'json').fail(onFail);
  };

  var askPaymentReceived = function() {
    $.post('/api/document/payment', postData, onPaymentSuccess, 'json').fail(onFail);
  };

  askDetails();

  


});
