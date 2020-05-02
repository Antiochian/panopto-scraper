# panopto-scraper

Given a panopto folder URL, this script is able to automatically navigate through the various authentification checks and cookie requirements of Panopto, and dig through the source code in order to extract the raw .mp4 files of a whole folder of lecture videos. These mp4 files are then saved to disk in a specified folder.

![Demo](scraper.gif)

The script is somewhat specialised to my situation, due to the unusual Panopto set up my university has. Bizarrely, there is no way to actually log on to Panopto directly in my institution, you instead have to follow a special link which refers you to a custom login portal. This script uses said link and login portal to navigate the first authentification step, so I doubt it will be useful for anyone not at my university.

This probably could have been done headlessly with urllib/requests only, but I wanted to learn Selenium for unit-testing purposes and this seemed like a good excuse, so I used Selenium instead.

Example Usage
-----
Replace the data in SECRET.py with your own user info.
Set the "path" variable in line 38 to where you want to files to be saved to.

Run `python scraper.py`

How It Works
-----
The obstacles that had to be negotiated for this project can be laid out as such:
 1. The shibboleth login portal must be passed
 2. The target folder URL (supplied by user) must be navigated to and all subvideos must be found
 3. The raw .mp4 file must be downloaded
 
Item (1) is solved with a very straightforward use of CSS selectors to mimic a user and enter a username/password/etc.

Item (2) is similar but complicated by the fact that the subvideos are contained within a dynamic javascript element, and so can't just be parsed from the HTML source. To solve this the script pauses until it detects that this element has finished loading, then Selenium pulls the div contents as a DOM and gets the video metadata from there.

Item (3) is the most interesting. In order to be able to download a file from Panopto, it is not enough to just have the link. You also need:
 - A valid cookie from the authenticator proving you are logged in
 - A valid user agent
 - 6 other cookies, all intended to make sure you are an authorized human user
 - A one-time "Session ID" which is generated through means unclear to me but can be extracted from the redirect URL when you try and access the file for the first time.
 
Using Selenium to collect together all of the cookies, I then stored them in a dictionary and loaded them into a Requests session, which does the actual downloading. The download is streamwise, so that at any given point no more than 8KB of data is being loaded into memory - some of these files are very large, and I didn't want to risk clogging up the system memory.

The neat thing about doing the downloading step with a totally different driver/agent is that it allows for parallel processing - the single Selenium instance darts around gathering cookies and logging Session IDs, while multiple seperate instances of the Requests session are downloading simultaneously in the background.

However, some of these lecture series comprise 20-30 hours of footage, and I was concerned that running 30 seperate 1GB downloads within a few milliseconds of each other might be an unfair strain on the Panopto servers, so the script as it is now waits for each download to finish before embarking on a new one. Still a cool proof-of-concept though.

NB
----
The materials obtained in this manner should be purely used for personal use and not for distribution, depending on the End User License Agreement you have signed. The End User License Agreement I signed, for example, forbids distribution but specifically states that it *is* permissible to download a copy of a lecture video for purposes of private study and/or non-commercial research.
