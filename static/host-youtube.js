var oldData;

document.addEventListener("DOMContentLoaded", function() {
    var intervalID = window.setInterval(SetData, 500);
}, false);

function onPlayerStateChange(event) {
    SetData();
}

function SetData() {
    var dataToSet = JSON.stringify({
            PlayerTimestamp: player.getCurrentTime(),
            PlayerState: player.getPlayerState(),
            PlaybackRate: player.getPlaybackRate(),
            Muted: player.isMuted()
        });

    if (oldData != dataToSet) {
        oldData = dataToSet;

        $.ajax({
        type: "POST" ,
            url: "/host-processor",
            data: dataToSet,
            success: function(data) {},
            error: function(data) {
                if (data.responseText != undefined) {
                    alert("Error: " + data.responseText);
                }
            }
        });
    }
}

