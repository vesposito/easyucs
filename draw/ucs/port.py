# coding: utf-8
# !/usr/bin/env python

""" port.py: Easy UCS Deployment Tool """


class UcsPortDraw:
    def __init__(self, id, color, size, coord, parent_draw, port, peer=None):
        self.parent_draw = parent_draw
        self.id = id
        self.color = color
        self.coord = coord
        self.size = size
        self.port = port
        self._parent = port
        self.aggr_id = self.port.aggr_port_id if hasattr(self.port, "aggr_port_id") else None
        if peer:
            self.peer = peer
