#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 20/10/2022 11:02 am
# @Organisation: Veracode

from constant import USER_CREATION_INPUT, SpinnerThread
import copy
import json
import click
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
import sys
from credentials_commands import activate_credentials

DISPLAY_USERS_FMT = "{:<3} {:35} {:20} {:20}"
DISPLAY_USERS_DETAIL_FMT = "{:<3} {:<30} {:<12} {:12} {:12}"


def print_users_headers(adding_user=None, show_details=False):
  if not show_details:
    click.echo(DISPLAY_USERS_FMT.
               format("ID",
                      "Email",
                      "Enabled" if not adding_user else "First Name",
                      "SAML" if not adding_user else "Last Name"))
    click.echo(DISPLAY_USERS_FMT.format("-" * 3, "-" * 30, "-" * 12, "-" * 12))
  else:
    click.echo(
      DISPLAY_USERS_DETAIL_FMT.format("ID", "Email", "First Name", "Last Name",
                                      "Last Login"))
    click.echo(
      DISPLAY_USERS_DETAIL_FMT.format("-" * 3, "-" * 30, "-" * 12, "-" * 12,
                                      "-" * 12))


def fetch_users(settings_dict, config, show_details=False):
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

  if not show_details:
    spinner_thread.set_complete()
    sys.stdout.write('\b')
    return user_list

  for user in user_list:
    try:
      response = requests.get(
        settings_dict['admin_base'] + '/users/' + user.user_id,
        auth=RequestsAuthPluginVeracodeHMAC(
          api_key_id=api_id,
          api_key_secret=api_key),
        headers=settings_dict['headers'])

    except requests.RequestException as e:
      click.echo('Whoops!')
      click.echo(e)
      sys.exit(1)
    if response.ok:
      data = response.json()
      user.first_name = data['first_name']
      user.last_name = data['last_name']
      user.last_login = None if 'last_login' not in data.keys() else data[
        'last_login']

  spinner_thread.set_complete()
  sys.stdout.write('\b')
  return user_list


def print_users(user_list, show_details=False):
  if not show_details:
    for idx, user in enumerate(user_list, start=1):
      click.echo(DISPLAY_USERS_FMT.
                 format(idx, user.email,
                        "True" if user.enabled else "False",
                        "True" if user.saml else "False"))
  else:
    for idx, user in enumerate(user_list, start=1):
      click.echo(
        DISPLAY_USERS_DETAIL_FMT.
        format(idx,
               user.email[:28] + (user.email[28:] and '..'),
               user.first_name[:10] + (user.first_name[10:] and '..'),
               user.last_name[:10] + (user.last_name[10:] and '..'),
               "None" if not user.last_login else user.last_login))


def add_users_to_platform(user_list, config, settings_dict):
  api_id = config[settings_dict['activated_credentials']]['veracode_api_key_id']
  api_key = config[settings_dict['activated_credentials']][
    'veracode_api_key_secret']

  count = 0

  with click.progressbar(
          length=len(user_list),
          show_eta=False,
          item_show_func=lambda first_name: f"Adding user: {first_name}"
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
        # sys.exit(1)

      if response.ok:
        count += 1
      else:
        click.secho(f"{response.status_code} "
                    f"{response.json()['message']}",
                    fg='red')
        # sys.exit(1)
      bar.update(idx - 1, user.first_name)

  click.secho(f'Successfully created {count} platform users.', fg='green')


@click.group()
@click.pass_context
def users(ctx):
  """Manage Veracode Users"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  if not config.sections():
    click.secho(
      'You have not configured Veracode API credentials, '
      'please run \"pov credentials add\" command before running this command.')
    sys.exit(1)
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
@click.option('-d',
              '--show-details',
              help='Include Veracode User Details',
              is_flag=True)
def list_users(ctx, show_details):
  """List Veracode Users"""
  if show_details:
    click.secho('Showing user details will take longer time to run.',
                fg='yellow')
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  print_users_headers(show_details=show_details)
  user_list = fetch_users(setting_dict, config, show_details=show_details)
  print_users(user_list, show_details=show_details)


def delete_one_user(user, settings_dict, config):
  spinner_thread = SpinnerThread()

  api_id = config[settings_dict['activated_credentials']]['veracode_api_key_id']
  api_key = config[settings_dict['activated_credentials']][
    'veracode_api_key_secret']

  if click.confirm(f'Delete \"{user.first_name}\", continue?'):
    spinner_thread.start()
    try:
      response = requests. \
        delete(settings_dict[
                 'admin_base'] + "/users/" + user.user_id,
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
      return 'success'
    else:
      click.secho(f"{response.status_code} "
                  f"{response.json()['message']}",
                  fg='red')
      return 'fail'


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


@users.command('delete')
@click.pass_context
def delete_user(ctx):
  """Update Veracode Users"""
  """Delete a Veracode Application"""
  config = ctx.obj['config']
  setting_dict = ctx.obj['setting']

  user_list = fetch_users(setting_dict, config)

  while True:
    print_users_headers()
    print_users(user_list)
    user_id = click.prompt(
      "Enter user id (i.e. 3) to delete or \"-1\" to quit", type=int)
    if user_id == -1:
      sys.exit(0)
    if user_id < 1 or user_id > len(user_list):
      click.secho(f'{user_id} is not in range.', fg='red')
    else:
      user = user_list[user_id - 1]
      result = delete_one_user(user, setting_dict, config)
      if result == 'fail':
        sys.exit(1)
      else:
        del user_list[user_id - 1]


class User:
  def __init__(self, first_name, last_name, email, username, user_id=None,
               saml=None, enabled=None, last_login=None):
    self.first_name = first_name
    self.last_name = last_name
    self.email = email
    self.username = username
    self.user_id = '' if not user_id else user_id
    self.saml = False if not saml else saml
    self.enabled = True if not enabled else enabled
    self.last_login = None if not last_login else last_login

  def get_user_json(self):
    user_dict = copy.deepcopy(USER_CREATION_INPUT)
    user_dict['first_name'] = self.first_name
    user_dict['last_name'] = self.last_name
    user_dict['email_address'] = self.email
    user_dict['user_name'] = self.username
    return json.dumps(user_dict)

  def __str__(self) -> str:
    return f'First Name {self.first_name}, Last Name {self.last_name}, ' \
           f'Email {self.email}, Last_login {self.last_login}'
