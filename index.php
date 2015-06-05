<html>
<title>ECAL PFG plots</title>
<body>

<center>
<h1>FE STATUS BITS</h1>
<a href="downloads">ROOT files</a><br>
<a href="Plots">Plots</a><br>


<?php

foreach (scandir("plots") as $s){
 if ($s == "." or $s == ".." or $s == ".htaccess"){
  continue;
 }
 echo "<img src='plots/$s'><br>";
}

?>
</center>
</body>
</html>
