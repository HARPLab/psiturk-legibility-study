# psiturk-harp-template

Template for creating a new PsiTurk experiment for data collection.

To use, please:
* Clone this directory to a repository on eve.pr
* `cd` to within this directory
* Type the command `psiturk`
* Once within the psiturk terminal, type `server on`. You should see the server status successfully update
* The public view of your website can be seen [here](http://dashboard.personalrobotics.ri.cmu.edu/)

To check if another PsiTurk project is already running there, use `ps aux | grep psiturk`.
`pkill gunicorn` kills all servers of this kind on the machine, which can be verified with the previous command.

Please remember to use relative paths only when accessing resources, otherwise when mirroring your local site, the server will get confused and be unable to find your content.

When prompted for a login while attempting to view user data, please use `harplab` and the lab standard password.

To use this template, please create your own repository based on this one, do not update this template unless there is a change you expect all future users to want (ex, updated HARP consent form or logo).

Quickstart Notes:
* Logged data can be found at the host url + '/view_data', behind lab password protected login.
* The folder "templates" contains the html pages of a study where the bulk of your work will take place
* If you would like to manually query user data, that can be found in `participants.db`
