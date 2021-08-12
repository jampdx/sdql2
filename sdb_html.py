import random

if random.choice([1,2]) == 1:
    right_header = "<center><a href=http://KillerCappers.com><img src='/Images/kc_banner_medium.png' border=0>"
    right_header += "<BR><font size=-1><nobr>Winning Picks, Guaranteed</nobr></font></a></center>"
else:
    right_header = "<center><a href=http://KillerSports.com><img src='/Images/ks_banner_medium.png' border=0>"
    right_header += "<BR><font size=-1><nobr>Information you need to win</nobr></font></a></center>"

left_header = """
<script type="text/javascript"><!--
google_ad_client = "pub-3254088164478059";
google_ad_width = 125;
google_ad_height = 125;
google_ad_format = "125x125_as";
google_ad_channel ="6156971486";
google_ad_type = "text";
google_color_border = "CCCCCC";
google_color_bg = "FFFFFF";
google_color_link = "000000";
google_color_url = "666666";
google_color_text = "333333";
//--></script>
<script type="text/javascript"
  src="http://pagead2.googlesyndication.com/pagead/show_ads.js">
</script>                   
"""

center_header = """<a href=http://SportsDataBase.com STYLE='text-decoration: none'>
                         <font size=+2 color=FF00FF>
                             <b>S p o r t s D a t a B a s e . c o m</b>
                         </font></a>
                         <BR>
               <a href=http://SDQL.com><font color=0000FF>                         
          <em><u>a sports data query language (SDQL &copy;) consultancy</a></u></em></font></a><p>
              <font size=-1>Permission is given to  quote trends found on SportsDataBase.com provided
                   that a reference and a link to SportsDataBase.com is provided. E.g.:
                   <a href=http://SportsDataBase.com/>Trend found on SportsDataBase.com</a></font>
                         """


top = "<TABLE><TR>"
top += "<TD width=125>%s</TD>"%left_header
top += "<td align=center valign=top>%s</TD>"%center_header
top += "<TD width=125>%s</TD>"%right_header
top += "</TR></TABLE>"
