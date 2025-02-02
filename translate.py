#!/usr/bin/env python3
import hcl2
import re
import glob
import os
from collections import defaultdict
import json
from jinja2 import Template

moved_template = Template('''
moved {
    from = {{ _from }}
    to   = {{ _to }}
}

''')

class TFConfig(object):

    def __init__(self, config_map, _dir):
        os.chdir(_dir)

        with open(config_map) as config_map_input:
            self.config_map = json.loads(config_map_input.read())

        self._config                  = defaultdict(dict)
        self.local_replacement_map    = dict()
        self.data_replacement_map     = list()
        self.resource_replacement_map = list()
        self.variable_replacement_map = list()
        self.module_replacement_map   = list()
        self.moved_items              = set()
        self.output_replacement_map   = list()

        for x in glob.glob("*.tf"):
            d = hcl2.loads(open(x).read())
            rsc_types = list(d.keys())
            for rsc_type in rsc_types:
                for rsc in d.get(rsc_type):
                    self._config[rsc_type].update(rsc)
 
    def replace_file_name(self, filename):
        for k, v in self.config_map.items():
            filename = filename.replace(k, v)
        return filename
    
    @property
    def locals(self):
        return self._config.get('locals')

    def replace_data(self, data):
        for k, v in self.config_map.items():
            if k in data:
                data = data.replace(k, v)
        return data

    def replace_locals_in_memory(self):
        for _local in self.locals:
            _data = _local
            for k, v in self.config_map.items():
                if k in _local:
                    _data = _data.replace(k, v)
            self.local_replacement_map[_local] = _data
        
    def replace_locals_on_file(self):
        for x in glob.glob("*.tf"):
            with open(x) as tf_input:
                data = tf_input.read()
                for k, v in self.local_replacement_map.items():
                    data = str(data).replace(k, v)
            with open(x, 'w') as tf_output:
                tf_output.write(data)
            os.rename(x, self.replace_file_name(x))
                
    @property
    def modules(self):
        return self._config.get('module')
    
    def replace_modules_in_memory(self):
        for _module in self.modules:
            _data = _module
            replaced = False
            for k, v in self.config_map.items():
                if k in _data:
                    _data = _data.replace(k, v)
                    replaced = True
            self.module_replacement_map.append(
                dict(
                    original=f"module \"{_module}\"",
                    replaced=f"module \"{_data}\""
                )
            )
            self.module_replacement_map.append(
                dict(
                    original=f"module.{_module}",
                    replaced=f"module.{_data}"
                )
            )
            if replaced:
                self.moved_items.add(
                    moved_template.render(
                        _from=f"module.{_module}",
                        _to=f"module.{_data}"
                    )
                )
                    
    def replace_modules_on_file(self):
        for x in glob.glob("*.tf"):
            with open(x) as tf_input:
                data = tf_input.read()
                for var in self.module_replacement_map:
                    data = str(data).replace(
                        var.get('original'), 
                        var.get('replaced')
                    )
            with open(x, 'w') as tf_output:
                tf_output.write(data)
            os.rename(x, self.replace_file_name(x))

    @property
    def resources(self):
        self._config['resource'] = dict()
        for x in glob.glob("*.tf"):
            d = hcl2.loads(open(x).read())
            if 'resource' in d:
                for rsc in d.get('resource'):
                    for k, v in rsc.items():
                        if k not in self._config['resource']:
                            self._config['resource'][k] = list()
                        for single_rsc in v.keys():
                            self._config['resource'][k].append(single_rsc)
        return self._config.get('resource')
    
    def replace_resources_in_memory(self):
        for rsc_type in self.resources.keys():
            for rsc in self.resources.get(rsc_type):
                data = rsc
                replaced_data = self.replace_data(data)
                if data == replaced_data:
                    continue
                self.resource_replacement_map.append(
                    dict(
                        original=f"resource \"{rsc_type}\" \"{rsc}\"",
                        replaced=f"resource \"{rsc_type}\" \"{replaced_data}\""
                    )
                )
                self.resource_replacement_map.append(
                    dict(
                        original=f"{rsc_type}.{rsc}",
                        replaced=f"{rsc_type}.{replaced_data}"
                    )
                )
                self.moved_items.add(
                    moved_template.render(
                        _from=f"{rsc_type}.{rsc}",
                        _to=f"{rsc_type}.{replaced_data}"
                    )
                )
        
    def replace_resources_on_file(self):
        for x in glob.glob("*.tf"):
            with open(x) as tf_input:
                data = tf_input.read()
                for var in self.resource_replacement_map:
                    data = str(data).replace(
                        var.get('original'), 
                        var.get('replaced')
                    )
            with open(x, 'w') as tf_output:
                tf_output.write(data)
            os.rename(x, self.replace_file_name(x))

    @property
    def variables(self):
        return self._config.get('variable')

    def replace_variables_in_memory(self):
        for _variable in self.variables:
            _data = _variable
            for k, v in self.config_map.items():
                if k in _data:
                    _data = _data.replace(k, v)
            self.variable_replacement_map.append(
                dict(
                    original=f"variable \"{k}\"",
                    replaced=f"variable \"{_data}\""
                )
            )
            self.variable_replacement_map.append(
                dict(
                    orignal=f"var.{k}",
                    replaced=f"var.{_data}"
                )
            )

    def replace_variables_on_file(self):
        for x in glob.glob("*.tf"):
            with open(x) as tf_input:
                data = tf_input.read()
                for var in self.resource_replacement_map:
                    data = str(data).replace(
                        var.get("original"), 
                        var.get("replaced")
                    )
            with open(x, 'w') as tf_output:
                tf_output.write(data)
            os.rename(x, self.replace_file_name(x))
    
    @property
    def data(self):
        return self._config.get('data')
    
    def replace_data_in_memory(self):
        for data_type, data_list in self.data.items():
            for datum in data_list.keys():
                print(datum)
                _data = datum
                for k, v in self.config_map.items():
                    if k in datum:
                        _data = _data.replace(k, v)
                self.data_replacement_map.append(
                    dict(
                        original=f"data \"{data_type}\" \"{datum}\"",
                        replaced=f"data \"{data_type}\" \"{_data}\""
                    )
                )
                self.data_replacement_map.append(
                    dict(
                        original=f"data.{data_type}.{datum}",
                        replaced=f"data.{data_type}.{_data}"
                    )
                        )

    def replace_data_on_file(self):
        for x in glob.glob("*.tf"):
            with open(x) as tf_input:
                data = tf_input.read()
                for var in self.data_replacement_map:
                    data = str(data).replace(
                        var.get("original"), 
                        var.get("replaced")
                    )
            with open(x, 'w') as tf_output:
                tf_output.write(data)
            os.rename(x, self.replace_file_name(x))

    def dump_moved(self):
        with open("moved.tf", "w") as moved_output:
            for moved_item in self.moved_items:
                moved_output.write(moved_item)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--map", default=os.path.join(os.getcwd(), "config-map.json"))
    parser.add_option("--dir", default=os.getcwd())
    opt, args = parser.parse_args()
    cnfg = TFConfig(
        opt.map,
        opt.dir
    )
    print("preformmating with terraform fmt...")
    os.system("terraform fmt")

    print("converting data sources...")
    cnfg.replace_data_in_memory()
    cnfg.replace_data_on_file()

    print("converting resources...")
    cnfg.replace_resources_in_memory()
    cnfg.replace_resources_on_file()

    print("converting modules...")
    cnfg.replace_modules_in_memory()
    cnfg.replace_modules_on_file()

    print("converting variables...")
    cnfg.replace_variables_in_memory()
    cnfg.replace_variables_on_file()

    print("converting locals...")
    cnfg.replace_locals_in_memory()
    cnfg.replace_locals_on_file()

    print("duping moved items...")
    cnfg.dump_moved()

    print("Terraform FMT...")
    os.system("terraform fmt")