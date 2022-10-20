#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 19/10/2022 12:44 pm
# @Organisation: Veracode
from pathlib import Path
import threading
import sys
import time
import json

CREDENTIALS = Path.home() / ".veracode" / "credentials"
SETTINGS = Path.home() / ".veracode" / "settings.json"
USER = Path.home() / ".veracode" / "user-creation-input.json"
DISPLAY_CREDENTIALS_FMT = "{:<3} {:10} {:32} {:<6}"
DISPLAY_USERS_FMT = "{:<3} {:35} {:12} {:12}"
DISPLAY_APPLICATION_FMT = "{:<3} {:40} {:40} {:20}"

SETTINGS_INIT_DICT = {
  'activated_credentials': 'default',
  'api_base': 'https://api.veracode.com/appsec/v1',
  'admin_base': 'https://api.veracode.com/api/authn/v2',
  'headers': {"User-Agent": "Python HMAC"},
}

USER_CREATION_INPUT = {
  'email_address': '',
  'user_name': '',
  'first_name': '',
  'last_name': '',
  'ipRestricted': False,
  'active': True,
  "userType": "VOSP",
  'roles': [
    {'role_name': 'greenlightideuser'},  # Greenlight IDE User
    # {'role_name': 'submitterapi'},
    # {'role_name': 'extsubmitdynamicmpscan'},
    {'role_name': 'sandboxadmin'},  # Sandbox Administrator
    # {'role_name': 'apisubmitstaticscan'},
    {'role_name': 'workSpaceEditor'},  # Workspace Editor
    # {'role_name': 'apisubmitdynamicscan'},
    {'role_name': 'deletescans'},  # Delete Scans
    # {'role_name': 'extsubmitdynamicanalysis'},
    # {'role_name': 'uploadapi'},
    {'role_name': 'securityLabsUser'},  # Security Labs User
    # {'role_name': 'resultsapi'},
    {'role_name': 'extexecutive'},  # Executive
    # {'role_name': 'greenlightapiuser'},
    # {'role_name': 'extsubmitanyscanextsubmitanyscan'},
    # {'role_name': 'extsubmitstaticscan'},
    {'role_name': 'collectionManager'},  # Collection Manager
    # {'role_name': 'adminapi'},
    {'role_name': 'extpolicyadmin'},  # Policy Administrator
    # {'role_name': 'extsubmitdynamicscan'},
    {'role_name': 'extelearn'},  # eLearning
    {'role_name': 'extsubmitter'},  # Submitter
    {'role_name': 'extreviewer'},  # Reviewer
    # {'role_name': 'extadmin'},
    {'role_name': 'workSpaceAdmin'},  # Workspace Administrator
    # {'role_name': 'collectionReviewerAPI'},
    {'role_name': 'extcreator'},  # Creator
    {'role_name': 'extmitigationapprover'},  # Mitigation Approver
    {'role_name': 'collectionReviewer'},  # Collection Reviewer
    {'role_name': 'extseclead'},  # Security Lead
    {'role_name': 'securityinsightsonly'},  # Security Insights
    {'role_name': 'sandboxuser'}  # Sandbox User
  ]
}

APPLICATION_CREATION_INPUT = {
  'profile': {
    'business_criticality': 'VERY_HIGH',
    'description': '',
    'name': '',
    'policies': [
      {
        'guid': '4cbdbf17-7979-4848-bd7f-f5c0e1b67d18'
        # Veracode Recommended High + SCA
      }
    ]
  }
}


def save_settings(setting_dict):
  with open(SETTINGS, 'w') as fp:
    fp.write(json.dumps(setting_dict, indent=4))


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
