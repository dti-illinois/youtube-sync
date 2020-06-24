document.addEventListener("DOMContentLoaded", function() {
    var intervalID = window.setInterval(SetData, 500);
}, false);

function onPlayerStateChange(event) {
    SetData();
}

function SetData() {
    $.ajax({
    type: "POST" ,
        url: "SetData.php",
        data: ({
            PlayerTimestamp: player.getCurrentTime(),
            PlayerState: player.getPlayerState(),
            PlaybackRate: player.getPlaybackRate(),
            Muted: player.isMuted()
        }),
        success: function(data) {},
        error: function(data) {
            if (data.responseText != undefined) {
                alert("Error: " + data.responseText);
            }
        }
    });
}