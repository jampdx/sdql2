import WNBA.wnba_dt
import WNBA.prepare
import S2.player_dt


class Player(S2.player_dt.Player,WNBA.wnba_dt.WNBA_DT):

    def __init__(self,data_dirs,name):
        self.name = name
        self.games_prepare = WNBA.prepare
        WNBA.wnba_dt.WNBA_DT.__init__(self, data_dirs=data_dirs,name=name)
