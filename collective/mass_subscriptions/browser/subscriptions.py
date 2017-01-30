# -*- coding: utf-8 -*-

import csv
import random

from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone import api

try:
    from Products.GroupUserFolder.GroupsToolPermissions import ManageGroups
except ImportError:
    from Products.PlonePAS.permissions import ManageGroups

from collective.mass_subscriptions import messageFactory as _

class MassSubscriptionsView(BrowserView):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.props = []
        request.set('disable_border', True)

    def __call__(self, *args, **kwargs):
        if getToolByName(self.context, 'portal_membership').isAnonymousUser():
            raise Unauthorized("You must be an authenticated site member")
        if self.request.form.get('csv'):
            self._importUsers()
        return self.index()

    def _generateRandomPassword(self, chars):
        st = ""
        possible_chars = 'qwertyuiopasdfghjklzxcvbnm_-1234567890'
        for x in range(chars):
            st+=random.choice(possible_chars)
        return st

    def _getUserData(self, row):
        """Take from the CSV row user data as dict"""
        props = {}
        ptool = getToolByName(self.context, 'plone_utils')

        for p in self.props:
            props[p] = self._findColumn(row, p).strip()
        if not props.get('password'):
            props['password'] = self._generateRandomPassword(8)
        return props

    def _sendConfirmationMail(self, email, username, password, userdata, subject, mail_template):
        mailhost = getToolByName(self.context, 'MailHost')
        portal_url = getToolByName(self.context, 'portal_url')
        mfrom = portal_url.getPortalObject().getProperty('email_from_address')
        message = mail_template.replace("$username", username).replace("$portal_url", portal_url())\
                        .replace("$password", password)
        for p in self.props:
            message = message.replace("$data-%s" % p, userdata.get(p, ''))
        try:
            mailhost.secureSend(message, email, mfrom, subject=subject, charset='utf-8')
        except:
            ptool.addPortalMessage(_("send_mail_error_message",
                                     default=u"Error while sending e-mail to $email",
                                     mapping={'email': email}), type="error")

    @property
    def all_groups(self):
        acl_users = getToolByName(self.context, 'acl_users')
        return acl_users.source_groups.getGroupIds()

    def can_manage_groups(self):
        mtool = getToolByName(self.context, 'portal_membership')
        return mtool.checkPermission(ManageGroups, self.context)

    def _addUserToGroups(self, username, groups):
        acl_users = getToolByName(self.context, 'acl_users')
        for group_id in groups:
            group = acl_users.getGroup(group_id)
            group.addMember(username)

    def _findColumn(self, row, name):
        return row[self.props.index(name)]

    def _importUsers(self):
        context = self.context
        form = self.request.form
        regtool = getToolByName(context, 'portal_registration')
        ptool = getToolByName(self.context, 'plone_utils')
        
        reader = csv.reader(form.get('csv'))
        send_mail = form.get('mail', False)
        subject = form.get('subject', '')
        mail_template = form.get('mail_template', '')
        
        if send_mail and (not subject or not mail_template):
            ptool.addPortalMessage(_(u"To send confirmation e-mail to users you need "
                                      "to provide both subject and a template"), type="error")
            return
        
        first = True
        cnt = 0

        for row in reader:
            cnt+=1
            if first:
                first = False
                self.props = row
                continue

            username = self._findColumn(row, 'username')
            userdata = self._getUserData(row)
            password = userdata['password']
            del userdata['password']

            try:
                regtool.addMember(username, password, properties=userdata)
                ptool.addPortalMessage(_("new_user_message",
                                         default=u"Registered new user $name",
                                         mapping={'name': userdata.get('fullname') or username})
                                        )

                if send_mail:
                    email = userdata.get('email')
                    if email:
                        self._sendConfirmationMail(email, username, password, userdata, subject, mail_template)
                    else:
                        ptool.addPortalMessage(_("cant_send_mail_message",
                                                 default=u"Can't send e-mail to $username",
                                                 mapping={'username': username},
                                                 ),
                                               type="warning")
                                               
                if userdata.get('group') and self.can_manage_groups:
                    group=userdata.get('group')
                    api.group.add_user(groupname=group, username=username)

                if form.get('groups') and self.can_manage_groups:
                    self._addUserToGroups(username, form.get('groups'))

            except ValueError, inst:
                ptool.addPortalMessage(_("new_user_error",
                                         default=u"Can't add user $name - $msg",
                                         mapping={'name': userdata.get('fullname') or username,
                                                  'msg': inst.args[0]},
                                        ),
                                       type="error")
