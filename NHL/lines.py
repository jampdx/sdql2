import PyQL.columns

lines_2014 = """
-101	-109
-102	-108
-103	-107
-104	-106
-105	-105
100	-110
101	-111
102	-113
103	-114
104	-115
105	-116
106	-117
107	-118
108	-119
109	-120
110	-121
111	-123
112	-124
113	-125
114	-126
115	-127
117	-129
118	-130
120	-133
122	-135
124	-137
125	-138
126	-139
127	-140
128	-141
129	-143
130	-144
131	-145
133	-147
135	-149
136	-150
137	-152
140	-155
142	-157
144	-160
147	-163
149	-165
152	-169
153	-170
155	-172
157	-174
158	-175
161	-179
162	-180
166	-185
171	-190
173	-193
175	-195
180	-200
188	-210
196     -220
205	-230"""

d = {}
for l in lines_2014.split('\n'):
    if not l.strip(): continue
    line,oline = map(int,l.split())
    d[line] = oline
    d[oline] = line


def extrapolate(line,d):
    for i in range(10):
        if d.has_key(line+i):
            return d[line+i]+i
        if d.has_key(line-i):
            return d[line-i]-i

def other_line(line):
    #print "other iline:",line
    if line is None:
        #print "oline also None"
        return None
    iline = int(line)
    oline = None
    m = -1.214; b = 11.387
    if iline>205:
        oline =  int(m * float(iline) + b)
        #print "ols match"
    elif iline<=-230:
        oline = int((iline-b)/m)
        #print "ols match"
    elif d.get(iline):
        #print "direct match"
        oline = d[iline]
    else:
        oline = extrapolate(iline,d)
        #print "extrapo match"
    #print "other returning ioline:",oline
    return oline
