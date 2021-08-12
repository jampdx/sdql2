from NBA.nba_dt import loader
from S2.directory import DATA_DIR
DATA_DIR = DATA_DIR("nba")

nba  = loader()



def dump_for_flat_file():
    import os
    out = []
    fields = "date,site,season,t:team,o:team,t:points,o:points,t:division,o:division,t:field goals made,o:field goals made,t:field goals attempted,o:field goals attempted,t:free throws made,o:free throws made,t:three pointers made,o:three pointers made,t:fouls,o:fouls,t:assists,o:assists,t:turnovers,o:turnovers,t:blocks,o:blocks,t:quarter scores,o:quarter scores,t:rebounds,o:rebounds,t:steals,o:steals,line,total"
    res = nba.query("Column((%s),format='''lambda x:'\t'.join(map(str,x))''')@2010>=season>=1005 and not _i%%2"%fields)[0]
    out.append(fields.replace(",","\t") )
    for i in range(len(res[0])):
        out.append("%s"%res[0].format(res[0][i]))
    #print "\n".join(out+[''])
    open(os.path.join(DATA_DIR,"nba.tab"),'w').write("\n".join(out+['']))
        
if __name__ == "__main__":
    dump_for_flat_file()
