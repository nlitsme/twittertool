# twitter tool

A commandline tool for querying twitter.

Usage
=====

First you will have to create a configuration file in your `HOME` directory called `.twitterrc`, with the following:

    [authentication]
    auth=----40-char-authtoken------

You can get this authtoken by several means, most easily by looking at the 'site-storage' with the browser's debug-console, and find the `auth_token` cookie.
it should be a 40 character hex string ( consisting of digits 0-9 and letters a-f )

Then use this tool for example:

    python3 tw.py --tweets elonmusk

This will give:

    None elonmusk / Elon Musk / 44196397	
    insn TimelineClearCache
    insn TimelineAddEntries
    1646361204401799168 Thu Apr 13 03:54:33 +0000 2023 RT @TexasLindsay_: @elonmusk @zerohedge PBS begging on twitter over the years to have people support their federal funding. https://t.co/WQ…
    1646225066345234437 Wed Apr 12 18:53:35 +0000 2023 https://t.co/krmcbhutr0
         https://pbs.twimg.com/media/FtiQ-MIagAAnqfm.jpg
    1646303780189900800 Thu Apr 13 00:06:22 +0000 2023 NPR literally says Federal funding is *essential* on their website right now at https://t.co/QA8TUZxmNO
    ...


The complete usage info:

    usage: tw.py [-h] [--followers] [--following] [--tweets] [--uidinfo] [--userinfo] [--tweetinfo] [--media] [--debug]
                 [--config CONFIG] [--authtoken AUTHTOKEN]
                 [ARGS ...]

    twitter tool

    positional arguments:
      ARGS                  which items to list

    options:
      -h, --help            show this help message and exit
      --followers           list followers for the specified user
      --following           list following for the specified user
      --tweets              list tweets for the specified user
      --uidinfo             print info by userid
      --userinfo            print info by screenname
      --tweetinfo           print info for a tweetid
      --media               list media for the specified user
      --debug               debug http requests
      --config CONFIG       specify configuration file.
      --authtoken AUTHTOKEN


TODO
====

 * add support for search
 * implement user authentication, so you don't have to copy the auth cookie.


Author:
======
Willem Hengeveld

itsme@xs4all.nl

