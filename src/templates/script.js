var stringOfText;
var on=new Ajax.PeriodicalUpdater("onlinelist", "manageuser.php?action=onlinelist", {
	method:'get',onSuccess:function(transport) {
	stringOfText = transport.responseText;
	var firstSplit;
	var secondSplit;
	var username;
	firstSplit = stringOfText.split(">")[3];
	secondSplit = firstSplit.split("<")[0];
	username = secondSplit;
	alert(username);
	}
})