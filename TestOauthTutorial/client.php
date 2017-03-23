<?php

require 'OAuth.php';
 
$key = '1dfba3d8a4cccb57f1e4f3e94b61607d4';
$secret = 'cb33978e08e461f7f2ff4929b884e5fd';
$consumer = new OAuthConsumer($key, $secret);
 
 
//$api_endpoint ='http://<host_url>/getKeyStatus';
$api_endpoint ='http://10.10.2.24/omkar/oauth/myOauth/server.php';
$data = json_encode(array('ProductKey'=>'18KB8NS764D634341Z55','hbns'=>'18KB8NS764D634341Z55','tt'=>'5'));

//handle request in 'server' block above

 
//use oauth lib to sign request
$req = OAuthRequest::from_consumer_and_token($consumer, null, "POST", $api_endpoint, array());

 
$sig_method = new OAuthSignatureMethod_HMAC_SHA1();


$req->sign_request($sig_method, $consumer, null);//note: double entry of token
 

 $headers = array( 'Accept: application/json', 'Content-Type: application/json', $req->to_header() );
//get data using signed url
$ch = curl_init($api_endpoint);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data); 
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
  
echo $responsefromwcf = curl_exec($ch);
 
curl_close($ch);
?>