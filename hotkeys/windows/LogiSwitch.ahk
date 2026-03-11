; AutoHotkey v2
; Run this script from inside the cloned repo.

repoDir := A_ScriptDir "\..\.."
switchDefault := repoDir "\scripts\windows\switch-default.cmd"

^F1::
{
    Run('"' switchDefault '"', repoDir, "Hide")
}
