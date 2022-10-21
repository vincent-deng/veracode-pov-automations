#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 20/10/2022 11:17 am
# @Organisation: Veracode

import sys
import click
from constant import CREDENTIALS, save_settings

DISPLAY_CREDENTIALS_FMT = "{:<3} {:10} {:32} {:<6}"


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


@click.group()
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
      sys.exit(1)
    if profile not in config.sections():
      click.secho(f"Profile {profile} not found!", fg='red')
    else:
      break

  setting['activated_credentials'] = profile
  save_settings(setting)
