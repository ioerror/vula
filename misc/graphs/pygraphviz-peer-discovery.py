#!/usr/bin/env python3
# apt install python3-pygraphviz

import pygraphviz as pgv

G = pgv.AGraph('wg-mdns-peer-discovery-long.dot')
G.layout(prog='dot')
G.draw('pygraphviz-wg-mdns-peer-discovery-long.png')

G = pgv.AGraph('wg-mdns-peer-discovery-short.dot')
G.layout(prog='dot')
G.draw('pygraphviz-wg-mdns-peer-discovery-short.png')
