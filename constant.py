#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Vincent Deng
# @Time: 19/10/2022 12:44 pm
# @Organisation: Veracode
from pathlib import Path

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
