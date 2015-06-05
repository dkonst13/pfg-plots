<html>
<title>ECAL PFG plots</title>
<body>

<center>
<?php

foreach (scandir("plots") as $s){
 if ($s == "." or $s == ".."){
  continue;
 }
 echo "<img src='plots/$s'><br>";
}

?>
</center>
</body>
</html>
