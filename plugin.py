###
# Copyright (c) 2020, Brian McCord
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import os
import json
import requests
from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('BeestFM')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


bullet = ' \x0303•\x0f '

class BeestFM(callbacks.Plugin):
    """Gets Last Played info for a user"""
    pass

    def nick_arg(self, my_nick, nick_inp):
        try:
            if nick_inp.find('*') == 0:
                nick_inp = nick_inp[1:]
                return nick_inp
        except AttributeError:
            pass
        fm_nick = ''
        try:
            fmdb = json.load(open("{0}/fm.json".format(os.path.dirname
                     (os.path.abspath(__file__)))))
        except FileNotFoundError:
            #irc.error('fm.json not found')
            return
        if not nick_inp:
            nick_inp = fmdb.get(my_nick)
            if not nick_inp:
                nick_inp = 'error'
                return nick_inp
        if fmdb.get(nick_inp):
            nick_inp = fmdb.get(nick_inp)
        return nick_inp

    def fm(self, irc, msgs, args, fm_input):
        '''[<user>]
            Get Last.fm Last Played info for a user.
        '''
        api_key = self.registryValue('FMKey')

        my_nick = msgs.nick
        fm_user = self.nick_arg(my_nick, fm_input)

        if fm_user == 'error':
            irc.error('See the administrator to register your Last.fm username.')
            return

        payload = {'method': 'user.getrecenttracks', 'user': fm_user,
                   'api_key': api_key, 'format': 'json'}
        fm_data = requests.get('http://ws.audioscrobbler.com/2.0/',
                               params=payload).json()
        try:
            fm_user = fm_data['recenttracks']['@attr']['user']
            fm_title = fm_data['recenttracks']['track'][0]['name']
            fm_artist = fm_data['recenttracks']['track'][0]['artist']['#text']
            fm_album = fm_data['recenttracks']['track'][0]['album']['#text']
        except KeyError:
            irc.error('User \"\x0306%s\x0F\" not found.' % fm_user)
            return
        except IndexError:
            irc.error('No song data found for \"\x0306%s\x0F\".' % fm_user)
            return

        fm_np = '\x0F last played: '
        try:
            if (fm_data['recenttracks']['track'][0]['@attr']
                       ['nowplaying']) == 'true':
                fm_np = '\x0F is now playing: '
        except KeyError:
            pass

        fm_output = ('\x0303' + fm_user + fm_np + "\x0306\""
                     + fm_title + "\"" + bullet + '\x0306' + fm_artist + bullet + '\x1D'
                     + fm_album + '\x0F')

        irc.reply(fm_output, prefixNick=False)

    fm = wrap(fm, [optional('somethingWithoutSpaces')])

    def fmtop(self, irc, msgs, args, fm_period, fm_input):
        '''[<lp|all|wk|mo|yr> <user>]
            Get Last.fm Top Tracks info for a user.
        '''
        api_key = self.registryValue('FMKey')

        if fm_period == 'all' or not fm_period:
            fm_period = ('overall', 'Top All-Time')
        elif fm_period == 'lp':
            fm_period = 'lp'
        elif fm_period == 'wk':
            fm_period = ('7day', 'Top Weekly')
        elif fm_period == 'mo':
            fm_period = ('1month', 'Top Monthly')
        elif fm_period == 'yr':
            fm_period = ('12month', 'Top Yearly')
        else:
            fm_period = 'overall'

        my_nick = msgs.nick
        fm_user = self.nick_arg(my_nick, fm_input)

        if fm_user == 'error':
            irc.error('See the administrator to register your Last.fm username.')
            return

        if fm_period == 'lp':
            payload = {'method': 'user.getrecenttracks', 'user': fm_user, 'api_key':
                       api_key, 'format': 'json', 'limit': '5'}
            fm_data = requests.get('http://ws.audioscrobbler.com/2.0/',
                                   params=payload).json()

            try:
                fm_user = fm_data['recenttracks']['@attr']['user']
            except KeyError:
                irc.error('User \"\x0306%s\x0F\" not found.' % fm_user)
                return

            fm_output = "\x0306" + fm_user + "\'s Last Five"

            try:
                for idx in range(0, 5):
                    fm_title = fm_data['recenttracks']['track'][idx]['name']
                    fm_artist = (fm_data['recenttracks']['track'][idx]['artist']
                                 ['#text'])
                    try:
                        if (fm_data['recenttracks']['track'][idx]['@attr']
                                   ['nowplaying']) == 'true':
                            fm_np = '\x0303(now) '
                    except KeyError:
                        fm_np = ''
                    fm_output = (fm_output + bullet + fm_np + 
                                 fm_artist + ", \"" + fm_title + "\"")
            except IndexError:
                pass
            irc.reply(fm_output, prefixNick=False)
            return


        payload = {'method': 'user.gettoptracks', 'user': fm_user, 'api_key':
                   api_key, 'format': 'json', 'period': fm_period[0]}
        fm_data = requests.get('http://ws.audioscrobbler.com/2.0/',
                               params=payload).json()

        try:
            fm_user = fm_data['toptracks']['@attr']['user']
        except KeyError:
            irc.error('User \"\x0306%s\x0F\" not found.' % fm_user)
            return

        fm_output = "\x0306" + fm_user + "\'s " + fm_period[1]

        try:
            for idx in range(0, 5):
                fm_rank = fm_data['toptracks']['track'][idx]['@attr']['rank']
                fm_title = fm_data['toptracks']['track'][idx]['name']
                fm_artist = fm_data['toptracks']['track'][idx]['artist']['name']
                fm_output = (fm_output + bullet + "\x0303#" + fm_rank +
                             "\x0F " + fm_artist + ", \"" + fm_title + "\"")
        except IndexError:
            pass
        irc.reply(fm_output, prefixNick=False)

    fmtop = wrap(fmtop, [optional(("literal", ("lp", "all", "wk", "mo", 
                 "yr"))), optional('somethingWithoutSpaces')])

    def fmlast(self, irc, msgs, args, fm_input):
        '''[<user>]
            Get Last.fm Last Tracks info for a user.
        '''
        api_key = self.registryValue('FMKey')

        my_nick = msgs.nick
        fm_user = self.nick_arg(my_nick, fm_input)

        if fm_user == 'error':
            irc.error('See the administrator to register your Last.fm username.')
            return

        payload = {'method': 'user.getrecenttracks', 'user': fm_user, 'api_key':
                   api_key, 'format': 'json', 'limit': '5'}
        fm_data = requests.get('http://ws.audioscrobbler.com/2.0/',
                               params=payload).json()

        try:
            fm_user = fm_data['recenttracks']['@attr']['user']
        except KeyError:
            irc.error('User \"\x0306%s\x0F\" not found.' % fm_user)
            return

        fm_output = "\x0306" + fm_user + "\'s " + "Last Five"

        try:
            for idx in range(0, 5):
                fm_title = fm_data['recenttracks']['track'][idx]['name']
                fm_artist = (fm_data['recenttracks']['track'][idx]['artist']
                             ['#text'])
                try:
                    if (fm_data['recenttracks']['track'][idx]['@attr']
                               ['nowplaying']) == 'true':
                        fm_np = '\x0303(now) '
                except KeyError:
                    fm_np = ''
                    pass
                fm_output = (fm_output + bullet + fm_np + "\x0F" + fm_artist + ", \""
                             + fm_title + "\"")
        except IndexError:
            pass
        irc.reply(fm_output, prefixNick=False)

    fmlast = wrap(fmlast, [optional('somethingWithoutSpaces')])



    def fmart(self, irc, msgs, args, fm_period, fm_input):
        '''[<all|wk|mo|yr> <user>]
            Get Last.fm Top Artists info for a user.
        '''
        api_key = self.registryValue('FMKey')

        if fm_period == 'all' or not fm_period:
            fm_period = ('overall', 'Top All-Time Artists')
        elif fm_period == 'wk':
            fm_period = ('7day', 'Top Weekly Artists')
        elif fm_period == 'mo':
            fm_period = ('1month', 'Top Monthly Artists')
        elif fm_period == 'yr':
            fm_period = ('12month', 'Top Yearly Artists')
        else:
            fm_period = 'overall'

        my_nick = msgs.nick
        fm_user = self.nick_arg(my_nick, fm_input)

        if fm_user == 'error':
            irc.error('See the administrator to register your Last.fm username.')
            return

        payload = {'method': 'user.gettopartists', 'user': fm_user, 'api_key':
                   api_key, 'format': 'json', 'period': fm_period[0]}
        fm_data = requests.get('http://ws.audioscrobbler.com/2.0/',
                               params=payload).json()

        try:
            fm_user = fm_data['topartists']['@attr']['user']
        except KeyError:
            irc.error('User \"\x0306%s\x0F\" not found.' % fm_user)
            return

        fm_output = "\x0306" + fm_user + "\'s " + fm_period[1]

        try:
            for idx in range(0, 5):
                fm_rank = fm_data['topartists']['artist'][idx]['@attr']['rank']
                fm_title = fm_data['topartists']['artist'][idx]['name']
                fm_output = (fm_output + bullet + "\x0303#" + fm_rank +
                             "\x0F " + fm_title)
        except IndexError:
            pass
        irc.reply(fm_output, prefixNick=False)

    fmart = wrap(fmart, [optional(("literal", ("all", "wk", "mo", 
                 "yr"))), optional('somethingWithoutSpaces')])



Class = BeestFM


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
