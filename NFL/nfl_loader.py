# need a file that has the database at top level
# consider mlb_database for mlb + trends.

from NFL.nfl_dt import loader
TOP_DATA_DIR = "/home/jameyer/S2/NFL/Data"

nfl  = loader()

def dump_for_flat_file():
    import os
    out = []
    fields = "date,site,season,t:team,o:team,t:points,o:points,t:division,o:division,t:passes,o:passes,t:interceptions,o:interceptions,t:passing yards,o:passing yards,t:rushes,o:rushes,t:rushing yards,o:rushing yards,line,total"
    res = nfl.query("Column((%s),format='''lambda x:'\t'.join(map(str,x))''')@2010>=season>=1005 and not _i%%2"%fields)[0]
    out.append(fields.replace(",","\t") )
    for i in range(len(res[0])):
        out.append("%s"%res[0].format(res[0][i]))
    #print "\n".join(out+[''])
    open(os.path.join(TOP_DATA_DIR,"nfl.tab"),'w').write("\n".join(out+['']))
        
if __name__ == "__main__":
    dump_for_flat_file()
