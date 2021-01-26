import sys
import torch
from logging import getLogger
from mwptoolkit.utils.utils import read_json_data,get_model
class Config(object):
    def __init__(self):
        super().__init__()
        self.cmd_config_dict={}
        self.variable_config_dict={}
        self.external_config_dict={}
        self.model_config_dict={}
        self.dataset_config_dict={}
        self.path_config_dict={}#
        self.final_config_dict={}
        self._load_config()
        self._load_cmd_line()
        
        self._build_path_config()
        self._load_model_config()
        self._load_dataset_config()

        self._merge_external_config_dict()
        self._build_final_config_dict()

        self._init_device()

    def _load_config(self):
        self.file_config_dict=read_json_data('mwptoolkit/config/config.json')
    
    def _convert_config_dict(self, config_dict):
        r"""This function convert the str parameters to their original type.

        """
        for key in config_dict:
            param = config_dict[key]
            if not isinstance(param, str):
                continue
            try:
                value = eval(param)
                if not isinstance(value, (str, int, float, list, tuple, dict, bool, Enum)):
                    value = param
            except (NameError, SyntaxError, TypeError):
                if isinstance(param, str):
                    if param.lower() == "true":
                        value = True
                    elif param.lower() == "false":
                        value = False
                    else:
                        value = param
                else:
                    value = param
            config_dict[key] = value
        return config_dict
    
    def _load_cmd_line(self):
        r""" Read parameters from command line and convert it to str.

        """
        cmd_config_dict = dict()
        unrecognized_args = []
        if "ipykernel_launcher" not in sys.argv[0]:
            for arg in sys.argv[1:]:
                if not arg.startswith("--") or len(arg[2:].split("=")) != 2:
                    unrecognized_args.append(arg)
                    continue
                cmd_arg_name, cmd_arg_value = arg[2:].split("=")
                if cmd_arg_name in cmd_config_dict and cmd_arg_value != cmd_config_dict[cmd_arg_name]:
                    raise SyntaxError("There are duplicate commend arg '%s' with different value." % arg)
                else:
                    cmd_config_dict[cmd_arg_name] = cmd_arg_value
        if len(unrecognized_args) > 0:
            logger = getLogger()
            logger.warning('command line args [{}] will not be used in TextBox'.format(' '.join(unrecognized_args)))
        cmd_config_dict = self._convert_config_dict(cmd_config_dict)

        if cmd_config_dict['task_type'] not in ['single_equation','multi_equation']:
            raise NotImplementedError("task_type {} can't be found".format(cmd_config_dict['task_type']))
        self.cmd_config_dict.update(cmd_config_dict)
        return cmd_config_dict
    
    def _get_model_and_dataset(self, model, dataset):
        if model is None:
            try:
                model = self.external_config_dict['model']
            except KeyError:
                raise KeyError(
                    'model need to be specified in at least one of the these ways: '
                    '[model variable, config file, config dict, command line] ')
        if not isinstance(model, str):
            final_model_class = model
            final_model = model.__name__
        else:
            final_model = model
            final_model_class = get_model(final_model)

        if dataset is None:
            try:
                final_dataset = self.external_config_dict['dataset']
            except KeyError:
                raise KeyError('dataset need to be specified in at least one of the these ways: '
                               '[dataset variable, config file, config dict, command line] ')
        else:
            final_dataset = dataset

        return final_model, final_model_class, final_dataset
    
    def _load_model_config(self):
        try:
            self.model_config_dict=read_json_data(self.path_config_dict["model_config_path"])
        except:
            self.model_config_dict={}
    
    def _load_dataset_config(self):
        try:
            self.dataset_config_dict=read_json_data(self.path_config_dict["dataset_config_path"])
        except:
            self.dataset_config_dict={}
    
    def _build_path_config(self):
        path_config_dict={}
        model_name=self.cmd_config_dict["model"]
        dataset_name=self.cmd_config_dict["dataset"]
        path_config_dict["checkpoint_path"]='checkpoint/'+'{}-{}.pth'.format(model_name,dataset_name)
        path_config_dict["trained_model_path"]='trained_model/'+'{}-{}.pth'.format(model_name,dataset_name)
        path_config_dict["log_path"]='log/'+'{}-{}.log'.format(model_name,dataset_name)
        path_config_dict["model_config_path"]="mwptoolkit/properties/model/{}.json".format(model_name)
        path_config_dict["dataset_config_path"]="mwptoolkit/properties/dataset/{}.json".format(dataset_name)
        path_config_dict["dataset_path"]="dataset/{}".format(dataset_name)
        self.path_config_dict=path_config_dict

        for key,value in path_config_dict.items():
            try:
                self.path_config_dict=self.cmd_config_dict[key]
            except:
                pass
    
    def _merge_external_config_dict(self):
        external_config_dict = dict()
        external_config_dict.update(self.file_config_dict)
        external_config_dict.update(self.variable_config_dict)
        external_config_dict.update(self.path_config_dict)
        external_config_dict.update(self.dataset_config_dict)
        external_config_dict.update(self.model_config_dict)
        external_config_dict.update(self.cmd_config_dict)
        self.external_config_dict = external_config_dict
    
    def _build_final_config_dict(self):
        self.final_config_dict.update(self.external_config_dict)
    
    def _init_device(self):
        self.final_config_dict['device'] = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("index must be a str.")
        self.final_config_dict[key] = value

    def __getitem__(self, item):
        if item in self.final_config_dict:
            return self.final_config_dict[item]
        else:
            return None
    
    def __str__(self):
        args_info = ''
        args_info += '\n'.join(
            ["{}={}".format(arg, value)
                for arg, value in self.final_config_dict.items()
                ])
        args_info += '\n\n'
        return args_info

