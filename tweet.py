import os,sys
from S2.directory import CLIENT_DIR
import PyQL.twitter_tools

def tweet_from(f):
    ff = os.path.join(CLIENT_DIR,f)
    if not os.path.isfile(ff):
        print "no file found at:",ff
        return
    trends = open(ff).readlines()
    if not trends:
        print "no trends found in:",ff
        return
    trend = trends[0]
    player = trend.split(' has ')[0]
    trends = filter(lambda x,p=player:p not in x,trends)
    open(ff,'w').write(''.join(trends))
    print "tweeting",trend
    PyQL.twitter_tools.tweet(trend)

if __name__ == "__main__":
    if len(sys.argv)>1:
        f = sys.argv[1].split('=')[-1]
        tweet_from(f)
