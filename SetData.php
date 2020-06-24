<?php
    file_put_contents("PlayerData.json", "{\"PlayerTimestamp\":" . $_POST["PlayerTimestamp"] . ", \"PlayerState\":" . $_POST["PlayerState"] . ", \"PlaybackRate\":" . $_POST["PlaybackRate"] . ", \"Muted\":" . $_POST["Muted"] . "}");
?>