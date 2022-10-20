#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 18/10/2022 3:05 pm
# @Organisation: Veracode

import configparser
import json
import click
from constant import SETTINGS_INIT_DICT, SETTINGS, CREDENTIALS, save_settings
from credentials import credentials_commands as credentials
from users import user_commands as users
from applications import application_commands as applications


@click.group()
@click.pass_context
def main(ctx):
  """Veracode PoV Automation Tool"""
  if not CREDENTIALS.parent.exists():
    CREDENTIALS.parent.mkdir()
  if not SETTINGS.parent.exists():
    SETTINGS.parent.mkdir()
  if not CREDENTIALS.exists():
    CREDENTIALS.touch()
  if not SETTINGS.exists():
    SETTINGS.touch()
    save_settings(SETTINGS_INIT_DICT)
  with open(SETTINGS, 'r') as fp:
    settings_dict = json.load(fp)
  ctx.ensure_object(dict)
  ctx.obj['setting'] = settings_dict

  config = configparser.ConfigParser()
  config.read(CREDENTIALS)
  ctx.obj['config'] = config

  # in case activated credentials is deleted, fall back to the first credentials
  if len(config.sections()) > 0 \
          and settings_dict['activated_credentials'] not in config.sections():
    settings_dict['activated_credentials'] = config.sections()[0]
    save_settings(settings_dict)


main.add_command(credentials.credentials)
main.add_command(users.users)
main.add_command(applications.applications)
