import rpy2.robjects as robjects
import Image
import math
from rpy2.robjects.lib import grid
from rpy2.robjects.packages import importr

r = robjects.r

COLORS =  ["#000000","#FF0000","#00FF00","#0000FF",
                                    "#880000",                   "#88FF00","#8800FF",
                                    "#008800","#FF8800",                   "#0088FF",
                                    "#000088","#FF0088","#00FF88"                  ]

def scatter(x,y,fname,size=(400,200),colors=COLORS,**kwargs):
    if not len(x):
        x = [[]]; y = [[]]
    elif type(x[0]) is not list:
        x = [x]; y=[y]
    r.png(fname,width=size[0],height=size[1])
    #r("par(mar=c(0, 0, 0, 0)) ") # b, l, t, r margins
    #r("par(cex=c(%s )) "%str(x[0])[1:-1])
    len_colors = len(colors)
    for i in range(len(x)):
        if i:  r("par(new=T) ")             # which means use the old canvas.
        r.plot(x[i],y[i], col=colors[i%len_colors],**kwargs)
        add = True
    r['dev.off']()

def plot(x,y,fname,size=(300,100),dx=0.5,colors=COLORS,**kwargs):
    if not len(x):
        x = [[]]; y = [[]]
    elif type(x[0]) is not list:
        x = [x]; y=[y]
    r.png(fname,width=size[0],height=size[1])
    r("par(mar=c(0, 0, 0, 0)) ") # b, l, t, r margins
    len_colors = len(colors)
    for i in range(len(x)):
        if i:  r("par(new=T) ")             # which means use the old canvas.
        r.plot(x[i],y[i], col=colors[i%len_colors],xlab='', ylab='',axes=False,**kwargs)
        add = True
    r['dev.off']()


def hist(x,y,fname,size=(300,100),**kwargs):
    r.png(fname,width=size[0],height=size[1])
    r("par(mar=c(0, 0, 0, 0)) ") # b, l, t, r margins
    r.hist(x,y, xlab='', ylab='',axes=False,**kwargs)
    r['dev.off']()

def sample_plot():
    x = range(1,11)
    y = [i**2 for i in x]
    r("par(mar=c(0, 0, 0, 0)) ") # b, l, t, r margins
    r.plot(x,y, xlab='', ylab='',col='lightblue',axes=False,type='h',xlim=r.range(1,10),ylim=r.range(1,240),
                                 frame=True,lwd=50,bg='blue')

    r("par(new=T) ")
    r.plot(x,y, xlab='', ylab='',col='red')

def sample_hist():
    # not working as expected.
    x = r.range(10) + r.range(3,6) + r.range(5,10)
    x = r.range(10) + r.range(3,8)
    #r.png('/tmp/rdemo.png',width=800,height=100)
    r("par(mar=c(0, 0, 0, 0)) ")
    r.hist(x, main='', xlab='', ylab='',col='blue',axes=True)
    #r.hist(y, main='', xlab='', ylab='',col='blue',axes=False,add=True)
    #r.dev_off()

def plot_hist():
    y = range(10)
    x = range(len(y))
    ylim = r.range(1,max(y)+1)
    plot(x,y,"/tmp/rpy_plot_hist.png",type='h',    size = (300,200), lwd=10,pch=15,ylim=ylim)

def test_scatter():
    x = range(2,100)
    y =map(lambda x:x*x, x)
    scatter(x,y,"/tmp/rpy_scatter.png",log='xy',xlab='x',ylab='y',
            lwd=4,
            pch=15)

if __name__ == "__main__":
    #sample_plot()
    #sample_hist()
    #plot_hist()
    test_scatter()
