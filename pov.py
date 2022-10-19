#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 18/10/2022 3:05 pm
# @Organisation: Veracode

import configparser
import json
import sys
import threading
import time
import copy
from datetime import datetime

import click
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
from constant import SETTINGS_INIT_DICT, SETTINGS, CREDENTIALS, USER, \
  DISPLAY_CREDENTIALS_FMT, DISPLAY_USERS_FMT, USER_CREATION_INPUT, \
  DISPLAY_APPLICATION_FMT

SETTINGS_DICT = dict()


def print_credentials_header():
  click.echo(
    DISPLAY_CREDENTIALS_FMT.format("ID", "Profile", "API_KEY_ID", "Active"))
  click.echo(
    DISPLAY_CREDENTIALS_FMT.format("-" * 3, "-" * 10, "-" * 32, "-" * 6))


def print_credentials(config, setting):
  sections = config.sections()

  for idx, section in enumerate(sections, start=1):
    if 'veracode_api_key_id' not in config[section].keys() or \
            'veracode_api_key_secret' not in config[section].keys():
      raise click.ClickException('Cannot parse credentials file.')
    click.echo(DISPLAY_CREDENTIALS_FMT.
               format(idx,
                      section,
                      config[section]['veracode_api_key_id'],
                      "Yes" if section == setting['activated_credentials']
                      else "No"))


def save_credentials(config):
  with open(CREDENTIALS, 'w') as configfile:
    config.write(configfile)


def save_settings(setting_dict):
  with open(SETTINGS, 'w') as fp:
    fp.write(json.dumps(setting_dict, indent=4))


def print_users_headers(adding_user=None):
  click.echo(DISPLAY_USERS_FMT.
             format("ID",
                    "Email",
                    "Enabled" if not adding_user else "First Name",
                    "SAML" if not adding_user else "Last Name"))
  click.echo(DISPLAY_USERS_FMT.format("-" * 3, "-" * 35, "-" * 12, "-" * 12))


def fetch_users(settings_dict, config):
  user_list = []
  spinner_thread = SpinnerThread()
  spinner_thread.start()
  api_id = config[settings_dict['activated_credentials']]['veracode_api_key_id']
  api_key = config[settings_dict['activated_credentials']][
    'veracode_api_key_secret']
  try:
    response = requests. \
      get(settings_dict['admin_base'] + "/users?size=160",
          auth=RequestsAuthPluginVeracodeHMAC(api_key_id=api_id,
                                              api_key_secret=api_key),
          headers=settings_dict['headers'])
  except requests.RequestException as e:
    click.echo("Whoops!")
    click.echo(e)
    sys.exit(1)

  spinner_thread.set_complete()
  sys.stdout.write('\b')

  if response.ok:
    data = response.json()
    for user in data['_embedded']['users']:
      local_user = User(
        '', '', user['email_address'], user['email_address'],
        user['user_id'], user['saml_user'], user['login_enabled'])
      user_list.append(local_user)
  else:
    click.secho(f"{response.status_code} "
                f"{response.json()['message']}",
                fg='red')
  return user_list


def print_users(user_list):
  for idx, user in enumerate(user_list, start=1):
    click.echo(DISPLAY_USERS_FMT.
               format(idx, user.email,
                      "True" if user.enabled else "False",
                      "True" if user.saml else "False"))


def add_users_to_platform(user_list, config, settings_dict):
  api_id = config[settings_dict['activated_credentials']]['veracode_api_key_id']
  api_key = config[settings_dict['activated_credentials']][
    'veracode_api_key_secret']

  with click.progressbar(
          length=len(user_list),
          show_eta=False,
          item_show_func=lambda first_name: f"Adding {first_name}"
  ) as bar:
    for idx, user in enumerate(user_list, start=1):
      user_json = user.get_user_json()
      try:
        response = requests. \
          post(settings_dict['admin_base'] + "/users",
               auth=RequestsAuthPluginVeracodeHMAC(api_key_id=api_id,
                                                   api_key_secret=api_key),
               headers={'Content-Type': 'application/json',
                        'Accept': 'application/json'},

               data=user_json)
      except requests.RequestException as e:
        click.echo("Whoops!")
        click.echo(e)
        sys.exit(1)

      if response.ok:
        pass
      else:
        click.secho(f"{response.status_code} "
                    f"{response.json()['message']}",
                    fg='red')
      bar.update(idx, user.first_name)

  click.secho('Successfully creating platform users.', fg='green')


