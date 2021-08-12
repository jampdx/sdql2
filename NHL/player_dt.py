import NHL.nhl_dt
import NHL.prepare
import S2.player_dt
NHL_DT = NHL.nhl_dt.NHL_DT



class Player(S2.player_dt.Player,NHL_DT):

    def __init__(self,data_dirs=[],name=''):
        self.name = name
        self.games_prepare = NHL.prepare
        NHL_DT.__init__(self, data_dirs=data_dirs,name=name)
