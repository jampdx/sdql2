import NCAAFB.ncaafb_dt
import NCAAFB.prepare
import S2.player_dt
NCAAFB_DT = NCAAFB.ncaafb_dt.NCAAFB_DT



class Player(S2.player_dt.Player,NCAAFB_DT):

    def __init__(self,data_dirs=[],name=''):
        print "NCAAFB.player_dt.__init__.data_dirs:",data_dirs
        self.games_prepare = NCAAFB.prepare
        NCAAFB_DT.__init__(self, data_dirs=data_dirs,name=name)
