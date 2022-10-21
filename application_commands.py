#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 20/10/2022 11:05 am
# @Organisation: Veracode

import click
from constant import DISPLAY_APPLICATION_FMT, SpinnerThread, \
  APPLICATION_CREATION_INPUT
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
import sys
from datetime import datetime
from credentials_commands import activate_credentials
import copy
import json


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
        application['last_completed_scan_date'],
        application['guid']
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


def add_applications_to_platform(application_list, config, settings_dict):
  api_id = config[settings_dict['activated_credentials']]['veracode_api_key_id']
  api_key = config[settings_dict['activated_credentials']][
    'veracode_api_key_secret']

  count = 0

  with click.progressbar(
          length=len(application_list),
          show_eta=False,
          item_show_func=lambda
                  application_name: f"Adding application: {application_name}"
  ) as bar:
    for idx, application in enumerate(application_list, start=1):
      application_json = application.get_application_json()
      try:
        response = requests. \
          post(settings_dict['api_base'] + "/applications",
               auth=RequestsAuthPluginVeracodeHMAC(api_key_id=api_id,
                                                   api_key_secret=api_key),
               headers={'Content-Type': 'application/json',
                        'Accept': 'application/json'},

               data=application_json)
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
      bar.update(idx - 1, application.application_name)

  click.secho(
    f'Successfully created {count} applications on Veracode Platform.',
    fg='green')


def delete_one_application(application, settings_dict, config):
  spinner_thread = SpinnerThread()

  api_id = config[settings_dict['activated_credentials']]['veracode_api_key_id']
  api_key = config[settings_dict['activated_credentials']][
    'veracode_api_key_secret']

  if click.confirm(f'Delete \"{application.application_name}\", continue?'):
    spinner_thread.start()
    try:
      response = requests. \
        delete(settings_dict[
                 'api_base'] + "/applications/" + application.application_guid,
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


@click.group()
@click.pass_context
def applications(ctx):
  """Manage Veracode Applications"""
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


@applications.command('list')
@click.pass_context
def list_applications(ctx):
  """List Veracode Applications"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  print_applications_header()
  application_list = fetch_applications(setting_dict, config)
  print_applications(application_list)


@applications.command('add')
@click.pass_context
def add_application(ctx):
  """Add Veracode Applications"""
  setting_dict = ctx.obj['setting']
  config = ctx.obj['config']
  application_list = []
  while True:
    application_name = click.prompt("Please enter the name of the Application")
    application = Application(application_name,
                              'Veracode Recommended High + SCA',
                              None, '')
    application_list.append(application)
    print_applications_header()
    print_applications(application_list)
    if not click.confirm(f'Add more users in this Veracode account?'):
      break
  click.echo('Adding applications to Veracode Platform...')
  add_applications_to_platform(application_list, config, setting_dict)


@applications.command('delete')
@click.pass_context
def delete_application(ctx):
  """Delete a Veracode Application"""
  config = ctx.obj['config']
  setting_dict = ctx.obj['setting']
  print_applications_header()
  application_list = fetch_applications(setting_dict, config)
  print_applications(application_list)

  while True:
    print_applications_header()
    print_applications(application_list)
    application_id = click.prompt(
      "Enter application id (i.e. 3) to delete or \"-1\" to quit", type=int)
    if application_id == -1:
      sys.exit(0)
    if application_id < 1 or application_id > len(application_list):
      click.secho(f'{application_id} is not in range.', fg='red')
    else:
      application = application_list[application_id - 1]
      result = delete_one_application(application, setting_dict, config)
      if result == 'fail':
        sys.exit(1)
      else:
        del application_list[application_id - 1]


class Application:
  def __init__(self, application_name, policy_name, last_scan,
               application_guid):
    self.application_name = application_name
    self.policy_name = policy_name
    self.last_scan = last_scan
    self.application_guid = application_guid

  def get_application_json(self):
    application_dict = copy.deepcopy(APPLICATION_CREATION_INPUT)
    application_dict['profile']['name'] = self.application_name
    application_dict['profile']['description'] = self.application_name
    return json.dumps(application_dict)
