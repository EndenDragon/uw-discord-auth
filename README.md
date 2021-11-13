# uw-discord-auth
Authentication for UW Discords

## Installation
1. Clone project within `public_html` (if ovid) and `cd` into the directory.
2. `python3 -m pip install -r requirements.txt -t pypackages/`
3. Remove dataclasses from pypackages `rm pypackages/dataclasses.py`
    - It currently crashes the site due to python version differences between server and web execution platform
4. Copy `config.example.py` into `config.py` and edit the values. You may obtain Discord IDs by [enabling Developer Mode](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-) and then right clicking the relevant portion of the Discord UI to access Copy ID context menu option.
5. Edit .htaccess `RewriteRule` portion to your url. For instance, if the `application.cgi` file is located within `/rc00/d00/jkzhang/public_html/uw-discord-auth` directory (`pwd` command output on ovid), the .htaccess RewriteRule will contain `/jkzhang/uw-discord-auth/application.cgi/`.
6. Visit the [Discord Developers portal](https://discordapp.com/developers/applications/me), select your bot, and proceed to the OAuth2 tab. Modify and add the following redirect url entry: `https://staff.washington.edu/jkzhang/uw-discord-auth/callback`. Modify this url so that the callback url is located to your installation.
