document.addEventListener("DOMContentLoaded", function() {
    var intervalID = window.setInterval(GetData, 500);
}, false);

function onPlayerStateChange(event) {}

var PlayerData;

function UpdatePlayer() {
    if(Math.abs(PlayerData["PlayerTimestamp"] - player.getCurrentTime()) > 0.25) {
        player.seekTo(PlayerData["PlayerTimestamp"]);
    }

    if (PlayerData["PlaybackRate"] != player.getPlaybackRate()) {
        player.setPlaybackRate(PlayerData["PlaybackRate"]);
    }

    if (PlayerData["Muted"] == true) {
        player.mute();
    } 
    else {
        player.unMute();
    }

    switch(PlayerData["PlayerState"]) {
        case -1:
            player.stopVideo();
            break;
        case 0:
            player.stopVideo();
            break;
        case 1:
            player.playVideo();
            break;
        case 2:
            player.pauseVideo();
            break;
        case 3:
            player.pauseVideo();
            break;
    }
}

function GetData() {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            PlayerData = JSON.parse(this.responseText);
            UpdatePlayer();
        }
    };

    xmlhttp.open("GET","GetData.php", true);
    xmlhttp.send();
}