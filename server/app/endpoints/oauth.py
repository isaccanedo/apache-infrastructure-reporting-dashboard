#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""ASF Infrastructure Reporting Dashboard"""
"""Handler for oauth operations"""

from ..lib import middleware
import quart
import aiohttp
import uuid
import urllib.parse
import time

# TODO: Switch back once KeyCloak is in prod?
# OAUTH_URL_INIT = "https://oauth.apache.org/auth-oidc?state=%s&redirect_uri=%s"
# OAUTH_URL_CALLBACK = "https://oauth.apache.org/token-oidc?code=%s"

OAUTH_URL_INIT = "https://oauth.apache.org/auth?state=%s&redirect_uri=%s"
OAUTH_URL_CALLBACK = "https://oauth.apache.org/token?code=%s"


async def process(form_data):
    if quart.request.method == "GET":
        code = form_data.get("code")
        state = form_data.get("state")
        if not code or not state:  # Presumably first step in OAuth
            state = str(uuid.uuid4())
            callback_url = urllib.parse.urljoin(
                quart.request.host_url.replace("http://", "https://"),
                f"/oauth?state={state}",
            )
            redirect_url = OAUTH_URL_INIT % (state, urllib.parse.quote(callback_url))
            headers = {
                "Location": redirect_url,
            }
            return quart.Response(status=302, response="Redirecting...", headers=headers)
        else:  # Callback from oauth.a.o
            ct = aiohttp.client.ClientTimeout(sock_read=15)
            async with aiohttp.client.ClientSession(timeout=ct) as session:
                rv = await session.get(OAUTH_URL_CALLBACK % code)
                assert rv.status == 200, "Could not verify oauth response."
                oauth_data = await rv.json()
                quart.session.clear()
                quart.session.update(oauth_data)
                # Quart sessions live for the entirety of the browser session. We don't want this to extend
                # too far into the future (abuse??), so let's set a fixed timeout after which a new login
                # will be required.
                quart.session["timestamp"] = int(time.time())
            uid = quart.session["uid"]
            return quart.Response(
                status=200,
                response=f"Successfully logged in! Welcome, {uid}\n",
            )


quart.current_app.add_url_rule(
    "/api/oauth",
    methods=[
        "GET",  # OAuth request
    ],
    view_func=middleware.glued(process),
)
