# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: admin.py 6 2008-01-14 13:06:00Z s0undt3ch $
# =============================================================================
#             $URL: http://devnull.ufsoft.org/svn/TracAdsPanel/trunk/adspanel/admin.py $
# $LastChangedDate: 2008-01-14 13:06:00 +0000 (Mon, 14 Jan 2008) $
#             $Rev: 6 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.admin import IAdminPanelProvider
from trac.config import Option, BoolOption, _TRUE_VALUES
from trac.util.text import unicode_unquote
from pkg_resources import resource_filename


class AdsAdminPanel(Component):
    implements(ITemplateProvider, IAdminPanelProvider)

    def __init__(self):
        self.options = {}

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        return [resource_filename(__name__, 'templates')]

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('adspanel', 'Ads Panel', 'config', 'Configuration')

    def render_admin_panel(self, req, cat, page, path_info):
        self._update_config()
        if req.method == 'POST':
            self.config.set('adspanel', 'hide_for_authenticated',
                            req.args.get('hide_for_authenticated') in
                            _TRUE_VALUES)
            self.config.set('adspanel', 'store_in_session',
                            req.args.get('store_in_session') in _TRUE_VALUES)
            self.config.save()
            code = req.args.get('ads_code')
            cursor = self.env.get_db_cnx().cursor()
            cursor.execute('SELECT value FROM system WHERE name=%s',
                           ('adspanel.code',))
            if cursor.fetchone():
                cursor.execute('UPDATE system SET value=%s WHERE name=%s',
                               ('adspanel.code', code))
            else:
                cursor.execute('INSERT INTO system (name,value) VALUES (%s,%s)',
                               ('adspanel.code', code))

            req.redirect(req.href.admin(cat, page))
        return 'ads_admin.html', {'ads_options': self.options}

    # Internal methods
    def _update_config(self):
        for option in [option for option in Option.registry.values()
                       if option.section == 'adspanel']:
            value = ''
            if option.name in ('hide_for_authenticated', 'store_in_session'):
                value = self.config.getbool('adspanel', option.name,
                                            option.default)
            elif option.name == 'ads_code':
                # Still get the Option to get __doc__ from it
                value = self.config.get('adspanel', option.name, option.default)
            option.value = value
            self.options[option.name] = option

        cursor = self.env.get_db_cnx().cursor()
        cursor.execute('SELECT value FROM system WHERE name=%s',
                       ('adspanel.code',))
        code = cursor.fetchone()
        if code:
            code = unicode_unquote(code[0])
        else:
            code = ''
        self.options['ads_code'].value = code