def print_applications_header():
  click.echo(DISPLAY_APPLICATION_FMT.
             format("ID", "Application", "Policy", "Last Scan"))
  click.echo(
    DISPLAY_APPLICATION_FMT.format("-" * 3, "-" * 40, "-" * 40, "-" * 20))


def fetch_applications(settings_dict, config):
  application_list = []
  spinner_thread = SpinnerThread()
  spinner_thread.start()
  api_id = config[settings_dict['activated_credentials']]['veracode_api_key_id']
  api_key = config[settings_dict['activated_credentials']][
    'veracode_api_key_secret']
  try:
    response = requests. \
      get(settings_dict['api_base'] + "/applications",
          auth=RequestsAuthPluginVeracodeHMAC(api_key_id=api_id,
                                              api_key_secret=api_key),
          headers=settings_dict['headers'])
  except requests.RequestException as e:
    click.echo("Whoops!")
    click.echo(e)
    sys.exit(1)

  spinner_thread.set_complete()
  sys.stdout.write('\b')

  if response.ok:
    data = response.json()
    for application in data['_embedded']['applications']:
      local_application = Application(
        application['profile']['name'],
        application['profile']['policies'][0]['name'],
        application['last_completed_scan_date']
      )
      application_list.append(local_application)
  else:
    click.secho(f"{response.status_code} "
                f"{response.json()['message']}",
                fg='red')
  return application_list


def print_applications(application_list):
  for idx, application in enumerate(application_list, start=1):
    dt_frm = "%Y-%b-%d %I:%M %p"
    last_scan_time = "Nil" if not application.last_scan else datetime.strptime(
      application.last_scan, "%Y-%m-%dT%H:%M:%S.%f%z").strftime(dt_frm)
    click.echo(DISPLAY_APPLICATION_FMT.
               format(idx, application.application_name,
                      application.policy_name, last_scan_time))


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


@main.group()
@click.pass_context
def users(ctx):
  """Manage Veracode Users"""
  pass


@users.command('list')
@click.pass_context
def list_users(ctx):
  """List Veracode Users"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  use_activated_profile = click.confirm(
    f"Your activated credentials is"
    f" \"{setting_dict['activated_credentials']}\", continue listing"
    f" users using this profile?")
  if use_activated_profile:
    print_users_headers()
    user_list = fetch_users(setting_dict, config)
    print_users(user_list)
  else:
    ctx.invoke(activate_credentials)
    ctx.invoke(list_users)


@users.command('add')
@click.pass_context
def add_user(ctx):
  """Add Veracode Users"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  user_list = []
  while True:
    email = click.prompt("Please enter user's email")
    first_name = click.prompt("Please enter user's first name")
    last_name = click.prompt("Please enter user's last name")
    user = User(first_name, last_name, email, email)  # username is email
    user_list.append(user)
    print_users_headers(True)
    for idx, user in enumerate(user_list, start=1):
      click.echo(DISPLAY_USERS_FMT.
                 format(idx, user.email, user.first_name, user.last_name))
    if not click.confirm(f'Add more users in this Veracode account?'):
      break
  click.echo('Adding users to Veracode Platform...')
  add_users_to_platform(user_list, config, setting_dict)


@users.command('update')
@click.pass_context
def update_user(ctx):
  """Update Veracode Users"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  user_list = []
  print_users_headers()
  print_users(setting_dict, config)


@main.group()
@click.pass_context
def applications(ctx):
  """Manage Veracode Applications"""
  pass


@applications.command('list')
@click.pass_context
def list_applications(ctx):
  """List Veracode Applications"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  use_activated_profile = click.confirm(
    f"Your activated credentials is"
    f" \"{setting_dict['activated_credentials']}\", continue listing"
    f" users using this profile?")
  if use_activated_profile:
    print_applications_header()
    application_list = fetch_applications(setting_dict, config)
    print_applications(application_list)
  else:
    ctx.invoke(activate_credentials)
    ctx.invoke(list_applications)


