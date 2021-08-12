import NBA.nba_dt
import NBA.prepare
import S2.player_dt
import PyQL.py_tools

class Player(S2.player_dt.Player,NBA.nba_dt.NBA_DT):

    def __init__(self,data_dirs,name):
        self.name = name
        self.games_prepare = NBA.prepare
        NBA.nba_dt.NBA_DT.__init__(self, data_dirs=data_dirs,name=name)

    def repair_names(self):
        print "NBA player prepare"

        # try to fix single letter first names
        sdql = "Unique((name,team,season))@1"
        res = self.query(sdql,_qt="player")
        print "NBA player prepare got",res
