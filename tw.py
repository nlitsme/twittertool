import re
import urllib.request
import urllib.parse
import http.cookiejar
import json
import time
from datetime import datetime, timezone, timedelta
"""
commandline tool for getting info from twitter:
    - tweets by an account
    - media tweeted by an account
    - followers of an account
    - users followed of an account
    - info for a specific screen-name
    - info for a specific user-id
    - info for a specific tweet-id

todo:
    - add support for twitter search
      using: https://api.twitter.com/2/search/adaptive.json
    - implement user authentication.


Author: Willem Hengeveld, itsme@xs4all.nl
"""

def get(x, *path):
    """
    get item from nested dict-of-dict struct
    """
    for p in path:
        if not x:
            break
        x = x.get(p)
    return x

def addCookie(cj, name, value, domain):
    """
    helper to add a cookie to the http-cookie-jar
    """
    cj.set_cookie(http.cookiejar.Cookie(
            version=0, name=name, value=value,
            port=None, port_specified=False,
            domain=domain, domain_specified=True, domain_initial_dot=True,
            path="/", path_specified=True,
            secure=False, expires=None, discard=False,
            comment=None, comment_url=None, rest={}))

def getCookie(cj, name):
    """
    helper to get a cookie from the http-cookie-jar
    """
    for c in cj:
        if c.name == name:
            return c.value