@main.group()
@click.pass_context
def credentials(ctx):
  """Manage Veracode API Credentials"""
  pass


@credentials.command('list')
@click.pass_context
def list_credentials(ctx):
  """List Veracode API Credentials"""
  print_credentials_header()
  config = ctx.obj['config']
  setting = ctx.obj['setting']
  print_credentials(config, setting)


@credentials.command('add')
@click.pass_context
def add_credentials(ctx):
  """Add Veracode API Credentials"""
  config = ctx.obj['config']
  profile = click.prompt("Profile Name")
  if profile in config.sections():
    profile_overwrite = click.confirm(
      f"You are about to overwrite profile \"{profile}\", continue?")
    if not profile_overwrite:
      return

  api_id = click.prompt('veracode_api_key_id')
  api_key = click.prompt('veracode_api_key_secret')
  config[profile] = dict()
  config[profile]['veracode_api_key_id'] = api_id
  config[profile]['veracode_api_key_secret'] = api_key

  save_credentials(config)


@credentials.command('update')
@click.pass_context
def update_credentials(ctx):
  """Update Veracode API Credentials"""
  config = ctx.obj['config']
  setting = ctx.obj['setting']
  print_credentials_header()
  print_credentials(config, setting)

  while True:
    profile = click.prompt("Enter profile to update or exit to quit")
    if profile == 'exit':
      return
    if profile not in config.sections():
      click.secho(f"Profile {profile} not found!", fg='red')
    else:
      break

  profile_overwrite = click.confirm(f"You are about to overwrite "
                                    f"profile \"{profile}\", continue?")
  if not profile_overwrite:
    return

  api_id = click.prompt('veracode_api_key_id')
  api_key = click.prompt('veracode_api_key_secret')
  config[profile] = dict()
  config[profile]['veracode_api_key_id'] = api_id
  config[profile]['veracode_api_key_secret'] = api_key

  save_credentials(config)


@credentials.command('delete')
@click.pass_context
def delete_credentials(ctx):
  """Delete Veracode API Credentials"""
  config = ctx.obj['config']
  setting = ctx.obj['setting']
  print_credentials_header()
  print_credentials(config, setting)

  while True:
    profile = click.prompt("Enter profile to delete or exit to quit")
    if profile == 'exit':
      return
    if profile not in config.sections():
      click.secho(f"Profile {profile} not found!", fg='red')
    else:
      break

  del config[profile]
  save_credentials(config)


@credentials.command('activate')
@click.pass_context
def activate_credentials(ctx):
  """Activate Veracode API Credentials"""
  config = ctx.obj['config']
  setting = ctx.obj['setting']
  print_credentials_header()
  print_credentials(config, setting)

  while True:
    profile = click.prompt("Enter profile to activate or exit to quit")
    if profile == 'exit':
      return
    if profile not in config.sections():
      click.secho(f"Profile {profile} not found!", fg='red')
    else:
      break

  setting['activated_credentials'] = profile
  save_settings(setting)


class User:
  def __init__(self, first_name, last_name, email,
               username, user_id=None, saml=None, enabled=None):
    self.first_name = first_name
    self.last_name = last_name
    self.email = email
    self.username = username
    self.user_id = '' if not user_id else user_id
    self.saml = False if not saml else saml
    self.enabled = True if not enabled else enabled

  def get_user_json(self):
    user_dict = copy.deepcopy(USER_CREATION_INPUT)
    user_dict['first_name'] = self.first_name
    user_dict['last_name'] = self.last_name
    user_dict['email_address'] = self.email
    user_dict['user_name'] = self.username
    return json.dumps(user_dict)


class Application:
  def __init__(self, application_name, policy_name, last_scan):
    self.application_name = application_name
    self.policy_name = policy_name
    self.last_scan = last_scan


class SpinnerThread(threading.Thread):
  def __init__(self):
    super().__init__(target=self._spin)
    self.done = False

  def set_complete(self):
    self.done = True

  def _spin(self):
    while True:
      for t in '|/-\\':
        sys.stdout.write(t)
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')
        if self.done:
          return
