JS = r'''
var _atsIdx = 0;
var _ouIdx = 0;
var _suIdx = 0;

$.extend( $.fn.dataTable.ext.oSort, {
	/*
	 * ATS sorting
	 */
	"ats-pre": function ( s ) {
      var matches = s.match(/([0-9]+?)\-([0-9]+?)\-([0-9]+?) \(([0-9\.\-]+?), ([0-9\.\-]+?)%\)/);
      
      return parseFloat( ( _atsIdx === 0 || _atsIdx === 1 ) ?
        matches[1] : matches[_atsIdx]
      );
	},

	"ats-asc": function ( x, y ) {
		return ((x < y) ? -1 : ((x > y) ? 1 : 0));
	},
	
	"ats-desc": function ( x, y ) {
		return ((x < y) ? 1 : ((x > y) ? -1 : 0));
	},
  
	/*
	 * OU sorting
	 */
	"ou-pre": function ( s ) {
      var matches = s.match(/([0-9]+?)\-([0-9]+?)\-([0-9]+?) \(([0-9\.\-]+?), ([0-9\.\-]+?)%\)/);
      
      return parseFloat( ( _ouIdx === 0 || _ouIdx === 1 ) ?
        matches[1] : matches[_ouIdx]
      );
	},

	"ou-asc": function ( x, y ) {
		return ((x < y) ? -1 : ((x > y) ? 1 : 0));
	},
	
	"ou-desc": function ( x, y ) {
		return ((x < y) ? 1 : ((x > y) ? -1 : 0));
	},
  
	/*
	 * SU sorting
	 */
	"su-pre": function ( s ) {
      var matches = s.match(/([0-9]+?)\-([0-9]+?) \(([0-9\.\-]+?), ([0-9\.\-]+?)%\)/);
      
      return parseFloat( ( _suIdx === 0 || _suIdx === 1 ) ?
        matches[1] : matches[_suIdx]
      );
	},

	"su-asc": function ( x, y ) {
		return ((x < y) ? -1 : ((x > y) ? 1 : 0));
	},
	
	"su-desc": function ( x, y ) {
		return ((x < y) ? 1 : ((x > y) ? -1 : 0));
	}
} );



$(document).ready(function() {
  // Set up a flag to tell the sort functions what data is needed
  // ATS header
  $('#example thead th').eq(1).find('span').click( function () {
    _atsIdx = $('span', this.parentNode).index( this );
  } );
  
  // OU header
  $('#example thead th').eq(2).find('span').click( function () {
    _ouIdx = $('span', this.parentNode).index( this );
  } );
  
  // SU header
  $('#example thead th').eq(3).find('span').click( function () {
    _suIdx = $('span', this.parentNode).index( this );
  } );
  
  $('#example').dataTable( {
    aoColumnDefs: [
      {
        asSorting: [ 'desc', 'asc' ],
        aTargets: [ 0 ]
      },
      {
        sType: 'ats',
        asSorting: [ 'desc', 'asc' ],
        aTargets: [ 1 ]
      },
      {
        sType: 'ou',
        asSorting: [ 'desc', 'asc' ],
        aTargets: [ 2 ]
      },
      {
        sType: 'su',
        asSorting: [ 'desc', 'asc' ],
        aTargets: [ 3 ]
      }
    ]
  } );
} );

'''