class Twitter:
    """
    class wrapping the twitter api
    """
    def __init__(self, args):
        self.args = args
        self.baseurl = "https://api.twitter.com/graphql/"

        # initial csrf token: 0*32, gets updated from the 'ct0' cookie after first request
        self.csrftoken = "0" * 32

        self.cj = http.cookiejar.CookieJar()
        addCookie(self.cj, "ct0", self.csrftoken, ".twitter.com")
        addCookie(self.cj, "auth_token", self.args.authtoken, ".twitter.com")

        # the auth-token is obtained from the final https://api.twitter.com/1.1/onboarding/task.json step

        handlers = [urllib.request.HTTPCookieProcessor(self.cj)]
        if args.debug:
            handlers.append(urllib.request.HTTPSHandler(debuglevel=1))
        self.opener = urllib.request.build_opener(*handlers)

    def logprint(self, *args):
        if self.args.debug:
            print(*args)

    def httpreq(self, url, data=None):
        """
        Generic http request function.
        Does a http-POST when the 'data' argument is present.

        Adds the nesecesary csrf and auth headers.
        """
        self.logprint(">", url)
        if data and type(data)==str:
            data = data.encode('utf-8')

        hdrs = { }
        if data and data[:1] in (b'{', b'['):
            hdrs["Content-Type"] = "application/json"

        # note: the bearer never changes, it is defined in https://abs.twimg.com/responsive-web/client-web/main.5ae1596a.js
        self.bearer = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

        # the auth token changes with each login.
        if self.bearer:
            hdrs['Authorization'] = 'Bearer ' + self.bearer
        if self.csrftoken:
            hdrs['x-csrf-token'] = self.csrftoken

        req = urllib.request.Request(url, headers=hdrs)
        kwargs = dict()
        if data:
            kwargs["data"] = data

        try:
            response = self.opener.open(req, **kwargs)
        except urllib.error.HTTPError as e:
            self.logprint("!", str(e))
            response = e

        data = response.read()
        # get updated csrf token
        self.csrftoken = getCookie(self.cj, "ct0")
        if response.headers.get("content-type", '').find("application/json")>=0:
            js = json.loads(data)
            self.logprint(js)
            self.logprint()
            return js
        self.logprint(data)
        self.logprint()
        return data

    def apiurl(self, apiname):
        match apiname:
            case "TweetDetail":
                return self.baseurl+"VaihYjIIeVg4gfvwMgQsUA/TweetDetail"
            case "ProfileSpotlightsQuery":
                return self.baseurl+"9zwVLJ48lmVUk8u_Gh9DmA/ProfileSpotlightsQuery"
            case "UserByRestId":
                return self.baseurl+"gUIQEk2xDGzQTX8Ii0Yesw/UserByRestId"
            case "UsersByRestIds":
                return self.baseurl+"zaTqxMKJ1kzpOxhVbYr1YQ/UsersByRestIds"
            case "UserByScreenName":
                return self.baseurl+"rePnxwe9LZ51nQ7Sn_xN_A/UserByScreenName"
            case "UserTweets":
                return self.baseurl+"rCpYpqplOq3UJ2p6Oxy3tw/UserTweets"
            case "UserMedia":
                return self.baseurl+"ghc-7mU9EvRC54PiccAsCA/UserMedia"
            case "Followers":
                return self.baseurl+"EcJ6iHzKpwDjpC0Dm1Gkhw/Followers"
            case "Following":
                return self.baseurl+"wh5eBj-w6PPSzTSbgrlHzw/Following"

    def getprofile(self, username):
        v = {"screen_name":username}
        f = None
        return self.httpreq(self.apiurl("ProfileSpotlightsQuery") + "?" + urllib.parse.urlencode(self.makeparams(v, f)))

    def makeparams(self, v, f):
        """
        create the params dictionary passed with the graphql-GET request
        """
        params = { }
        if v is not None:
            params["variables"] = json.dumps(v, separators=(',', ':'))
        if f is not None:
            params["features"] = json.dumps(f, separators=(',', ':'))
        return params

    def makefeatures(self):
        """
        make the features dict.
        note that this has the features for all the requests, not all are needed for each req.
        """
        return {
            "responsive_web_twitter_blue_verified_badge_is_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": False,
            "verified_phone_label_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "vibe_api_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "freedom_of_speech_not_reach_appeal_label_enabled": False,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
            "interactive_text_enabled": True,
            "responsive_web_text_conversations_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        }

    def gettweets(self, uid, cursor=None, type="UserTweets"):
        """
        Gets tweets of the sepcified type for the given uid.
        type: UserTweetsAndReplies or UserMedia or UserTweets
        """
        v = {
            "includePromotedContent":True,
            "withQuickPromoteEligibilityTweetFields":True,
            "withSuperFollowsUserFields":True,
            "withDownvotePerspective":False,
            "withReactionsMetadata":False,
            "withReactionsPerspective":False,
            "withSuperFollowsTweetFields":True,
            "withVoice":True,
            "withV2Timeline":True,
            "withClientEventToken":False,
            "withBirdwatchNotes":False,

            "userId":uid,
            "count":40,
        }
        if cursor:
            v["cursor"] = cursor
        f = self.makefeatures()
        return self.httpreq(self.apiurl(type) + "?" + urllib.parse.urlencode(self.makeparams(v, f)))

    def getmedia(self, uid, cursor=None):
        """
        gets media for the specified uid.
        """
        return self.gettweets(uid, cursor, type="UserMedia")

    def getfollowers(self, uid, cursor):
        """
        gets followers for the specified uid
        """
        v = {
            "includePromotedContent":False,
            "withSuperFollowsUserFields":True,
            "withDownvotePerspective":False,
            "withReactionsMetadata":False,
            "withReactionsPerspective":False,
            "withSuperFollowsTweetFields":True,
            "userId":uid,
            "count":20,
        }
        if cursor:
            v["cursor"] = cursor
        f = self.makefeatures()
        return self.httpreq(self.apiurl("Followers") + "?" + urllib.parse.urlencode(self.makeparams(v, f)))

    def getfollowing(self, uid, cursor):
        """
        gets following for the specified uid
        """
        v = {
            "includePromotedContent":False,
            "withSuperFollowsUserFields":True,
            "withDownvotePerspective":False,
            "withReactionsMetadata":False,
            "withReactionsPerspective":False,
            "withSuperFollowsTweetFields":True,
            "userId":uid,
            "count":20,
        }
        if cursor:
            v["cursor"] = cursor

        f = self.makefeatures()
        return self.httpreq(self.apiurl("Following") + "?" + urllib.parse.urlencode(self.makeparams(v, f)))

    def printprofile(self, p):
        """
        print info from the user profile.
        """
        r = get(p, "user_results", "result") or get(p, "data", "result") or get(p, "data", 'user_result_by_screen_name', "result") or get(p, "data", 'user', "result")
        if not r:
            # note: this probably happens for deleted accounts
            print("??", p)
            return

        sn = get(r, "legacy", "screen_name")
        n = get(r, "legacy", "name")
        id = get(r, "rest_id")
        desc = get(r, "legacy", "description") or ""
        since = get(r, "legacy", "created_at")
        print(f"{since} {sn} / {n} / {id}\t{desc}")

    def printtli(self, item):
        """
        print timeline info item.
        """
        match get(item, "__typename"):
            case "TimelineTweet":
                id = get(item, "tweet_results", "result", "rest_id")
                txt = get(item, "tweet_results", "result", "legacy", "full_text")
                frm = get(item, "tweet_results", "result", "legacy", "created_at")
                print(f"{id} {frm} {txt}")
                media = get(item, "tweet_results", "result", "legacy", "entities", "media")
                if media:
                    for m in media:
                        print("\t", get(m, "media_url_https"))
            case "TimelineUser":
                self.printprofile(item)
            case "TimelineTimelineCursor":
                # TODO - use cursor
                pass
            case _:
                # TimelineTombstone
                print("unsupported-tli", get(item, "__typename"))
                print(item)

    def printitem(self, item):
        """
        Print timeline items
        {
            entryId: "<type>-<id>"
            sortIndex: "<number>"
            content: {
                entryType + __typename : TimelineTimelineItem
                itemContent: {
                    itemType + __typename: TimelineTweet
                    tweet_results: {
                      result: {
                        legacy: {
                          full_text: "...",
                       },
                     }
                   }                    
                }
            }
        }
        """
        t = get(item, "content", "__typename")
        match t:
            case "TimelineTimelineItem":
                c = get(item, "content", "itemContent")
                self.printtli(c)
            case "TimelineTimelineModule":
                for i in get(item, "content", "items"):
                    self.printtli(get(i, "item", "itemContent"))
            case _:
                print("unsupported", t)

    def dump(self, uid, getter):
        """
        iterate over some api, using the cursor.
        """
        cursor = None
        done = False
        while not done:
            time.sleep(1.5)
            res = getter(uid, cursor)
            if type(res) != dict:
                print(res)
                break
            if res.get('errors'):
                print(res)
                break
            res = get(res, "data", "user", "result")
            tl = res.get("timeline_v2") or res.get("timeline")
            done = self.process_instructions(get(tl, "timeline", "instructions"))

    def process_instructions(self, instructions):
        done = False
        count = 0
        for i in instructions:
            print("insn", i.get("type"))
            if i.get("type") == "TimelineAddEntries":
                for e in i.get("entries"):
                    if get(e, "content", "entryType") == "TimelineTimelineCursor":
                        if get(e, "content", "cursorType") == "Bottom":
                            cursor = get(e, "content", "value")
                    else:
                        self.printitem(e)
                        count += 1
            elif i.get("type") == "TimelineTerminateTimeline":
                if i.get('direction') == 'Bottom':
                    done = True
        if count==0:
            done = True

    def getbyuid(self, uid):
        """
        get profile info by user-id
        """
        v = { "userId":uid, "withSuperFollowsUserFields":True }
        f = self.makefeatures()
        return self.httpreq(self.apiurl("UserByRestId") + "?" + urllib.parse.urlencode(self.makeparams(v, f)))

    def printuidinfo(self, uid):
        """
        print profile for the given uid
        """
        r = self.getbyuid(uid)
        self.printprofile(r)

    def getbyuser(self, user):
        """
        get profile by screen-name
        """
        v = { "screen_name":user, "withSuperFollowsUserFields":True }
        f = self.makefeatures()
        return self.httpreq(self.apiurl("UserByScreenName") + "?" + urllib.parse.urlencode(self.makeparams(v, f)))

    def printuserinfo(self, user):
        """
        print profile for the given screen-name
        """
        r = self.getbyuser(user)
        self.printprofile(r)

    def getbytweetid(self, id):
        """
        get tweet details by tweet/status-id
        
        note that since November 2010, status-id are basically a precise timestamp:

        status-id = (unixtime - '2010-11-04 01:41:54') * 1000 * 0x400000

        """
        v = {
            "focalTweetId":id,
            "withVoice":True,
            "withSuperFollowsUserFields":True,
            "withSuperFollowsTweetFields":True,
            "withReactionsPerspective":True,
            "withReactionsMetadata":True,
            "withDownvotePerspective":True,
            "withBirdwatchNotes":True,
            "includePromotedContent":True
        }
        f = self.makefeatures()
        return self.httpreq(self.apiurl("TweetDetail") + "?" + urllib.parse.urlencode(self.makeparams(v, f)))

    def printtweetinfo(self, id):
        """
        print tweet details by status-id
        """
        r = self.getbytweetid(id)
        self.process_instructions(get(r, "data", "threaded_conversation_with_injections", "instructions"))


def loadconfig(cfgfile):
    """
    Load config from .twitterrc
    """
    with open(cfgfile, 'r') as fh:
        txt = fh.read()
    txt = "[root]\n" + txt
    import configparser
    config = configparser.ConfigParser()
    config.read_string(txt)

    return config


def applyconfig(cfg, args):
    """
    Apply the configuration read from .twitterrc to the `args` dictionary,
    which is used to configure everything.
    """
    def add(argname, cfgname):
        if not getattr(args, argname) and cfg.has_option('authentication', cfgname):
            setattr(args, argname, cfg.get('authentication', cfgname))
    #add("bearer", "bearer")
    add("authtoken", "auth")
    #add("username", "user")
    #add("password", "pass")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='twitter tool')
    #parser.add_argument('--username', type=str, help='username')
    #parser.add_argument('--password', type=str, help='password')
    parser.add_argument('--followers', action='store_true', help='list followers for the specified user')
    parser.add_argument('--following', action='store_true', help='list following for the specified user')
    parser.add_argument('--tweets', action='store_true', help='list tweets for the specified user')
    parser.add_argument('--uidinfo', action='store_true', help='print info by userid')
    parser.add_argument('--userinfo', action='store_true', help='print info by screenname')
    parser.add_argument('--tweetinfo', action='store_true', help='print info for a tweetid')
    parser.add_argument('--media', action='store_true', help='list media for the specified user')
    parser.add_argument('--debug',  action='store_true', help=argparse.SUPPRESS)    # 'debug http requests'
    parser.add_argument('--config', default='~/.twitterrc', help=argparse.SUPPRESS) # 'specify configuration file.'
    parser.add_argument('--authtoken', type=str, help=argparse.SUPPRESS)
    parser.add_argument('ARGS', nargs='*', help='which items to list')
    args = parser.parse_args()

    if args.config.startswith("~/"):
        import os
        homedir = os.environ['HOME']
        args.config = args.config.replace("~", homedir)

    try:
        cfg = loadconfig(args.config)

        applyconfig(cfg, args)
    except Exception as e:
        print("Error in config: %s" % e)

    tw = Twitter(args)

    for u in args.ARGS:
        if args.uidinfo:
            tw.printuidinfo(u)
            continue
        if args.userinfo:
            tw.printuserinfo(u)
            continue
        if args.tweetinfo:
            tw.printtweetinfo(u)
            continue

        p = tw.getprofile(u)
        tw.printprofile(p)

        uid = get(p, "data", "user_result_by_screen_name", "result", "rest_id")
        if args.followers:
            tw.dump(uid, tw.getfollowers)
        if args.following:
            tw.dump(uid, tw.getfollowing)
        if args.tweets:
            tw.dump(uid, tw.gettweets)
        if args.media:
            tw.dump(uid, tw.getmedia)

if __name__ == '__main__':
    main()

