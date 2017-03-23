<?php 
/*require 'OAuth.php';
 
$key = '123344';
$secret = '2345';
// echo "cfsdfsf"; exit;
$method = $_SERVER['REQUEST_METHOD'];
  $uri = 'http://'.$_SERVER['SERVER_NAME'].':'.$_SERVER['SERVER_PORT'].$_SERVER['REQUEST_URI'];
  $sig = $_GET['oauth_signature'];
  // print_r($_GET); exit;
  $consumer = new OAuthConsumer($_GET['oauth_consumer_key'], $secret);
  $sig_method = new OAuthSignatureMethod_HMAC_SHA1;
 
// print_r($sig_method); exit;
  $req = new OAuthRequest($method, $uri);
   echo "<pre>";print_r($req); 
  //token is null because we're doing 2-leg
  $authenticated = $sig_method->check_signature($req, $consumer, null, $sig );
echo "auth=".$authenticated; exit;


*/
/*require 'OAuth.php';
//$consArray = array("123344"=>"2345");
$consArray = array("dfba3d8a4cccb57f1e4f3e94b61607d4"=>"cb33978e08e461f7f2ff4929b884e5fd");
	$req =  OAuthRequest::from_request();
	echo "<pre>"; print_r($req); 
	echo $conskey = $req->get_parameter('oauth_consumer_key');
	$sig = $req->get_parameter('oauth_signature');	
	$consumer = new OAuthConsumer($conskey, $consArray[$conskey]);
	$sig_method = new OAuthSignatureMethod_HMAC_SHA1;
    //token is null because we're doing 2-leg
        echo "Request: - ".$req."<br>";
        $authenticated = $sig_method->check_signature($req, $consumer, null, $sig );
	echo "auth=== ".$authenticated;
        echo "<br>";
	if($authenticated==1)
	{
	echo " YES ".$authenticated;
	}else
	{
	  echo "NO";
	}*/
require 'OAuth.php';
$consArray = array("dfba3d8a4cccb57f1e4f3e94b61607d4"=>"cb33978e08e461f7f2ff4929b884e5fd");
	$req =  OAuthRequest::from_request();	
	$conskey = $req->get_parameter('oauth_consumer_key');
	$sig = $req->get_parameter('oauth_signature');	
        $consumer = new OAuthConsumer($conskey, '12345');
        if(isset($consArray[$conskey])){
	$consumer = new OAuthConsumer($conskey, $consArray[$conskey]);
        }        
	$sig_method = new OAuthSignatureMethod_HMAC_SHA1;    
        $authenticated = $sig_method->check_signature($req, $consumer, null, $sig );
	if($authenticated==1)
	{
            echo '{"status":"SUCCESS"}';
            
	}else
	{
            echo'{"status":"FAIL", "errorCode": "ERR106"}';
	}        
?>