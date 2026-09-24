# Terminal steps for beginners

Use the terminal only when there is no way to do the step in the app or with your own file tools. When you can create the file yourself, do that instead and show the person where it went.

Write every step for the comfort level the person gave in the opening questions. If they skipped that question, ask once before the first terminal step: "Have you used the Terminal app before? Never, a little, or comfortable?" For "never", include how to open it.

## Opening the terminal
- Mac: press Command and Space, type Terminal, press Return.
- Windows: press the Windows key, type PowerShell, press Enter.
- Linux: usually Ctrl, Alt, and T together.
- Claude desktop and some other apps have a built-in terminal panel; if the person's app has one, point to it instead.

## Format for every command

1. One sentence: what this does, in plain words.
2. The exact command, alone in its own code block, ready to copy. One command per block. No `$` prompt in front.
3. What they should see if it worked.
4. What to do if they see something else (the most likely error and its fix), and "otherwise, copy what it printed and paste it here".

Example:

> This creates the folder where your helper's file will live. It does nothing else.
>
> ```bash
> mkdir -p ~/.claude/agents
> ```
>
> If it worked, you will see nothing at all, just a new line waiting for you. That is normal.
> If you see "Permission denied", stop and paste the message here.

## Backing up a settings file

Prefer your own file tools. If the person has to do it, give these two steps (Mac and Linux; adjust the file name):

> This makes a private backup folder in your home folder. It changes nothing else.
>
> ~~~bash
> mkdir -p ~/agent-builder-backups
> ~~~
>
> This copies your current settings there, with the date and time in the name so it never replaces an earlier backup.
>
> ~~~bash
> cp -n ~/.claude/settings.json ~/agent-builder-backups/claude-settings-$(date +%Y-%m-%d-%H%M%S).json
> ~~~
>
> This lists the backups so you can see the new one is there.
>
> ~~~bash
> ls -l ~/agent-builder-backups
> ~~~

On Windows PowerShell, the same three steps:

~~~powershell
New-Item -ItemType Directory -Force "$HOME\agent-builder-backups"
~~~

~~~powershell
$dest = "$HOME\agent-builder-backups\claude-settings-$(Get-Date -Format yyyy-MM-dd-HHmmss).json"; if (Test-Path $dest) { "A backup with this name already exists. Wait a second and run this again." } else { Copy-Item "$HOME\.claude\settings.json" $dest }
~~~

~~~powershell
Get-ChildItem "$HOME\agent-builder-backups"
~~~

Do not edit the original until the listing shows the new backup. Never back up into a project, repository, or cloud-synced folder. If the person's home folder itself is synced (for example, the whole profile is inside OneDrive), use a local folder they name instead. Never paste the file's contents into chat.

## Rules
- Never ask the person to paste a password, key, or token into chat. If a step needs one, tell them to enter it where the app asks for it, or in their password manager, and to type it only into the terminal prompt that asks for it.
- Never give a command that deletes, overwrites, or changes permissions without saying so first in plain words and offering a backup step.
- Never use `sudo` or run anything with administrator rights for a beginner's agent. If something seems to need it, stop and explain why.
- Never pipe a download straight into a shell.
- Use full paths or `~/` paths so it does not matter which folder the terminal is in.
- After each command, wait for the person to report back before giving the next one.
- If the person is on Windows, give PowerShell commands, not Mac ones.
