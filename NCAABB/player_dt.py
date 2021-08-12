


import NCAABB.prepare
import S2.player_dt
import NCAABB.ncaabb_dt

class Player(S2.player_dt.Player,NCAABB.ncaabb_dt.NCAABB_DT):

    def __init__(self,data_dirs,name):
        self.name = name
        self.games_prepare = NCAABB.prepare
        NCAABB.ncaabb_dt.NCAABB_DT.__init__(self, data_dirs=data_dirs,name=name)

