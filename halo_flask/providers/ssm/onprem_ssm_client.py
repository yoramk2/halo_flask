from __future__ import print_function

import configparser
import datetime
import json
import logging
import os
import time
from environs import Env
from abc import ABCMeta,abstractmethod
from halo_flask.exceptions import HaloError, CacheKeyError, CacheExpireError,HaloException
from halo_flask.providers.ssm.onprem_ssm import AbsOnPremClient
# from .logs import log_json


logger = logging.getLogger(__name__)

# for testing

class OnPremClient(AbsOnPremClient):
    dict = {}

    def put_parameter(self, Name, Value, Type, Overwrite):
        root = Name.split("/")
        section_position = len(root) - 1
        section_name = root[section_position]
        params = [{'Name':section_name,'Value':Value}]
        rec = {'Parameters' : params }
        self.dict[Name.replace("/"+section_name,"")] = rec

    def get_parameters_by_path(self, Path, Recursive, WithDecryption):
        return self.dict[Path]


