#!/usr/bin/env python
import inkex
import sys
import subprocess
from lxml import etree
from collections import OrderedDict

class Glue(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-d", "--direction",
                        action="store", type="string",
                        dest="direction", default="horizontal",
                        help="direction for gluing")

    def effect(self):
        filename = self.args[-1]
        elem_list = get_elem_dim_text(filename).split('\n')
        elem_position_dict = parse_elems(elem_list)
        
        attachable_elems = []
        for id, node in self.selected.iteritems():
           attachable_elems.append(AttachableElement(node, elem_position_dict[id]))

        sorted_elems = sorted(attachable_elems, key=lambda e: e.dimension['y'])        
        for first,second in zip(sorted_elems, sorted_elems[1:]):
            if self.options.direction == 'horizontal':
                second.attach_right_of(first)
            elif self.options.direction == 'vertical':
                second.attach_down_to(first)

class AttachableElement(object):
    def __init__(self, node, dimension):
        self.dimension = dimension
        self.node = node

    def attach_down_to(self, other_attachable_elem):
        wanted_x = other_attachable_elem.dimension['x']
        wanted_y = (other_attachable_elem.dimension['y'] 
                  + other_attachable_elem.dimension['height'])
        self.update_pos_to(wanted_x, wanted_y)

    def attach_right_of(self, other_attachable_elem):
        wanted_x = (other_attachable_elem.dimension['x'] 
                  + other_attachable_elem.dimension['width'])
        wanted_y = other_attachable_elem.dimension['y']
        self.update_pos_to(wanted_x, wanted_y)

    def update_pos_to(self, x,y):
        curr_transform = Transform(self.node.get('transform'))
        curr_transform.update_translate(*self.calc_translation_to(x,y))
        self.node.set('transform', curr_transform.to_string())
        self.dimension['x'] = x
        self.dimension['y'] = y

    def calc_translation_to(self, x,y):
        curr_transform = Transform(self.node.get('transform'))
        curr_translate_x, curr_translate_y = curr_transform.get_translate()
        needed_translate_x = -(self.dimension['x'] - curr_translate_x) + x
        needed_translate_y = -(self.dimension['y'] - curr_translate_y) + y
        return (needed_translate_x, needed_translate_y)


#FIXME: doesnt work with rotations and matrix now, maybe switch to matrix operations
class Transform(object):
    def __init__(self, transform_string):
        self.t_dict = self.parse_transforms(transform_string)

    def update_translate(self, x, y):
        self.t_dict['translate'] = ''.join(map(str,[
            '(',x,',',y,')'
        ]))

    def get_translate(self):
        try:
            current = self.t_dict['translate']
            return tuple(self._get_nums(current))
        except KeyError:
            return (0,0)

    def _get_nums(self, s):
            return (map(float, s[1:-2].split(',')))

    def update(self, key, value):
            self.t_dict[key] = value

    def to_string(self):
        ret = []
        for key in self.t_dict.keys():
            ret.append(key + self.t_dict[key])
        return ' '.join(ret)

    def parse_transforms(self, s):
        ret = OrderedDict()
        if(s):
            for t in s.split(' '):
                splt_lst = t.split('(')
                ret[splt_lst[0]] = '('+ splt_lst[1]
        return ret

def parse_elems(elem_list):
    ret = {}
    for elem in elem_list:
        item = elem.split(',')
        if(len(item) != 5): continue

        ret[item[0]] = {
                'x':float(item[1]),
                'y':float(item[2]),
                'width':float(item[3]),
                'height':float(item[4]),
                }
    return ret
        
def get_elem_dim_text(filename):
    ret_val, out, err = cmd_exec('inkscape --query-all "%s"' % (filename))
    return out

def cmd_exec(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out_stream, err_stream = process.communicate()
    errcode = process.returncode
    return errcode, out_stream, err_stream
        

if __name__ == '__main__':
    glue = Glue()
    glue.affect()
