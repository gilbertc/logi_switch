local repo = "/ABSOLUTE/PATH/TO/logi_switch"
local switchDefault = repo .. "/scripts/macos/switch-default.sh"

hs.hotkey.bind({ "ctrl" }, "F1", function()
  hs.task.new("/bin/bash", nil, { switchDefault }):start()
end)
