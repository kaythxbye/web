'''
    Copyright (C) 2018 Gitcoin Core

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

'''
import time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from dashboard.models import Profile
from dashboard.views import profile_keywords_helper
from github.utils import search
from marketing.models import EmailSubscriber


def get_github_user_from_github(email):
    result = search(email)
    if not result.get('total_count', 0):
        # print(result)
        raise Exception("no users found")

    return result['items'][0]


def get_github_user_from_DB(email):
    users = User.objects.filter(email__iexact=email)
    for user in users:
        if user.profile:
            return user.profile.handle
    profiles = Profile.objects.filter(email__iexact=email)
    for profile in profiles:
        return profile.handle
    return None


class Command(BaseCommand):

    help = 'pulls all github login info'

    def handle(self, *args, **options):
        emailsubscribers = EmailSubscriber.objects.filter(github='')
        success = 0
        exceptions = 0
        for es in emailsubscribers:
            # print(es.email)
            try:
                es.github = get_github_user_from_DB(es.email)
                if not es.github:
                    ghuser = get_github_user_from_github(es.email)
                    es.github = ghuser['login']
                if not es.keywords:
                    es.keywords = profile_keywords_helper(es.github)
                es.save()
                # print(es.email, es.github, es.keywords)
                success += 1
            except Exception:
                exceptions += 1
            time.sleep(2)

        print("success: {}".format(success))
        print("total: {}".format(emailsubscribers.count()))
        print("pct: {}".format(round(success / emailsubscribers.count(), 2)))

        print("exceptions: {}".format(exceptions))
        print("total: {}".format(emailsubscribers.count()))
        print("pct: {}".format(round(exceptions / emailsubscribers.count(), 2)))
