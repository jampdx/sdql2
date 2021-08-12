import NFL.nfl_dt
import NFL.prepare
import S2.player_dt
NFL_DT = NFL.nfl_dt.NFL_DT



class Player(S2.player_dt.Player,NFL_DT):

    def __init__(self,data_dirs=[],name='', verbose=False):
        if verbose: print "NFL.player_dt.__init__.data_dirs:",data_dirs
        self.games_prepare = NFL.prepare
        NFL_DT.__init__(self, data_dirs=data_dirs,name=name, verbose=verbose)
