#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 20/10/2022 11:02 am
# @Organisation: Veracode

from constant import USER_CREATION_INPUT, DISPLAY_USERS_FMT, SpinnerThread
import copy
import json
import click
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
import sys
from credentials.credentials_commands import activate_credentials


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
        sys.exit(1)
      bar.update(idx, user.first_name)

  click.secho('Successfully creating platform users.', fg='green')


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


@click.group()
@click.pass_context
def users(ctx):
  """Manage Veracode Users"""
  setting_dict = ctx.obj['setting']
  use_activated_profile = click.confirm(
    f"Your activated credentials is "
    f"\"{setting_dict['activated_credentials']}\""
    f", continue using this profile to run this command?")
  while not use_activated_profile:
    ctx.invoke(activate_credentials)
    use_activated_profile = click.confirm(
      f"Your activated credentials is "
      f"\"{setting_dict['activated_credentials']}\""
      f", continue using this profile to run this command?")


@users.command('list')
@click.pass_context
def list_users(ctx):
  """List Veracode Users"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  print_users_headers()
  user_list = fetch_users(setting_dict, config)
  print_users(user_list)


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
  print_users(setting_dict)