html = r'''
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    
    <title>DataTables live example</title>
    <style type="text/css">
      @import "/media/css/demo_page.css";
      @import "/media/css/demo_table.css";
      
      th>span { color: blue; }
      th>span:hover { text-decoration: underline; }
    </style>
    <script type="text/javascript" language="javascript" src="/media/js/jquery.js"></script>
    <script class="jsbin" src="http://datatables.net/download/build/jquery.dataTables.nightly.js"></script>
  </head>
  <body id="dt_example">
    <div id="container" style="width:960px">
      <h1>Live example</h1>

      <table cellpadding="0" cellspacing="0" border="0" class="display" id="example">
        
<thead><tr>
<th><span># games</span></th>
<th><span>ATS</span><BR><span>W</span>-<span>L</span>-<span>P</span> (<span>marg</span>,<span>% win</span>)</th>
<th><span>OU</span><BR><span>O</span>-<span>U</span>-<span>P</span> (<span>marg</span>,<span>% over</span>)</th>
<th><span>SU</span><BR><span>W</span>-<span>L</span> (<span>marg</span>,<span>% win</span>)</th>
<th name='query_header'><span>team</span></th>
</tr></thead>
        
        <tbody>
<tr bgcolor=FFFFFF>
<td align=center>356</td>
<td align=center>195-158-3 (0.84, 55.2&#37;)</td>
<td align=center>186-163-7 (0.82, 53.3&#37;)</td>
<td align=center>199-157 (1.69, 55.9&#37;)</td>
<td align=center><a href=query?text=team=Thunder&output=summary&sid=guest>Thunder</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1489</td>
<td align=center>774-690-25 (0.45, 52.9&#37;)</td>
<td align=center>691-769-29 (-0.43, 47.3&#37;)</td>
<td align=center>997-492 (5.08, 67.0&#37;)</td>
<td align=center><a href=query?text=team=Spurs&output=summary&sid=guest>Spurs</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1461</td>
<td align=center>738-691-32 (0.13, 51.6&#37;)</td>
<td align=center>737-699-25 (0.40, 51.3&#37;)</td>
<td align=center>843-618 (1.98, 57.7&#37;)</td>
<td align=center><a href=query?text=team=Mavericks&output=summary&sid=guest>Mavericks</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1403</td>
<td align=center>715-675-13 (0.23, 51.4&#37;)</td>
<td align=center>693-695-15 (0.53, 49.9&#37;)</td>
<td align=center>712-691 (0.06, 50.7&#37;)</td>
<td align=center><a href=query?text=team=Bulls&output=summary&sid=guest>Bulls</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1383</td>
<td align=center>694-663-26 (0.24, 51.1&#37;)</td>
<td align=center>661-697-25 (-0.02, 48.7&#37;)</td>
<td align=center>718-665 (-0.01, 51.9&#37;)</td>
<td align=center><a href=query?text=team=Hornets&output=summary&sid=guest>Hornets</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1416</td>
<td align=center>703-677-36 (-0.02, 50.9&#37;)</td>
<td align=center>681-708-27 (-0.16, 49.0&#37;)</td>
<td align=center>775-641 (1.50, 54.7&#37;)</td>
<td align=center><a href=query?text=team=Magic&output=summary&sid=guest>Magic</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1420</td>
<td align=center>707-684-29 (0.41, 50.8&#37;)</td>
<td align=center>723-680-17 (0.72, 51.5&#37;)</td>
<td align=center>820-600 (2.58, 57.7&#37;)</td>
<td align=center><a href=query?text=team=Suns&output=summary&sid=guest>Suns</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1400</td>
<td align=center>692-671-37 (0.10, 50.8&#37;)</td>
<td align=center>703-680-17 (0.67, 50.8&#37;)</td>
<td align=center>829-571 (2.62, 59.2&#37;)</td>
<td align=center><a href=query?text=team=Jazz&output=summary&sid=guest>Jazz</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1045</td>
<td align=center>517-505-23 (-0.11, 50.6&#37;)</td>
<td align=center>512-518-15 (0.22, 49.7&#37;)</td>
<td align=center>562-483 (0.99, 53.8&#37;)</td>
<td align=center><a href=query?text=team=Supersonics&output=summary&sid=guest>Supersonics</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1404</td>
<td align=center>694-678-32 (0.21, 50.6&#37;)</td>
<td align=center>695-681-28 (0.35, 50.5&#37;)</td>
<td align=center>761-643 (1.30, 54.2&#37;)</td>
<td align=center><a href=query?text=team=Pacers&output=summary&sid=guest>Pacers</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1372</td>
<td align=center>682-668-22 (-0.10, 50.5&#37;)</td>
<td align=center>644-700-28 (-0.29, 47.9&#37;)</td>
<td align=center>734-638 (0.98, 53.5&#37;)</td>
<td align=center><a href=query?text=team=Trailblazers&output=summary&sid=guest>Trailblazers</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1467</td>
<td align=center>725-712-30 (0.48, 50.5&#37;)</td>
<td align=center>697-743-27 (-0.21, 48.4&#37;)</td>
<td align=center>814-653 (2.02, 55.5&#37;)</td>
<td align=center><a href=query?text=team=Pistons&output=summary&sid=guest>Pistons</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1379</td>
<td align=center>685-674-20 (0.12, 50.4&#37;)</td>
<td align=center>668-693-18 (0.04, 49.1&#37;)</td>
<td align=center>501-878 (-3.74, 36.3&#37;)</td>
<td align=center><a href=query?text=team=Grizzlies&output=summary&sid=guest>Grizzlies</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1359</td>
<td align=center>668-663-28 (-0.23, 50.2&#37;)</td>
<td align=center>668-674-17 (0.59, 49.8&#37;)</td>
<td align=center>630-729 (-1.05, 46.4&#37;)</td>
<td align=center><a href=query?text=team=Knicks&output=summary&sid=guest>Knicks</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1385</td>
<td align=center>681-677-27 (0.20, 50.1&#37;)</td>
<td align=center>671-695-19 (0.59, 49.1&#37;)</td>
<td align=center>753-632 (1.39, 54.4&#37;)</td>
<td align=center><a href=query?text=team=Rockets&output=summary&sid=guest>Rockets</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1418</td>
<td align=center>695-697-26 (-0.29, 49.9&#37;)</td>
<td align=center>680-711-27 (-0.21, 48.9&#37;)</td>
<td align=center>698-720 (-0.46, 49.2&#37;)</td>
<td align=center><a href=query?text=team=Cavaliers&output=summary&sid=guest>Cavaliers</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1358</td>
<td align=center>666-668-24 (-0.07, 49.9&#37;)</td>
<td align=center>667-663-28 (0.82, 50.2&#37;)</td>
<td align=center>550-808 (-2.60, 40.5&#37;)</td>
<td align=center><a href=query?text=team=Raptors&output=summary&sid=guest>Raptors</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>644</td>
<td align=center>309-310-25 (-0.04, 49.9&#37;)</td>
<td align=center>324-310-10 (0.45, 51.1&#37;)</td>
<td align=center>229-415 (-4.27, 35.6&#37;)</td>
<td align=center><a href=query?text=team=Bobcats&output=summary&sid=guest>Bobcats</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1403</td>
<td align=center>684-688-31 (-0.20, 49.9&#37;)</td>
<td align=center>672-709-22 (0.40, 48.7&#37;)</td>
<td align=center>610-793 (-1.84, 43.5&#37;)</td>
<td align=center><a href=query?text=team=Nets&output=summary&sid=guest>Nets</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1458</td>
<td align=center>715-721-22 (0.08, 49.8&#37;)</td>
<td align=center>667-770-21 (-0.67, 46.4&#37;)</td>
<td align=center>828-630 (1.89, 56.8&#37;)</td>
<td align=center><a href=query?text=team=Heat&output=summary&sid=guest>Heat</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1405</td>
<td align=center>684-693-28 (-0.04, 49.7&#37;)</td>
<td align=center>691-688-26 (0.37, 50.1&#37;)</td>
<td align=center>646-759 (-1.24, 46.0&#37;)</td>
<td align=center><a href=query?text=team=Nuggets&output=summary&sid=guest>Nuggets</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1382</td>
<td align=center>676-686-20 (-0.20, 49.6&#37;)</td>
<td align=center>716-643-23 (1.47, 52.7&#37;)</td>
<td align=center>671-711 (-0.49, 48.6&#37;)</td>
<td align=center><a href=query?text=team=Kings&output=summary&sid=guest>Kings</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1461</td>
<td align=center>715-727-19 (0.29, 49.6&#37;)</td>
<td align=center>716-723-22 (0.46, 49.8&#37;)</td>
<td align=center>739-722 (0.53, 50.6&#37;)</td>
<td align=center><a href=query?text=team=Celtics&output=summary&sid=guest>Celtics</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1358</td>
<td align=center>656-672-30 (0.08, 49.4&#37;)</td>
<td align=center>692-637-29 (0.88, 52.1&#37;)</td>
<td align=center>516-842 (-3.33, 38.0&#37;)</td>
<td align=center><a href=query?text=team=Warriors&output=summary&sid=guest>Warriors</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1393</td>
<td align=center>674-699-20 (-0.31, 49.1&#37;)</td>
<td align=center>699-677-17 (0.44, 50.8&#37;)</td>
<td align=center>641-752 (-1.64, 46.0&#37;)</td>
<td align=center><a href=query?text=team=Hawks&output=summary&sid=guest>Hawks</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1394</td>
<td align=center>669-700-25 (0.08, 48.9&#37;)</td>
<td align=center>686-688-20 (-0.01, 49.9&#37;)</td>
<td align=center>648-746 (-0.99, 46.5&#37;)</td>
<td align=center><a href=query?text=team=Seventysixers&output=summary&sid=guest>Seventysixers</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1483</td>
<td align=center>710-743-30 (-0.39, 48.9&#37;)</td>
<td align=center>749-712-22 (0.76, 51.3&#37;)</td>
<td align=center>964-519 (3.96, 65.0&#37;)</td>
<td align=center><a href=query?text=team=Lakers&output=summary&sid=guest>Lakers</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1370</td>
<td align=center>655-690-25 (-0.49, 48.7&#37;)</td>
<td align=center>682-665-23 (0.51, 50.6&#37;)</td>
<td align=center>617-753 (-1.52, 45.0&#37;)</td>
<td align=center><a href=query?text=team=Timberwolves&output=summary&sid=guest>Timberwolves</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1369</td>
<td align=center>651-692-26 (-0.36, 48.5&#37;)</td>
<td align=center>709-644-16 (1.30, 52.4&#37;)</td>
<td align=center>617-752 (-1.21, 45.1&#37;)</td>
<td align=center><a href=query?text=team=Bucks&output=summary&sid=guest>Bucks</a></td>
</tr>
<tr bgcolor=E6E6E6>
<td align=center>1370</td>
<td align=center>639-709-22 (-0.35, 47.4&#37;)</td>
<td align=center>667-676-27 (0.30, 49.7&#37;)</td>
<td align=center>510-860 (-3.91, 37.2&#37;)</td>
<td align=center><a href=query?text=team=Clippers&output=summary&sid=guest>Clippers</a></td>
</tr>
<tr bgcolor=FFFFFF>
<td align=center>1373</td>
<td align=center>630-717-26 (-0.24, 46.8&#37;)</td>
<td align=center>669-673-31 (0.86, 49.9&#37;)</td>
<td align=center>557-816 (-2.39, 40.6&#37;)</td>
<td align=center><a href=query?text=team=Wizards&output=summary&sid=guest>Wizards</a></td>
</tr>
        </tbody>
      </table>
  </body>
</html>'''
 
